# Houses all the dash app callbacks in one neat place

import dash_bootstrap_components as dbc
from dash import Dash, html, Input, Output, State, ctx, callback, dcc
import pandas as pd
import numpy as np
import logging
from . global_constants import *
from . import data
from . import charts
from dash.exceptions import PreventUpdate #for raising exception to break out of callbacks
import sys

#Obtain the root logger
logger = logging.getLogger(LOGGER)


def init_callbacks(dash_app, dobj):
    

    #INPUTS
    def callback_main_create_inputs() -> list:
        #Return a list of type callback Input representing all inputs for main callback
        
        c=[]                 
                   
        # get all dataset ids as list of strings
        keys_list = list(dobj.config_key_dsid.keys())
        keys_list_str = [str(id) for id in keys_list]    

        # recursively add input ids for all datasets in dataset_lkup
        for id in keys_list_str:         
            c.append(Input(id,"n_clicks"))     
        
        # add random button
        c.append(Input('random-button', "n_clicks"))
        
        # add search menu
        c.append(Input('nav-search-menu', 'value'))
        
        # add api
        c.append(Input('my-url-map-trigger', 'data')) 
        
        c.append(Input("year-slider", "value"))

        c.append(Input('my-settings_json_store', 'data')) #these act purely as triggers after apply button pushed (like the hidden div), to call the main callback
        c.append(Input('my-settings_mapstyle_store', 'data')) #these act purely as triggers after apply button pushed (like the hidden div), to call the main callback
        
        #print(c)
        return c


    # MAIN CALLBACK
    @dash_app.callback(
        #OUTPUTS
        [
            Output("my-series","data"),
        #    Output("my-series-label","data"),
            Output("geomap_figure", "figure"),
            Output("my-source", "children"),
            Output("my-source-link", "href"),         
        #    Output("download-button", "style"),                       
        #    Output("bar-button", "style"),
        #    Output("line-button", "style"),
        #    Output("geobar-button", "style"),
        #    Output("sunburst-button", "style"),
        #    Output("globe-button", "style"),
        #    Output("bubble-button", "style"),        
        #    Output('my-year', "data"),
            Output('my-loader-main', "children"), #used to trigger loader. Use null string "" as output
        #    Output('button-panel-style', "style"), #used to hide initially
        #    Output('year-slider-style', "style"), #used to hide initially
        #    Output('data-source-style', 'style'), #used to hide initially         
            #Output("year-slider", "max"),         
            Output("year-slider", "marks"),
            Output("year-slider", "value"),         
        #    Output("year-slider-title","style"),
        #    Output("year-slider-title","children"),
        #    Output("my-selection-m49", "data"), #NEW, to save the m49 location of the selected map
        #    #Output("my-series-data","data"),         
        #    Output("my-url-main-callback","data"), #to set url in another callback
        #    Output("my-url-bar-trigger", "data"),  # chain to bar
        #    Output("my-url-line-trigger", "data"), # chain to line
        #    Output("my-url-globe-trigger", "data"),# chain to globe
        #    Output("my-url-jigsaw-trigger", "data"),# chain to globe
            Output("source-popover","children"), #popover with explanatory notes
        #    Output("my-experimental-trigger", "data") #trigger for experimental modal          
        ],        
        
        #INPUTS
        callback_main_create_inputs(), #build list of input items programmatically 
        
        #STATE
        [
            State("geomap_figure", "figure"),
            State("year-slider", "marks"),
            State("year-slider", "max"),
            State("year-slider", "value"),
            State("my-series","data"),        
            State("my-series-label","data"),        
            State('my-settings_json_store', 'data'), #allows data intself to be extracted
            State('my-settings_mapstyle_store', 'data'), #allows data intself to be extracted
            State("my-settings_colorbar_store", 'data'),
            State("my-settings_colorbar_reverse_store", 'data'),
            State('nav-search-menu', 'value'), #new
            State("my-selection-m49", "data"), #NEW, to save the m49 location of the selected map
            State("my-url-path", "data"),        
            State("my-url-root", 'data'),
            State('my-url-map-trigger', 'data'),
            State("my-url-series", 'data'),
            State("my-url-year", 'data'),
            State("my-url-view", 'data'),
            State("js-detected-viewport", 'data'),             
        ],
        
        prevent_initial_call=True
    )    
    def callback_main(*args):  
        logger.info("MAIN CALLBACK")
                
        # user selection
        selection = ctx.triggered_id
        states = ctx.states        
        logger.info(f"Selection is {selection}")

        # load colour palette
        colorpalette = states['my-settings_colorbar_store.data']
        colorpalette_reverse = states['my-settings_colorbar_reverse_store.data']  
        if colorpalette is None: colorpalette = geomap_colorscale[INIT_COLOR_PALETTE] #39 inferno,  #55 plasma    
        if colorpalette_reverse is None: colorpalette_reverse = INIT_COLOR_PALETTE_REVERSE # default True        

        #series: dict of type {dataset_id, dataset_label, dataset_raw, var_type, nav_cat, nav_cat_nest, colour, var_type, source, link, note} 

        # CASE: navmenu selection        
        if selection.isnumeric():                                 
            series = dobj.config_key_dsid[int(selection)]            

        # CASE: random button selection
        elif selection == 'random-button':                      
            series = dobj.config_key_dsid[np.random.randint(0,len(dobj.config_key_dsid))]           

        # CASE: search menu
        elif selection == 'nav-search-menu':            
            search_menu_dsraw = states["nav-search-menu.value"] #dataset_raw
            series = dobj.config_key_dsraw[search_menu_dsraw]            

        # CASE: series selection (from either navmenu, random btn or search menu) 
        if selection.isnumeric() or selection == 'random-button' or selection == 'nav-search-menu':
            #return out and build main map
            year = dobj.get_latest_year(series['dataset_raw'])
            fig = charts.create_map_geomap(dobj, series, colorpalette, colorpalette_reverse, year)
            series_label = f"{series['dataset_label']} in {year}"
            series_source = series['source']
            link = series['link']
            note = series['note']            
            time_slider = data.get_time_slider(dobj, series['dataset_raw'], year=None)
            return series['dataset_raw'], fig, series_source, link, series_label, time_slider['marks'], time_slider['value'], note

        # CASE: year slider
        if selection == 'year-slider':
            year = int(states['year-slider.value'])
            print(f"Year selected is {year}")
            series_name = states['my-series.data']
            series = dobj.config_key_dsraw[series_name]   
            fig = charts.create_map_geomap(dobj, series, colorpalette, colorpalette_reverse, year)
            series_label = f"{series['dataset_label']} in {year}"
            series_source = series['source']
            link = series['link']
            note = series['note']            
            time_slider = data.get_time_slider(dobj, series['dataset_raw'], year=year)
            return series['dataset_raw'], fig, series_source, link, series_label, time_slider['marks'], time_slider['value'], note  
        
 



        """


        # data object vars (substituted. fix later)
        master_config = dobj.config_key_dsraw
        pop = dobj.stats        
        master_config_key_datasetid = dobj.config_key_dsid
        api_dict_label_to_raw = dobj.api_dict_label_to_raw
        api_dict_raw_to_label = dobj.api_dict_raw_to_label      
        SERIES = dobj.dataset_list

        # dcc states
        states = ctx.states
        zoom = states["geomap_figure.figure"]["layout"]["mapbox"]["zoom"]
        center = states["geomap_figure.figure"]["layout"]["mapbox"]["center"]
        series = states["my-series.data"] #this is initially "No data selected"   
        series_label = states["my-series-label.data"] 
        year_slider_marks = states["year-slider.marks"]
        year_slider_max = states["year-slider.max"]
        year_slider_selected = states["year-slider.value"]
        search_menu = states["nav-search-menu.value"]  
        settings_json = states['my-settings_json_store.data']
        settings_mapstyle = states['my-settings_mapstyle_store.data']
        settings_colorpalette = states['my-settings_colorbar_store.data']
        settings_colorpalette_reverse = states['my-settings_colorbar_reverse_store.data']
        selection_m49 = states['my-selection-m49.data'] #Map selection state (For later feature)        
        search_query = states['my-url-path.data']  #url 
        maptrigger = 'map'
        url_view = 'map' #override when necessary
        url_year = states['my-url-year.data']  #api   
        experiment_trigger = "" # trigger for experiments (i.e. the power station globe)
        
        # load settings data: border 
        if settings_json is None: geojson = dobj.map_lowres                 
        else:             
            if int(settings_json) == 0: geojson = dobj.map_lowres 
            elif int(settings_json)==1: geojson = dobj.map_medres
            elif int(settings_json)==2: geojson = dobj.map_hires
        
        # load settings data: map type
        if settings_mapstyle is None: mapstyle = mapbox_style[1] #default cartoposition        
        else: mapstyle = mapbox_style[int(settings_mapstyle)]        
            
        # load settings data: colour pallette    
        if settings_colorpalette is None: colorbarstyle = geomap_colorscale[INIT_COLOR_PALETTE] #39 inferno,  #55 plasma 
        else:
            if int(settings_colorpalette) == 0: colorbarstyle = None #this is the only way to get the mapboxchoroplethmap to default to automatic colouring
            else: colorbarstyle = geomap_colorscale[int(settings_colorpalette)]        
        if settings_colorpalette_reverse is None: settings_colorpalette_reverse = INIT_COLOR_PALETTE_REVERSE #i.e. set to default if nothing returned from store
        
        selected_map_location = "none" #default (used in map selection, still in dev!!)  
        
        # set display defaults (these are tuned later in logic)
        navbtm_btns_style = {'display': 'block', 'marginLeft': "1vw", 'marginBottom':0, 'opacity':INIT_BUTTON_OPACITY} #used to hide/display entire button panel
        navbtm_yr_style = {'display': 'block', 'marginBottom':5, 'marginRight':30} #display
        navtm_yr_title_style = {'fontWeight': 'bold', 'color': INIT_year_SLIDER_FONTCOLOR, 'fontSize': INIT_year_TITLE_FONTSIZE, 'align-items': 'center', 'justify-content': 'center','display': 'flex', 'marginBottom':'0.5vmin', 'marginRight':30}
        navbtm_source_style = {'display': 'inline-block', 'marginBottom':5, 'marginLeft':10, 'marginTop':15, 'paddingRight':50, 'vertical-align':'bottom', 'backgroundColor': 'transparent', 'width':'33%', 'minWidth':INIT_NAVFOOTER_COMPONENT_MINWIDTH} #display source     
        download_btn_style = {"marginBottom": 10, 'display': 'inline-block', 'fontSize': INIT_NAVFOOTER_BTN_FONT} #inline-block is the key to not adding line break!!!
        bar_btn_style = {'display': 'inline-block', 'fontSize': INIT_NAVFOOTER_BTN_FONT} #display!
        line_btn_style = {'display': 'inline-block', 'fontSize': INIT_NAVFOOTER_BTN_FONT} #display!
        geobar_btn_style = {'display': 'inline-block', 'fontSize': INIT_NAVFOOTER_BTN_FONT} #display!
        sunburst_btn_style = { 'display': 'inline-block', 'fontSize': INIT_NAVFOOTER_BTN_FONT} #display!
        globe_btn_style = { 'display': 'inline-block', 'fontSize': INIT_NAVFOOTER_BTN_FONT} #display!
        bubble_btn_style = { 'display': 'inline-block', 'fontSize': INIT_NAVFOOTER_BTN_FONT} #display!
        
        #setup source for normal operation
        if series == None:
            source = "No data selected"
            link = ""
            year=""
        else:            
            source = dobj.config_key_dsraw[series].get("source") 
            link = master_config[series].get("link")    
            year = int(data.get_years(pop.loc[(pop['dataset_raw'] == series)])[year_slider_selected]) #expensive                       
               
        
        # MAIN CALLBACK LOGIC pt1 (Determine what the event was)
        
        # MAP CLICK (PRESENTLY DISABLED: CHECK CALLBACK INPUT TO SWITCH BACK ON)
        if selection == "geomap_figure":
            #Grab some shit about the click data, yeeeh baby. We got some click data. We gonna do shit with it. Yeeh.
            selected_map_location = ctx.triggered[0]['value']['points'][0]['location'] #this is the M49 code of selected country
            selection_m49 = selected_map_location
            #logger.info("Map click detected. Click data is %r, location is %r.", ctx.triggered, selected_map_location)        
            #OK GOT THE STORE FOR SELECTION WORKING, CAN OUTPUT AND RETRIEVE FROM STATE. NEED TO RESOLVE LOGIC TO BUILD MAP WITH TRACE, PLUS NEW LOGIC TO SUBSET DF TO SELECTION + ALL YRS FOR country ETC.
            #MIGHT BE A BIT TRICKY. COULD POSSIBLY HAVE TO RETURN OUT OF MAIN CALLBACK HERES        
            #return series, create_map_geomap(pop, geojson, series, years[year], zoom, center, selected_map_location), d.get_source(logger, pop, series, years[year]), "https://www.google.com"
            #This still needs work
        
        # YEAR SLIDER CHANGE
        elif selection == "timeslider-hidden-div":  
            # reset fonts
            for i in range(0,len(year_slider_marks)):
                year_slider_marks[str(i)]['style']['fontWeight']='normal'     
            year_slider_marks[str(year_slider_selected)]['style']['fontWeight']='bold'
            
            
        # SETTINGS CHANGE
        elif selection == "my-settings_json_store":   
            #Check if there is a dataset and hide source, slider and buttons if not
            if series == None:
                navbtm_yr_style = {'display': 'none'}
                navtm_yr_title_style = {'fontWeight': 'bold', 'color': INIT_year_SLIDER_FONTCOLOR, 'fontSize': INIT_year_SLIDER_FONTSIZE, 'align-items': 'center', 'justify-content': 'center','display': 'none', 'marginBottom':'0.5vmin',}
                navbtm_source_style = {'display': 'none'}            
                download_btn_style = {'display': 'none'}
                bar_btn_style = {'display': 'none'}
                line_btn_style = {'display': 'none'}
                geobar_btn_style = {'display': 'none'}
                sunburst_btn_style = {'display': 'none'}
                globe_btn_style = {'display': 'none'}
                bubble_btn_style = {'display': 'none'}
        
        # URL PATH SEARCH
        elif selection == "my-url-map-trigger":
            
            #print("API hit. Search query: ",search_query,"\nMap trigger signal:",maptrigger)
            
            url_view = states['my-url-view.data']  #override
            maptrigger = states['my-url-map-trigger.data']  #override        
            
            if search_query == '/' : raise PreventUpdate()
            
            # split query into a list
            query = search_query.split('/')        
            print("query: ",query,"length:",len(query))          
                    
            # /series/year/map
            if len(query) == 4:
                api_series = query[1] #working
                api_year = query[2] #working                
            
            else: raise PreventUpdate("Break from main callback. Invalid URL input")
                
            # check if series valid
            try:        
                series = api_dict_label_to_raw[api_series]    #working         
            except KeyError as error:
                print("series not found, breaking out of callback")
                raise PreventUpdate()                                  
            
            # check if year valid
            year = api_year #working            
            
            # special condition if coming from non-specific year modal
            if year != 'x':            
                # Check to see if year is in dataset for this series                
                year_check = data.check_year(pop, series, year) #expensive
                if year_check == False:
                    print("year not found in dataset, breaking out of callback")
                    raise PreventUpdate()       
            else:
                # grab years and auto select most recent
                year_dict = data.get_years(pop.loc[(pop['dataset_raw'] == series)])
                year_index = list(year_dict)[-1]
                year = year_dict[year_index] 
                
            # update all vars        
            series_label = master_config[series].get("dataset_label")  
            source = master_config[series].get("source") 
            link = master_config[series].get("link")    
            year_slider_marks = data.get_year_slider_marks(series, pop, INIT_year_SLIDER_FONTSIZE, INIT_year_SLIDER_FONTCOLOR, year_slider_selected)
            year_slider_max = len(year_slider_marks)-1                        
            year_slider_selected = data.get_year_slider_index(pop, series, year)
            year_slider_marks[year_slider_selected]['style']['fontWeight']='bold' #mark selected year bold          
        
        
        # NAVBAR SELECTION
        else:
            #New dataset is selected, query available years and rebuild year slider vals        
            logger.info("Main callback: navbar selection logic, or search pressed") 
                   
            # first check if search menu input, and override series variable if so
            if selection == 'nav-search-menu':            
                
                # if we have a value, update the series
                if search_menu != None and search_menu != '': series = search_menu
            
            # next check for random button
            elif selection == 'random-button':            
                series = SERIES[np.random.randint(0,len(SERIES))] 
                        
            # it must be from dropdown items
            else:
                #get series from master config dictionary (using the dataset id integer number as the key)                            
                series = master_config_key_datasetid[int(selection)].get("dataset_raw")
                
                #special check for experimental data selected (global power stations thingy)                
                if series == "Global power stations of the world": experiment_trigger = "Creme freesh" # to trigger the experimental globe modal
            
            #update all vars
            series_label = master_config[series].get("dataset_label")  
            source = master_config[series].get("source") 
            link = master_config[series].get("link")     
            year_dict = data.get_years(pop.loc[(pop['dataset_raw'] == series)])
            
            # it the datasets has data in at least 1 year, set the year slider
            if len(year_dict) > 0:
                year_index = list(year_dict)[-1]
                year = year_dict[year_index] #what is returned
                year_slider_marks = data.get_year_slider_marks(series, pop, INIT_year_SLIDER_FONTSIZE, INIT_year_SLIDER_FONTCOLOR, year_slider_selected)
                year_slider_max = len(year_slider_marks)-1
                year_slider_selected = year_slider_max #select the most recent year by default
                year_slider_marks[year_slider_selected]['style']['fontWeight']='bold' #mark selected year bold          
            
        # MAIN CALLBACK LOGIC Pt2 (Get ready to return) 
                        
        # Check what datatype is selected and hide buttons not applicable for discrete data   
        if series != None:       
                
            if master_config[series].get("var_type")  == "discrete":
                print("Main callback: discrete dataset found")            
                navbtm_yr_style = {'display': 'block'}            
                geobar_btn_style = {'display': 'none'}
                sunburst_btn_style = {'display': 'none'}
                bar_btn_style = {'display': 'none'}
                line_btn_style = {'display': 'none'}
                bubble_btn_style = {'display': 'none'}        
        
        # If only one year is available, do some custom logic to display year (slider has a bug)
        if len(year_slider_marks) < 2:
            navbtm_yr_style = {'display': 'none'} #hid
            navtm_yr_title_style = {'fontWeight': 'bold', 'color': INIT_year_SLIDER_FONTCOLOR, 'fontSize': INIT_year_SLIDER_FONTSIZE, 'align-items': 'center', 'justify-content': 'center','display': 'flex', 'marginBottom':'0.5vmin',}
            navbtm_yr_title_val = "YEAR: "+str(year)
        else:
            navbtm_yr_title_val = "YEAR"
        
        # set URL path to return
        root_path = states['my-url-root.data']    
        if url_view == "": url_view = 'map'  
        if series != None: path = api_dict_raw_to_label[series]+"/"+str(year)+'/'+url_view #fix for experimental first load 
        else: path = ""        
        url = root_path+path                     
        
        # Update source extra information if relevant
        if series != None:
            popover_children = [
            dbc.PopoverHeader("Explanatory Notes"),            
            dbc.PopoverBody(master_config[series].get("note")), #WORKING
            ]
        else: popover_children = []
        
        print('SELECTION is ',selection)
        # Finally, check for experimental dataset and reset base map and view if necessary.
        if experiment_trigger == "Creme freesh":
            print('EXPERIMENT FOUND. Series label is',series_label)
            series = None #to ensure empty geomap is built
            df = None #just so can return without error
            navbtm_yr_style = {'display': 'none'} #hide
            navtm_yr_title_style = {'display':'none'}
            year = ''

        else:
            #subset master dataset to selected series and selected year (used to build new geomap) being careful to avoid experimental datasets      
            df = pop.loc[(pop['dataset_raw'] == series) & (pop['year'] == int(year))].sort_values('country')   
        """
        
        """    
        return \
        series, series_label, \
        charts.create_map_geomap(df, geojson, series, zoom, center, selected_map_location, mapstyle, colorbarstyle, settings_colorpalette_reverse), \
        source, link, \
        download_btn_style, bar_btn_style, line_btn_style, geobar_btn_style, sunburst_btn_style, globe_btn_style, bubble_btn_style, \
        year, \
        series_label+" in "+str(year), \
        navbtm_btns_style, navbtm_yr_style, navbtm_source_style,\
        year_slider_max, year_slider_marks, year_slider_selected, navtm_yr_title_style, navbtm_yr_title_val, \
        selection_m49, \
        url, \
        maptrigger, maptrigger, maptrigger, maptrigger, \
        popover_children, \
        experiment_trigger
        """
        
   
    #About modal callback
    @dash_app.callback(
        [Output("dbc-modal-about", "is_open"),
        Output("about-button", "active"),],     
        [Input("about-button", "n_clicks"), 
        Input("modal-about-close", "n_clicks")],
        [State("dbc-modal-about", "is_open")], 
        prevent_initial_call=True,
    )
    def callback_toggle_modal_about(n1, n2, is_open):
        if n1 or n2:
            logger.info("Modal about triggered")
            return not is_open, False
        return is_open, False
    
    #User Guide modal callback
    @dash_app.callback(
        Output("dbc-modal-uguide", "is_open"),
        [
        Input("uguide-button", "n_clicks"), 
        Input("modal-uguide-close", "n_clicks"),
        #Input("button-userguide-about", "n_clicks"),
        ],
        [State("dbc-modal-uguide", "is_open")], 
        prevent_initial_call=True,
    )
    def callback_toggle_modal_uguide(n1, n2, is_open):
        if n1 or n2:
            logger.info("Modal User Guide triggered")
            return not is_open    
        return is_open
    

    #Download dataset MAIN
    @dash_app.callback(Output('download_dataset_main', 'data'),
                [Input('btn-popover-map-download-xls', 'n_clicks'),
                Input('btn-popover-map-download-csv', 'n_clicks'),
                Input('btn-popover-map-download-json', 'n_clicks'),                              
                ],
                State("my-series","data"), 
                State('geomap_figure', 'figure'),
                prevent_initial_call=True,)
    def callback_download_dataset_main(n1, n2,n3, series_name_raw, fig): 

        selection = ctx.triggered_id          
            
        # Obtain cleaned df
        df = dobj.get_stats_for_dl(series_name_raw) 

        # Metadata for filename
        series = dobj.config_key_dsraw[series_name_raw]          
        series_label = series['dataset_label']       

        if selection == 'btn-popover-map-download-xls':
            filename = "WORLD_ATLAS_2.0 "+series_label+".xlsx" 
            def to_xlsx(bytes_io):
                xslx_writer = pd.ExcelWriter(bytes_io, engine="xlsxwriter")
                df.to_excel(xslx_writer, index=False, sheet_name="sheet1")
                xslx_writer.close()    
            return dcc.send_bytes(to_xlsx, filename)
        
        elif selection == 'btn-popover-map-download-csv':
            filename = "WORLD_ATLAS_2.0 "+series_label+".csv"     
            return dcc.send_data_frame(df.to_csv, filename, index=False)
        
        elif selection == 'btn-popover-map-download-json':          
            filename = "WORLD_ATLAS_2.0 "+series_label+".json"        
            return dcc.send_data_frame(df.to_json, filename, orient='table', index=False)
        
    
    #Bar graph modal
    @dash_app.callback(
        [
        Output("dbc-modal-bar", "is_open"),
        Output('bar-graph', 'figure'),
        Output("bar-graph-modal-title", "children"),
        Output("bar-graph-modal-footer", "children"),
        Output("bar-graph-modal-footer-link", "href"),
        #Output('my-loader-bar', "children"), #used to trigger loader. Use null string "" as output
        Output('bar-graph-dropdown-countrieselector', 'options'),
        Output('bar-graph-dropdown-dataset', 'options'), 
        Output('bar-graph-dropdown-year', 'options'),
        Output('my-series-bar','data'),
        Output('my-year-bar','data'),     
        #Output("my-url-bar-callback","data"),
        #Output('my-loader-bar-refresh','children'),
        ],
        [
        Input("my-url-bar-trigger", "data"), 
        Input("bar-button", "n_clicks"), 
        Input("modal-bar-close", "n_clicks"),
        Input("bar-graph-dropdown-countrieselector", "value"),
        Input("bar-graph-dropdown-dataset", "value"),
        Input('bar-graph-dropdown-year','value'),     
        ],
        [
        State("dbc-modal-bar", "is_open"),
        State("my-series", "data"), #map series selection 
        State("year-slider", "value"),  
        State("year-slider", "marks"),     
        State('bar-graph-dropdown-year','options'),
        State('url','href'),
        State("my-url-view", 'data'),       
        State("my-url-series", 'data'),
        State("my-url-year", 'data'),
        State('my-series-bar','data'),
        State('my-year-bar', 'data'),
        ],
        prevent_initial_call=True
    )
    def callback_toggle_modal_bar(bar_trigger, n1, n2, highlight_countries, select_dataset, select_year, is_open, series_map_state, year_slider_state, yeardict, dropdown_year_list, href, url_view, url_series, url_year, series_state, year_state):
            
        trigger = ctx.triggered_id
        states = ctx.states  
        print(f"Bar chart: {trigger}")
        print(states)

        # CASE: entry from map mode   
        if trigger == 'bar-button': 
            year = year_slider_state                        
            series_name = series_map_state            
        
        # CASE: year selection
        elif trigger == 'bar-graph-dropdown-year':
            year = int(select_year)            
            series_name = series_state
            
        # CASE: dataset selection
        elif trigger == 'bar-graph-dropdown-dataset':            
            series_name = select_dataset #this should be dsraw from the drop down 'value' (label:value)
            year = dobj.get_latest_year(series_name)
        
        # CASE: country highlight
        elif trigger == 'bar-graph-dropdown-countrieselector':
            series_name = series_state
            year = int(year_state)                   
        
        series = dobj.config_key_dsraw[series_name]  
        series_label = series['dataset_label']
        series_source = series['source']
        series_link = series['link']
        bar_graph_title = f"{series_label} in {str(year)}"             
        fig = charts.create_chart_bar(dobj, series, year, highlight_countries)    
        
        # Build country highlighter
        dropdown_countries = []
        for country in dobj.get_countries(series_name, year):
            dropdown_countries.append({'label': country, 'value': country}) 

        # Build year dropdown
        dropdown_years = []
        for yr in dobj.get_years(series_name):
            dropdown_years.append({'label': yr, 'value': yr}) 

        # Build series dropdown
        dropdown_dataset = []
        for series in dobj.get_numerical_series():            
            dropdown_dataset.append({'label': dobj.config_key_dsraw[series]['dataset_label'], 'value': series}) 
              
       
        return True, fig, bar_graph_title, series_source, series_link, dropdown_countries, dropdown_dataset, dropdown_years, series_name, year
       
           
        

        

        """
        # return out quickly on close     
        if trigger == 'modal-bar-close': return not is_open, {}, None,None,None,None,[],[],[], None, None, None, None   
        
        if trigger == 'my-url-bar-trigger':
            if url_view == '' or url_view == None or bar_trigger != 'bar': 
                #print("breaking out of bar callback!")
                raise PreventUpdate()
            else:
                # logic here. Can't wait for underlying map, so need year and series from somewhere else
                series = api_dict_label_to_raw[url_series]
                year = url_year                   
                series_label = master_config[series].get("dataset_label")         
                source = master_config[series].get("source")        
                link = master_config[series].get("link") 
                bar_graph_title = series_label+" in "+year  
                df = d.get_series_and_year(pop, year, series, False) 
              
                
            
        # case: entry from dataset selection 
        elif trigger == 'bar-graph-dropdown-dataset':        
                
            #if we have a manual selection set the series to this, otherwise we fall back on the underlying myseries selection from the map (already received as input)
            if dropdown_dataset != None: 
                series = dropdown_dataset        
            
            series_label = master_config[series].get("dataset_label")         
            source = master_config[series].get("source")        
            link = master_config[series].get("link") 
            
            #select the series (expensive)       
            df = d.get_series(pop, series, False)
            df['value'] = df['value'].astype(float)            
            
            #set to the most current year
            year = np.max(pd.unique(df["year"]))
            
            if dropdown_year != None and dropdown_year != "":
                
                availyrs = np.sort(pd.unique(df["year"]))           
                #logger.info("available years %r\nyear %r",availyrs, year)
                if str(dropdown_year) in availyrs:
                    #logger.info("setting year %r to dropdown_year %r", year, dropdown_year)
                    year = str(dropdown_year)
                #else it will be reset automatically by the drop down when it's not in the new list   
            
            #now subset to the most recent year        
            df = df[(df["year"] == year)].sort_values(by="value", ascending=False)    
            
            #update title
            bar_graph_title = series_label+" in "+str(year) 
        
        #case: country selector
        elif trigger == 'bar-graph-dropdown-countrieselector': 
            
            # case: map entry so use map data
            if dropdown_dataset == None or dropdown_dataset == '': 
                if dropdown_year == None or dropdown_year == '':
                    year = d.get_years(pop.loc[(pop['dataset_raw'] == series)])[yearid]
                else:
                    year = dropdown_year
                series_label = master_config[series].get("dataset_label")         
                source = master_config[series].get("source")        
                link = master_config[series].get("link") 
                bar_graph_title = series_label+" in "+str(year)
            
            # case: dataset selection
            else:
                series = dropdown_dataset            
                series_label = master_config[series].get("dataset_label")         
                source = master_config[series].get("source")        
                link = master_config[series].get("link")    
                df = d.get_series(pop, series, False)          
                
                if dropdown_year == None or dropdown_year == '':
                    year = np.max(pd.unique(df["year"]))
                else:
                    year = dropdown_year               
                bar_graph_title = series_label+" in "+str(year)     
            
            #select the series and year from pop data, and sort it descending
            df = d.get_series_and_year(pop, str(year), series, False)               
            
        elif trigger == 'bar-graph-dropdown-year':          
            
            #determine which series to use
            if dropdown_dataset != None and dropdown_dataset != '':
                series = dropdown_dataset
            
            #determine which year to use
            if dropdown_year == None:
                #year has been cleared, set to most recent            
                years = np.sort(pd.unique(pd.DataFrame(pop[(pop['dataset_raw']==series)], columns=['year'])['year'].astype(int)))
                year = str(years[-1])
            else:
                year = str(dropdown_year)        
            
            #update all vars               
            series_label = master_config[series].get("dataset_label")         
            source = master_config[series].get("source")        
            link = master_config[series].get("link") 
            bar_graph_title = series_label+" in "+year        
            
            #select the series and year from pop data, and sort it descending
            df = d.get_series_and_year(pop, year, series, False)    
        """

        # case: all conditions 
            
        # build dropdown list for datasets  (exclude discrete)  
        
        # get list of dicts for continuous and ratio, then combine them
        list_continuous = d.get_list_of_dataset_labels_and_raw(master_config,'continuous')
        list_ratio = d.get_list_of_dataset_labels_and_raw(master_config,'ratio')
        list_combined = list_continuous + list_ratio #won't be sorted
        
        # sort this list by label by converting to df and back to list
        list_combined = pd.DataFrame(list_combined).sort_values(by="dataset_label").to_dict('records') 
        
        #assemble into list of dicts for dataset dropdown
        dropdown_ds=[]
        for i in range(0,len(list_combined)):        
            dropdown_ds.append({'label': list_combined[i].get("dataset_label"), 'value': list_combined[i].get("dataset_raw")}) 
        
        # build dropdown list of unique countries available for the given dataset (in df)    
        
        # Find the unique countries for this dataset (all years) and sort 
        dd = np.sort(pd.unique(df["country"]).astype(str)) #numpy array. Had to conv to str as countries are categoricals now and was glitching
        
        #refresh list of country labels and vals for the dropdown
        dropdown_countries=[]
        for i in range(0,len(dd)):
            dropdown_countries.append({'label': dd[i], 'value': dd[i]})     
   
        # build dropdown list for available years
        dropdown_years=[]
        years = np.sort(pd.unique(pd.DataFrame(pop[(pop['dataset_raw']==series)], columns=['year'])['year'].astype(int)))    
        for i in range(0,len(years)):
                dropdown_years.append({'label': years[i], 'value': years[i]})   
            
        # build url
        #print("href: ",href)
        blah = href.split('/') 
        root = blah[0]+'//'+blah[2]+'/'
        url_bar = root + api_dict_raw_to_label[series] + '/' + str(year) + '/bar'
        
        # keep modal open in these conditions
        if trigger == 'bar-graph-dropdown-dataset' or trigger == 'bar-graph-dropdown-countrieselector' or trigger == 'bar-graph-dropdown-year': is_open = not is_open
        
        return not is_open, create_chart_bar(df, series, dropdown_countrieselector), bar_graph_title, source, link, "", dropdown_countries, dropdown_ds, dropdown_years, series, year, url_bar, ''
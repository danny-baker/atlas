from dash import dash, html, dcc
import dash_bootstrap_components as dbc
from . global_constants import *
from . import layout_globe_modal, layout_geobar_modal, layout_bargraph_modal, layout_linegraph_modal, layout_bubblegraph_modal, layout_sunburst_modal, layout_about_modal
from . import layout_userguide_modal, layout_settings_modal, layout_downloads_modal


# CSS bullshit
STYLE_BUTTON = {"marginLeft": 0, "marginBottom": 10, 'display': 'inline-block', 'opacity':INIT_BUTTON_OPACITY, 'fontSize': INIT_NAVFOOTER_BTN_FONT}


def build():
    
    #Builds out the nav footer including all modals
    
    # Bottom navbar (buttons for now)
    nav_footer = html.Div(
        [                  
                         
            # 1 main row with 3 columns
            dbc.Row([
                             
                    #Button panel
                    dbc.Col(                    

                        html.Div([                                     
                                
                            dbc.Row([                                                                 
                                html.Div([
                                    dbc.Button("USER GUIDE", color="primary", className="me-1", id="uguide-button", size=INIT_BUTTON_SIZE,style=STYLE_BUTTON),
                                    dbc.Button("SETTINGS", outline=INIT_BTN_OUTLINE, color="warning", className="me-1", id="settings-button", style=STYLE_BUTTON, size=INIT_BUTTON_SIZE),                                                                                                                                             
                                    dbc.Button("DOWNLOAD", outline=INIT_BTN_OUTLINE, color="success", className="me-1", id="download-button", disabled=False,style=STYLE_BUTTON, size=INIT_BUTTON_SIZE), #disabled on initial
                                    dcc.Download(id='download_dataset_main'),   
                                    dbc.Button("ABOUT", outline=INIT_BTN_OUTLINE, color="info", className="me-1", id="about-button", style=STYLE_BUTTON, size=INIT_BUTTON_SIZE),
                                ]),
                            ]),
                                                            
                            dbc.Row([
                                html.Div([                                  
                                    dbc.Button("BAR", outline=INIT_BTN_OUTLINE, color="dark", className="me-1", id="bar-button",style=STYLE_BUTTON, size=INIT_BUTTON_SIZE), #disabled on initial 
                                    dbc.Button("LINE", outline=INIT_BTN_OUTLINE, color="dark", className="me-1", id="line-button",style=STYLE_BUTTON, size=INIT_BUTTON_SIZE), #disabled on initial 
                                    dbc.Button("BUBBLE", outline=INIT_BTN_OUTLINE, color="dark", className="me-1", id="bubble-button",style=STYLE_BUTTON, size=INIT_BUTTON_SIZE),
                                    dbc.Button("PIZZA", outline=INIT_BTN_OUTLINE, color="dark", className="me-1", id='sunburst-button',style=STYLE_BUTTON, size=INIT_BUTTON_SIZE), #disabled on initial 
                                    dbc.Button("JIGSAW", outline=INIT_BTN_OUTLINE, color="dark", className="me-1", id="geobar-button",style=STYLE_BUTTON, size=INIT_BUTTON_SIZE),
                                    dbc.Button("GLOBE", outline=INIT_BTN_OUTLINE, color="dark", className="me-1", id="globe-button",style=STYLE_BUTTON, size=INIT_BUTTON_SIZE),
                                ]),
                            ]),        
                            
                        ],
                        id = 'button-panel-style',
                        #style = {'display': 'block', "marginLeft":"1vw" }, #I think this is needed somehow to make the secondary buttons wrap properly, it gets set to flexc
                        ),                           
                        style={"marginBottom": 5, "marginLeft": 10, 'backgroundColor': 'transparent', 'width':'33%', 'display':'inline-block', 'minWidth':INIT_NAVFOOTER_COMPONENT_MINWIDTH, }, #formatting for column 
                        align='end',                          
                              
                    ),
                    
                    
                    
                    dbc.Tooltip(
                        "Learn how to use this site",
                        target='uguide-button',
                        placement='top',
                        style={},
                    ), 
                    
                    
                    dbc.Tooltip(
                        "Download current dataset (all available countries and years)",
                        target='download-button',
                        placement='top',
                        style={},
                    ),

                    dbc.Popover(
                          [
                          dbc.PopoverHeader("Download", style={'fontWeight':'bold'}),
                          dbc.PopoverBody([
                              html.Div('Raw data'),
                              dbc.Button(".xlsx", outline=True, color="secondary", className="mr-1", id="btn-popover-map-download-xls", style={}, size=INIT_BUTTON_SIZE),
                              dbc.Button(".csv", outline=True, color="secondary", className="mr-1", id="btn-popover-map-download-csv", style={}, size=INIT_BUTTON_SIZE),
                              dbc.Button(".json", outline=True, color="secondary", className="mr-1", id="btn-popover-map-download-json", style={}, size=INIT_BUTTON_SIZE),
                              html.Div('Advanced', style={'marginTop':5,'display':'none'}),
                              dbc.Button("Downloads Area", outline=True, color="secondary", className="mr-1", id="btn-popover-map-download-land", style={'display':'none'}, size=INIT_BUTTON_SIZE),                              
                              ]),
                          ],
                          id="download-popover",                                        
                          target="download-button",                          
                          trigger="legacy",
                          placement="top",
                          hide_arrow=False,
                          
                    ),                    
                                    
                    dbc.Tooltip(
                        "Compare countries for a single dataset and year",
                        target='bar-button',
                        placement='top',
                        style={},
                    ),
                    
                    dbc.Tooltip(
                        "Compare trends across years for a single dataset",
                        target='line-button',
                        placement='top',
                        style={},
                    ),                    
                    
                    dbc.Tooltip(
                        "View the current map as an interactive 3d globe",
                        target='globe-button',
                        placement='top',
                        style={},
                    ),
                    
                    dbc.Tooltip(
                        "Compare up to three datasets",
                        target='bubble-button',
                        placement='top',
                        style={},
                    ),
                    
                    dbc.Tooltip(
                        "Think of a pie chart on steroids",
                        target='sunburst-button',
                        placement='top',
                        style={},
                    ),
                    
                    dbc.Tooltip(
                        "Turn the current map into a jigsaw puzzle (geo-bar) graph",
                        target='geobar-button',
                        placement='top',
                        style={},
                    ),
                    
                                       
                    layout_globe_modal.build(), 
               
                    layout_geobar_modal.build(), 
                                  
                    layout_bargraph_modal.build(),
                                     
                    layout_linegraph_modal.build(),                    
                                    
                    layout_bubblegraph_modal.build(),
                  
                    layout_sunburst_modal.build(),  
                   
                    layout_about_modal.build(),                    
                   
                    layout_userguide_modal.build(),
                    
                    layout_settings_modal.build(),
                    
                    layout_downloads_modal.build(), #Download land (not active)            
                    
                               
                    #year Slider 
                    dbc.Col([
                    #html.Div([ 
                        
                        html.Div("year_test", 
                                 style={'fontWeight': 'bold', 'color': INIT_year_SLIDER_FONTCOLOR, 'fontSize': INIT_year_SLIDER_FONTSIZE, 'align-items': 'center', 'justify-content': 'center','display': 'none', 'marginBottom':'0.5vmin'},
                                 id='year-slider-title'), 
                        
                        html.Div([                                
                           
                                
                            dcc.Slider(
                                id='year-slider',
                                min=0,
                                max=0,
                                #marks={ 0: {'label':'2005', 'style':{'color':'red', 'fontSize':12}}}, #dummy data. Overwritten
                                #marks={}, #dummy data. Overwritten
                                marks={0: {'label': '2020', 'style': {'fontSize': 14, 'color': 'grey', 'fontWeight': 'bold'}}},
                                value=0, 
                                included=False,                                
                                #disabled=True,
                            )],
                            
                            id='year-slider-style', #div id
                            #style={'display': 'none'}, #use only one style value, to udpate with callback (initially slider is invisible)
                        ),
                        ], 
                        style={"marginTop": 15, "marginLeft": 0, 'backgroundColor': 'transparent', 'width':'33%', 'display':'inline-block', 'minWidth':INIT_NAVFOOTER_COMPONENT_MINWIDTH}, #use col to move slider down
                        align='end', 
                    ),
                    
                        

                    #Data source 
                    dbc.Col(                    

                        [
                              
                            html.Div([
                                html.Span("Data source: ", style={'fontSize':INIT_SOURCE_FONT}),
                                html.Span("No data selected", id="my-source", style={'fontSize':INIT_SOURCE_FONT}),                                
                                html.Div(dcc.Link(href='', target="_blank", id="my-source-link", style={'fontSize':INIT_SOURCE_FONT, 'color':'LightBlue'})),                                
                            ], id="source-popover-target", style={"marginBottom": 0, "marginTop": 0, "marginLeft": 0, "marginRight": 0, "fontSize": INIT_SOURCE_POPOVER_FONT, 'backgroundColor': INIT_TITLE_BG_COL, 'opacity': INIT_TITLE_OPACITY,'color':INIT_TITLE_COL}),
                            
                            dbc.Popover(
                                [
                                dbc.PopoverHeader("Dummy", style={'fontWeight':'bold'}),
                                dbc.PopoverBody("Dummy"),
                                ],
                                id="source-popover",
                                #is_open=False,
                                target="source-popover-target",
                                style={'maxHeight': '400px', 'overflowY': 'auto', },
                                trigger="hover",
                                placement="top",
                                hide_arrow=False,
                                #style={'backgroundColor': INIT_TITLE_BG_COL, 'opacity': INIT_TITLE_OPACITY,'color':INIT_TITLE_COL, 'width':'100%'}
                            ),                            
                       ],
                    id = 'data-source-style',
                    #style = {'display': 'none'}, #default hidden 
                    align='end',               
                    
                    ),                                                      
                ],                
                #style={'display': 'flex', 'align-items': 'flex-end'}
                #style={'align-items': 'center', 'justify-content': 'center'}
                
            ),
            
            
        ],
        style={
                "width": INIT_NAVFOOTER_W,
                #"margin-left": "1vw",
                #"margin-right": "auto",
                "position": "absolute",
                "z-index": "2",
                #"top": INIT_NAVFOOTER_POSITION,
                "bottom": INIT_NAVFOOTER_OFFSET,
                #'vertical-align':'bottom',
                #"left": "5vw",
                #'display':'inline-block',
            },
    )
    return nav_footer

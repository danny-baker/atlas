#from dash import dash, html, dcc
from . global_constants import *
import logging
import plotly.express as px
import plotly.graph_objs as go
import numpy as np
import copy

#Obtain the root logger
logger = logging.getLogger(LOGGER)


def create_map_geomap_empty():
    #No method overloading in python, so have an empty map load for initial.
    logger.info("Creating geomap empty...")
    
    fig = go.Figure(
        go.Choroplethmapbox(),
        layout=go.Layout(uirevision='some_constant_value')
    )
    
    fig.update_layout(
        mapbox_style=mapbox_style[1], #default
        mapbox_zoom=INIT_ZOOM,
        mapbox_center={"lat": INIT_LATITUDE, "lon": INIT_LONGITUDE},   
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
    )
    return fig


def create_map_geomap(dobj, series, colorpalette, colorpalette_reverse):    
    
    series_name = series['dataset_raw']
    var_type = series['var_type']
    year = dobj.get_latest_year(series_name)
    stats = dobj.get_stats(series_name=series_name, year=year)
    geojson = dobj.map_lowres
    mapstyle = mapbox_style[1] #default for now

    # DISCRETE DATA
    if var_type == 'discrete':            
        
        logger.info("Create Geomap: 'discrete' data")        
    
        hovertemp = "%{customdata}: %{text}<extra></extra>"         
        fig = go.Figure()
                    
        for i, discrete_classes in enumerate(stats['value'].unique()): 
            #Loop through all the discrete classes and add a coloured trace
            logger.info("Create discrete geomap.Iterator i and type are: %r, %r",i, discrete_classes)
            
            #subset dataframe to a discrete class
            t = stats[stats["value"] == discrete_classes]
            
            #optimisation: strip out unneeded json before passing to fig.add 
            #loop through JSON and pull anything from the mask
            gj = copy.deepcopy(geojson)
            gj['features'].clear()
            for j in range(0,len(geojson['features'])):                
                if geojson['features'][j]['properties']['UN_A3'] in t.m49_un_a3.values:                    
                    gj['features'].append(geojson['features'][j])               
                        
            #add a choroplethmapbox trace passing just the JSON fragments needed for each discrete category
            fig.add_choroplethmapbox(geojson=gj, #send the bare minimum json each time
                                    locations=t.m49_un_a3,
                                    z=[i,] * len(t),                                     
                                    featureidkey="properties.UN_A3", #this is the link to the gejson
                                    showlegend=True,
                                    name=discrete_classes,
                                    customdata=t['country'],  
                                    text=t['value'],
                                    hovertemplate=hovertemp,
                                    colorscale=discrete_colorscale[i],                                     
                                    showscale=False,
                                    marker_opacity=0.5,
                                    marker_line_width=1)        
                    
        fig.update_layout(
            mapbox_style=mapstyle,
            mapbox_zoom=INIT_ZOOM,
            mapbox_center={"lat": INIT_LATITUDE, "lon": INIT_LONGITUDE},   
            margin={"r": 0, "t": 0, "l": 0, "b": 0},        
        )
        
        return fig

    # CONTINUOUS DATA
    elif var_type == 'continuous' or var_type == 'ratio':

        logger.info("Create Geomap: 'continuous' or 'ratio' dataset")
                            
        # format numbers in d3 format
        print("Mean value is ",stats['value'].astype(float).mean())
        hovertemp = "%{customdata} %{text:,.2f}<extra></extra>" 
        if stats["value"].astype(float).mean() > 1000000: hovertemp = "%{customdata} %{text:,d}<extra></extra>" #large number formatting no decmials e.g. 123,000,000                
                
        fig = go.Figure(
            go.Choroplethmapbox(
                geojson=geojson,
                locations=stats.m49_un_a3,              
                featureidkey="properties.UN_A3",                
                z=np.log10(stats['value'].astype(float)),  #use log scale to naturally normalise. 
                text=stats['value'],
                customdata=stats['country'],                
                hoverinfo="location+text",
                hovertemplate=hovertemp,             
                colorscale=colorpalette,
                reversescale=colorpalette_reverse,                
                colorbar= {'ticks': '', 'title': {'text': 'HIGH', 'side': 'top'}, 'showticklabels': False, 'bgcolor': 'rgba(0,0,0,0)', 'outlinewidth':0 },  #'xpad': 20, 'borderwidth': 10, 'bgcolor': 'blue'
                zauto=True,
                marker_opacity=0.5,
                marker_line_width=1,
            ),
            layout=go.Layout(uirevision='some_constant_value') #this auto preserves zoom state etc.
        )
            
        #add in some extras (needs to be done like this)
        fig.update_layout(                             
            mapbox_style=mapbox_style[1], #default
            mapbox_zoom=INIT_ZOOM,
            mapbox_center={"lat": INIT_LATITUDE, "lon": INIT_LONGITUDE},   
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
        )

        return fig




def create_map_geomap_old(df, geojson, series, zoom, center, selected_map_location, mapstyle, colorbarstyle, colorpalette_reverse):      
        
    logger.info("Create Geomap...")
    
    if series == None: return create_map_geomap_empty()  #speical case for if settings are applied before a dataset is selected. Cmplicated logic.
    
    #determine if selected dataset is discrete or continuous
    var_type = master_config[series].get("var_type")         
    #logger.info("Creating geomap with zoom %r and centre %r for series %r and variable type %r", zoom, center, series, var_type)
    
    #DISCRETE DATA
    if var_type == "discrete":
        #print("Discrete data found. Dataframe length is:", len(df))        
        #print("data types ",df.dtypes)
        #print("discrete classes found ",len(df['value'].unique()))
        
        #build figure out here for discrete data        
        hovertemp = "%{customdata}: %{text}<extra></extra>" 
        
        fig = go.Figure()
        
        #Loop through all the discrete classes and add a coloured trace
        for i, discrete_classes in enumerate(df['value'].unique()): 
            #logger.info("Create discrete geomap.Iterator i and type are: %r, %r",i, discrete_classes)
            
            #subset dataframe to a discrete class
            t = df[df["value"] == discrete_classes]
            
            #optimisation: strip out unneeded json before passing to fig.add            
            
            #loop through JSON and pull anything from the mask
            gj = copy.deepcopy(geojson)
            gj['features'].clear()
            for j in range(0,len(geojson['features'])):                
                if geojson['features'][j]['properties']['UN_A3'] in t.m49_un_a3.values:                    
                    gj['features'].append(geojson['features'][j])                
             
            
            #add a choroplethmapbox trace passing just the JSON fragments needed for each discrete category
            fig.add_choroplethmapbox(geojson=gj, #send the bare minimum json each time
                                     locations=t.m49_un_a3,
                                     z=[i,] * len(t),                                     
                                     featureidkey="properties.UN_A3", #this is the link to the gejson
                                     showlegend=True,
                                     name=discrete_classes,
                                     customdata=t['country'],  
                                     text=t['value'],
                                     hovertemplate=hovertemp,
                                     colorscale=discrete_colorscale[i],                                     
                                     showscale=False,
                                     marker_opacity=0.5,
                                     marker_line_width=1)
           
                    
        fig.update_layout(
            mapbox_style=mapstyle,
            mapbox_zoom=zoom,
            mapbox_center=center, #{"lat": -8.7, "lon": 34.5},
            margin={"r": 0, "t": 0, "l": 0, "b": 0},        
        )
        
        return fig
    
    
    #ALL OTHER DATA TYPES (non-discrete)
    else:
    
        logger.info("Create Geomap: 'continuous' or 'ratio' dataset")
                            
        # format numbers in d3 format
        #print("Mean value is ",df['value'].astype(float).mean())
        hovertemp = "%{customdata} %{text:,.2f}<extra></extra>" 
        if df["value"].astype(float).mean() > 1000000: hovertemp = "%{customdata} %{text:,d}<extra></extra>" #large number formatting no decmials e.g. 123,000,000                
                
        #Build main figure
        fig = go.Figure(
            go.Choroplethmapbox(
                geojson=geojson,
                locations=df.m49_un_a3, #if you correct and link on the country name, can free up customdata field for the units                
                featureidkey="properties.UN_A3",                
                z=np.log10(df['value'].astype(float)),  #use log scale to naturally normalise. 
                text=df['value'],
                customdata=df['country'],                
                hoverinfo="location+text",
                hovertemplate=hovertemp,             
                colorscale=colorbarstyle,
                reversescale=colorpalette_reverse,
                #this is a dict and I think can set all the params of colorbar here. scale etc. Either object of type colorbar, or dict with compat properties
                colorbar= {'ticks': '', 'title': {'text': 'HIGH', 'side': 'top'}, 'showticklabels': False, 'bgcolor': 'rgba(0,0,0,0)', 'outlinewidth':0 },  #'xpad': 20, 'borderwidth': 10, 'bgcolor': 'blue'
                zauto=True,
                marker_opacity=0.5,
                marker_line_width=1,
            )
        )
            
        #add in some extras (needs to be done like this)
        fig.update_layout(
            mapbox_style=mapstyle,
            mapbox_zoom=zoom,
            mapbox_center=center, #{"lat": -8.7, "lon": 34.5},
            margin={"r": 0, "t": 0, "l": 0, "b": 0},              
        )
     
    return fig
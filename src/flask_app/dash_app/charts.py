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


def create_map_geomap(dobj, series, colorpalette, colorpalette_reverse, year):    
    
    series_name = series['dataset_raw']
    var_type = series['var_type']
    #year = dobj.get_latest_year(series_name)
    stats = dobj.get_stats(series_name=series_name, year=year, sort_by='country', ascending=True)
    geojson = dobj.map_lowres
    mapstyle = mapbox_style[1] #default for now

    print(series)

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
    elif var_type == 'continuous' or var_type == 'ratio' or var_type == 'quantitative':

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
    



def create_chart_bar(dobj, series, year, highlight_countries:list):     
        
    #lookup the series label from the dataset_lkup df
    series_label = series['dataset_label']                
    series_name = series['dataset_raw']    
    df = dobj.get_stats(series_name, year, sort_by='value', ascending=False)    
    logger.info("Creating bar graph with series %r", series_label, )
   
    #Colour a new column of the df based on any selections received
    
    #first colour all markers to a nice default
    df['color'] = "rgb(158,202,225)"
    
    #If there is list of countries to mark, set the colour to black
    if highlight_countries != None:
       for country in highlight_countries:
            df.loc[df['country']==country, 'color'] = 'black' #discrete_colorscale[i][0][1]        
       
    #build using graph object
    fig = go.Figure([
        go.Bar(
            x=df['country'],
            y=df['value'],            
            hovertemplate="%{x} %{y:}<extra></extra>",
            opacity=0.7,
            )
        ])
    
    # Customize aspect
    fig.update_traces(            
        marker={'color': df['color']}, #fuck yeeeeeh            
        marker_line_width=0,
        opacity=0.7,
        #texttemplate='%{text:.2s}',
        #textposition='outside'
    )  
    
    fig.update_layout({
        'plot_bgcolor': 'white',
        'paper_bgcolor': 'white',        
        },
        yaxis_title=series_label,)   
    
    return fig

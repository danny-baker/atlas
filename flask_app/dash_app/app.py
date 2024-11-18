# This is the main python web application in Plotly Dash.
# It has a few helper files which are imported, but the core code for the entire app is here
# At run-time, it reads in geojson polygons (for country borders), the master statistics file (15M rows) and a master config file (which defines the menu structure and data types for each dataset)

from . import data_processing_runtime as d  # run-time processing
#from . import data_paths as paths
from . import dash_html #index page
from . import hovertip_text
from . import modal_text
import logging
import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
import dash_deck
from dash_extensions import Download
from dash_extensions.snippets import send_data_frame, send_bytes, send_file
from dash.exceptions import PreventUpdate #for raising exception to break out of callbacks
import pydeck
import json
import copy
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
import os
from dotenv import load_dotenv
from PIL import ImageColor #colour fun
from functools import reduce #array fun for year intersects
import time
import xlsxwriter #needed for linux Ubuntu server
import plotly
import gc

# config
DEBUG=False

# setup logger to console
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("atlas")

# Azure storage blob config (access cloud data)
load_dotenv()
container_name  = os.getenv("AZURE_STORAGE_ACCOUNT_CONTAINER_NAME")
account_name = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
account_key = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
#sudo docker run -p 80:8050 -v /home/dan/atlas/.env:/usr/src/app/.env ghcr.io/danny-baker/atlas/atlas_app:latest

# setup system
if os.path.exists("tmp") == False: 
    os.mkdir("tmp")  # this is used to store charts and zip files on server OS until in memory solution is found

# initialise dash layout and callbacks
def init_dashboard(server):
    
    # Create Dashboard
    dash_app = dash.Dash(
        server=server,
        routes_pathname_prefix='/',
        external_stylesheets=[
            #'/static/dist/css/styles.css',
            dbc.themes.FLATLY #FLATLY UNITED SANDSTONE PULSE
        ],
        update_title=None          
    )

    # Create Dash Layout
    dash_app._favicon = ("favicon.ico") #must be in /assets/favicon.ico 
    dash_app.title = "WORLD ATLAS 2.0" #browser tab
    dash_app.index_string = dash_html.index_string
    create_dash_layout(dash_app)

    # Initialize callbacks after our app is loaded
    init_callbacks(dash_app)

    return dash_app.server



#DECLARE GLOBAL APPLICATION DATA

mapbox_style = ["open-street-map", "carto-positron", "carto-darkmatter", "stamen-terrain", "stamen-toner", "stamen-watercolor"]

geomap_colorscale = ["auto", 'aggrnyl', 'agsunset', 'algae', 'amp', 'armyrose', 'balance',
             'blackbody', 'bluered', 'blues', 'blugrn', 'bluyl', 'brbg',
             'brwnyl', 'bugn', 'bupu', 'burg', 'burgyl', 'cividis', 'curl',
             'darkmint', 'deep', 'delta', 'dense', 'earth', 'edge', 'electric',
             'emrld', 'fall', 'geyser', 'gnbu', 'gray', 'greens', 'greys',
             'haline', 'hot', 'hsv', 'ice', 'icefire', 'inferno', 'jet',
             'magenta', 'magma', 'matter', 'mint', 'mrybm', 'mygbm', 'oranges',
             'orrd', 'oryel', 'peach', 'phase', 'picnic', 'pinkyl', 'piyg',
             'plasma', 'plotly3', 'portland', 'prgn', 'pubu', 'pubugn', 'puor',
             'purd', 'purp', 'purples', 'purpor', 'rainbow', 'rdbu', 'rdgy',
             'rdpu', 'rdylbu', 'rdylgn', 'redor', 'reds', 'solar', 'spectral',
             'speed', 'sunset', 'sunsetdark', 'teal', 'tealgrn', 'tealrose',
             'tempo', 'temps', 'thermal', 'tropic', 'turbid', 'twilight',
             'viridis', 'ylgn', 'ylgnbu', 'ylorbr', 'ylorrd']

#build discrete colourscale (16 available)
discrete_colorscale = [
    ((0.0, '#792069'), (1.0, '#792069')), #purple
    ((0.0, '#FFBB33'), (1.0, '#FFBB33')), #orangy
    ((0.0, '#00cc96'), (1.0, '#00cc96')), #green (0,204,150)       
    ((0.0, '#EF553B'), (1.0, '#EF553B')), #red (239,85,59)    
    ((0.0, '#636efa'), (1.0, '#636efa')), #blue (99,110,25)         
    ((0.0, '#7F8C8D'), (1.0, '#7F8C8D')), #grey
    ((0.0, '#0dc9b6'), (1.0, '#0dc9b6')), #cyan
    ((0.0, '#eac1c1'), (1.0, '#eac1c1')), #yuk pink
    ((0.0, '#fff8b7'), (1.0, '#fff8b7')), #cream
    ((0.0, '#264f7d'), (1.0, '#264f7d')), #navy blue
    ((0.0, '#95b619'), (1.0, '#95b619')), #yellowy
    ((0.0, '#99b8cc'), (1.0, '#99b8cc')), #bluey
    ((0.0, '#853d55'), (1.0, '#853d55')), #beige
    ((0.0, '#542709'), (1.0, '#542709')), #poo brown
    ((0.0, '#4db0bd'), (1.0, '#4db0bd')), #turcoise
    ((0.0, '#13ad20'), (1.0, '#13ad20')), #green as fuck
]

#Initialise default settings
INIT_BORDER_RES = 0
INIT_COLOR_PALETTE = 39 #fall 28 
INIT_COLOR_PALETTE_REVERSE = True
INIT_MAP_STYLE = 1
INIT_TITLE_TEXT = "WORLD  ATLAS  2.0"
INIT_TITLE_H = "6vmin" # "7vh"
INIT_TITLE_DIV_H = "7vmin"
INIT_TITLE_PAD_TOP = "1vmin"
INIT_TITLE_COL = "white"                                 # title colour
INIT_TITLE_BG_COL = "grey"                               # title background
INIT_TITLE_OPACITY = 0.8                                 # title opacity
INIT_BUTTON_OPACITY = 0.9                                # button opacity
INIT_BTN_OUTLINE = False
INIT_year_SLIDER_FONTSIZE = "1.5vmin"
INIT_year_TITLE_FONTSIZE = "2vmin" #2vmin
INIT_year_SLIDER_FONTCOLOR = 'grey'
INIT_SELECTION_H = "2.3vmin"  #was 2.3
INIT_NAVBAR_H = "7vmin"                                # NAVBAR HEIGHT
INIT_NAVBAR_W = "100vw" 
INIT_NAVBAR_FONT_H = "1.6vmin"                         #was 1.35vmin making larger for chrome tradeoff
INIT_NAVBAR_SEARCH_WIDTH ='30vw'
INIT_NAVBAR_SEARCH_FONT = "1.5vmin" 
INIT_RANDOM_BTN_TEXT = "PRESS ME"
INIT_RANDOM_BTN_FONT = "1.35vmin"
INIT_MAP_H = "88vh"                                   # MAP HEIGHT was 92.75. was 88 for firefox. Dropping for chrome windows. Was 87.
INIT_MAP_W = "100vw"
INIT_BAR_H = "55vmin"
INIT_LINE_H = "50vmin"
INIT_BUBBLE_H = "50vmin"
INIT_SUNBURST_H = "60vh"
INIT_JIGSAW_H = "65vh"
#INIT_JIGSAW_W = "50vw"
INIT_GLOBE_H = "72vh"
INIT_EXPERIMENT_H = '90vh'
#INIT_BUTTON_FONT_H = "1.1vmin"
INIT_BUTTON_SIZE = 'sm'
INIT_DROPDOWNITEM_LPAD = 0
INIT_DROPDOWNITEM_RPAD = "0.65vw"
INIT_SETTINGS_BORDER_CARD_WIDTH = "19vh" #settings modal was 17vh
INIT_SETTINGS_MAP_CARD_WIDTH = "18vh" #settings modal
INIT_SETTINGS_DL_CARD_WIDTH = '31.5%'
INIT_UGUIDE_MODAL_W = "70%"
INIT_SETTINGS_MODAL_W = "70%"
INIT_GLOBE_MODAL_W = "70%"
INIT_BAR_MODAL_W = "90%"
INIT_DL_MODAL_W = "70%"
INIT_LINE_MODAL_W = "70%"
INIT_BAR_BUBBLE_W = "70%"
INIT_SUNBURST_MODAL_W = "70%"
INIT_JIGSAW_MODAL_W = "70%"
INIT_ABOUT_MODAL_W = "60%"
INIT_AREA51_NAVBAR_W = '35vw'
INIT_NAVFOOTER_W = '97vw' #100% causes scroll bar to appear 97.5vw good for firefox. But dropping to test.
INIT_NAVFOOTER_OFFSET = "5.5vmin" #This is optimised for wide aspect. it pushes nav footer too high on narrow portrait screens. Try to detect?
INIT_NAVFOOTER_BTN_FONT = "1.35vmin" 
INIT_NAVFOOTER_COMPONENT_MINWIDTH = 400
INIT_SOURCE_POPOVER_FONT = "1.5vmin" #does not appear to be working. Could be a bug with the popover style
INIT_SOURCE_FONT = "1.5vmin"
INIT_LATITUDE = 24.32570626067931 
INIT_LONGITUDE = 6.365789817509949
INIT_ZOOM = 1.6637151294876884
#Fonts
#Title font "allstar, ca, bal, bank, capt1, capt2, commodore, const, game, lady, miss, prometheus, mario, aad, amnestia, betel, bord, emy, reduza, maizen
#like: miss, madio, amnestia, betel
#refined/timeless: const
#futuristic scifi: betel, lady
#old school fantasy: amnestia
#8 bit retro stylised: miss, mario, commodore
INIT_FONT_MASTER = ""
INIT_TITLE_FONT = INIT_FONT_MASTER 
INIT_MODAL_HEADER_FONT_GENERAL = INIT_FONT_MASTER #the default font for heading
INIT_MODAL_HEADER_FONT_UGUIDE = INIT_FONT_MASTER
INIT_MODAL_HEADER_FONT_SETTINGS = INIT_FONT_MASTER
INIT_MODAL_HEADER_FONT_ABOUT = INIT_FONT_MASTER
INIT_MODAL_HEADER_FONT_SIZE = "4vmin"
INIT_MODAL_HEADER_FONT_WEIGHT = "bold"
INIT_MODAL_FOOTER_FONT_SIZE = 12
INIT_SUNBURST_MODAL_HEADER_FONT_SIZE = '3vmin'
INIT_LOADER_DATASET_COLOR = "#3E3F3A"
INIT_LOADER_CHART_COLOR = "#3E3F3A"
INIT_LOADER_CHART_COMPONENT_COLOR = "#3E3F3A"
INIT_LOADER_TYPE = 'dot'


## LOAD APP DATA ## CONSIDER LOADING THESE IN PARALLEL WITH THREAD POOLING

#Load geojson 2d region data
geojson_LOWRES = d.read_blob(account_name, account_key, container_name,'geojson/map/ne_110m.geojson', 'json', 'json')
geojson_MEDRES = d.read_blob(account_name, account_key, container_name,'geojson/map/ne_50m.geojson', 'json', 'json')
geojson_HIRES = d.read_blob(account_name, account_key, container_name,'geojson/map/ne_10m.geojson', 'json', 'json')

#Load geojson 3d region data
geojson_globe_land_ne50m = d.read_blob(account_name, account_key, container_name,'geojson/globe/ne_50m_land.geojson', 'json', 'json') # load contries
geojson_globe_ocean_ne50m = d.read_blob(account_name, account_key, container_name,'geojson/globe/ne_50m_ocean.geojson', 'json', 'json') #load oceans
geojson_globe_land_ne110m = d.read_blob(account_name, account_key, container_name,'geojson/globe/ne_110m_land_cultural.geojson', 'json', 'json') # load countries
geojson_globe_ocean_ne110m = d.read_blob(account_name, account_key, container_name,'geojson/globe/ne_110m_ocean.geojson', 'json', 'json') # load oceans
del(geojson_globe_ocean_ne110m['features'][0]['geometry']['coordinates'][12]) #americas, also a problem on ne50m

# Load config (Dictionary of all datasets, their metadata and how to display them in the overhead nav menu)
master_config, master_config_key_datasetid, master_config_key_nav_cat = d.read_master_config(['dataset_raw', 'dataset_id', 'nav_cat'],account_name, account_key, container_name, 'meta/master_config.csv' )

#Load master stats dataset
pop = d.read_blob(account_name, account_key, container_name,'statistics/master_stats.parquet', 'parquet', 'dataframe')

# Load experimental datasets
EXP_POWER_PLANTS = d.read_blob(account_name, account_key, container_name, 'geojson/global-power-stations/xp1_global_power_plant_database.parquet', 'parquet', 'dataframe')

#Set global dataset size indicators (for text in search bar)
DATASETS = len(pd.unique(pop['dataset_raw'])) 
OBSERVATIONS = len(pop.index)
SERIES = pd.unique(pop['dataset_raw']) #for randomising

# set global api lookup dicts (for url path operations)
api_dict_raw_to_label, api_dict_label_to_raw = d.create_api_lookup_dicts(master_config)


#@cache.memoize(timeout=CACHE_TIMEOUT)
def create_chart_bar(df, series, dropdown_choices):     
        
    #lookup the series label from the dataset_lkup df
    series_label = master_config[series].get("dataset_label") 
            
    logger.info("Creating bar graph with series %r", series, )
      
    #Colour a new column of the df based on any selections received
    
    #first colour all markers to a nice default
    df['color'] = "rgb(158,202,225)"
    
    #If there is an array of countries to mark, set the colour to black
    if dropdown_choices != None:
        for i in range(0,len(dropdown_choices)):
            df.loc[df['country']==dropdown_choices[i], 'color'] = 'black' #discrete_colorscale[i][0][1]        
    
    #GRAPH OBJECT VERSION
    #build using graph object
    fig = go.Figure([
        go.Bar(
            x=df['country'],
            y=df['value'],            
            hovertemplate="%{x} %{y:}<extra></extra>",
            opacity=0.7,
            )
        ])
       
        
    #PX VERSION (FOR ANIMATION)
    
    '''
    #can do sick animations in px, but tradeoff with the marking thing
    fig = px.bar(
            df,    
            x='country',
            y='value',
            labels={'value': series_label},
            #color='color',
            #animation_frame="year",
            #animation_group="value",
            #range_y=[0,5000000]                
            
            )'''
    
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


def create_chart_line(df, series, dropdown_choices):  
    
    #lookup the series label from the dataset_lkup df
    series_label = master_config[series].get("dataset_label")   
   
    logger.info("Creating line graph with series %r", series)
          
    #get unique, ordered list of years for selected series
    chartdata = pd.DataFrame(np.sort(pd.unique(df["year"])), columns=["year"]).copy() #numpy array...fix for pop
    
    #loop through dropdown_choices and populate chartdata array    
    if dropdown_choices != None:
        for i in range(0,len(dropdown_choices)):
            
            #create a new column for each country
            chartdata[dropdown_choices[i]] = "hello"
            
            #for this country, set any vals found in dataset (be sure to do a isin check first)
            for j in range(0,len(chartdata)):
                
                #check to see if data exists for this country and year (avoids a key error)                
                if chartdata.iloc[j][0] in df[(df['country']==dropdown_choices[i])].year.values:                    
                    #update chart data with corresponding value for this country and year
                    chartdata.loc[chartdata.year == chartdata.iloc[j][0], dropdown_choices[i]] = df[(df['country']==dropdown_choices[i]) & (df['year']==chartdata.iloc[j][0])].iloc[0][4]
                
                else:                    
                    #this country must be missing some data points compared to others in the set
                    chartdata.loc[chartdata.year == chartdata.iloc[j][0], dropdown_choices[i]] = None
    
   
    # set line width based on number of countries
    if len(dropdown_choices) <=10: width=3
    elif len(dropdown_choices) > 10 and len(dropdown_choices) <= 40: width=2
    else: width=1
    
   
    # now build the figure
    fig = go.Figure()
    
    if dropdown_choices != None:
        for k in range(0,len(dropdown_choices)):  
            
            #build custom list for hover template (must be country name repeated)
            countryname = [dropdown_choices[k]] * len(chartdata)                        
            
            fig.add_trace(go.Scatter(
                x=chartdata['year'],
                y=chartdata[dropdown_choices[k]],
                name=dropdown_choices[k], # Style name/legend entry with html tags
                showlegend=True,
                customdata=countryname,
                hovertemplate="%{customdata} %{y:} (%{x})<extra></extra>", # e.g. "America 45.3 (2009)"
                connectgaps=True, 
                line=dict(width=width),
                #mode='lines+markers',
            ))
           
        
        fig.update_layout(
                       #xaxis_title='Month',
                       yaxis_title=series_label,                       
                       )
         
  
    
    return fig


def create_chart_bubble(x, y, z, year, xlog, ylog, zlog):      
    
    #logger.info("\nCreating bubble graph:\ndropx %r \ndropy %r \ndropz % r \nyear %r\nxlog %r\nylog %r\nzlog %r",x,y,z,year,xlog,ylog,zlog )  
    
    
    #return from function if no datasets
    if (x == None and y == None and z == None) or year == None or year == '':
        #return blank scatter
        fig = px.scatter()
        return fig
    
    #Build 3 dataframes as precursor to chart data
    if x != None:
        dfx = pop[(pop['dataset_raw']==x) & (pop['year']==year)].rename(columns={"value":x})        
        dfx[x] = dfx[x].astype(float)
        #d.add_regions(dfx,country_lookup) #add regions
        seriesX_label = master_config[x].get("dataset_label") 
    
    if y != None:
        dfy = pop[(pop['dataset_raw']==y) & (pop['year']==year)].rename(columns={"value":y})
        dfy[y] = dfy[y].astype(float)
        #d.add_regions(dfy,country_lookup) #add regions
        seriesY_label = master_config[y].get("dataset_label") 
    
    if z != None:
        dfz = pop[(pop['dataset_raw']==z) & (pop['year']==year)].rename(columns={"value":z})
        dfz[z] = dfz[z].astype(float)
        #d.add_regions(dfz,country_lookup) #add regions
        seriesZ_label = master_config[z].get("dataset_label") 
    
    #we're gonna need logic for every input combination so user can experience the chart growing dynamically
      
    # x only
    if x!=None and y==None and z==None:
        dfa = dfx
        #print("x")
        fig = px.scatter(dfa,
                     x=x,
                     #y=y,
                     #size=z,
                     labels={x: seriesX_label, 'continent':'Continent'},
                     color="continent",
                     hover_name="country",
                     log_x=xlog,
                     size_max=60)
        #fig.update_layout(xaxis_title=x)
    
    # x y only
    elif x!=None and y!=None and z==None:
        common_countries = reduce(np.intersect1d,(dfx['country'].values,dfy['country'].values))
        dfx = dfx[dfx['country'].isin(common_countries)]
        dfy = dfy[dfy['country'].isin(common_countries)]
        dfa = pd.merge(dfx,dfy[['country',y]],on='country', how='left')
        #print("xy")
        fig = px.scatter(dfa,
                     x=x,
                     y=y,
                     #size=z,
                     labels={x: seriesX_label, y: seriesY_label,  'continent':'Continent'},
                     color="continent",
                     hover_name="country",
                     log_x=xlog,
                     log_y=ylog,
                     size_max=60)
        #fig.update_layout(xaxis_title=x, yaxis_title=y)
        
    # x z only
    elif x!=None and y==None and z!=None:    
        common_countries = reduce(np.intersect1d,(dfx['country'].values, dfz['country'].values))
        dfx = dfx[dfx['country'].isin(common_countries)]        
        dfz = dfz[dfz['country'].isin(common_countries)]
        dfa = pd.merge(dfx,dfz[['country',z]],on='country', how='left')
        #print("xz")
        
        #custom logic for log z as it is not available in px function
        if zlog == True:
            #get the log of the list, and then normalise it to 0 and above by adding the absolute value of the min to every element
            size = np.log10(dfa[z].astype(float))+abs(min(np.log10(dfa[z].astype(float))))
        else:
            size = dfa[z]
        
        fig = px.scatter(dfa,
                     x=x,
                     #y=y,
                     size=size,
                     labels={x: seriesX_label, z: seriesZ_label, 'continent':'Continent' },
                     color="continent",
                     hover_name="country",
                     log_x=xlog,
                     size_max=60)
        #fig.update_layout(xaxis_title=x)
        
    # y only    
    elif x==None and y!=None and z==None:
        dfa = dfy
        #print("y")
        fig = px.scatter(dfa,
                     #x=x,
                     y=y,
                     #size=z,
                     labels={y: seriesY_label, 'continent':'Continent'},
                     color="continent",
                     hover_name="country",
                     log_x=xlog,
                     log_y=ylog,
                     size_max=60)
        #fig.update_layout(yaxis_title=y)
    
    # y z only
    elif x==None and y!=None and z!=None:
        common_countries = reduce(np.intersect1d,(dfy['country'].values, dfz['country'].values))        
        dfy = dfy[dfy['country'].isin(common_countries)]
        dfz = dfz[dfz['country'].isin(common_countries)]
        dfa = pd.merge(dfy,dfz[['country',z]],on='country', how='left')
        #print("yz")
        
        #custom logic for log z as it is not available in px function
        if zlog == True:
            #get the log of the list, and then normalise it to 0 and above by adding the absolute value of the min to every element
            size = np.log10(dfa[z].astype(float))+abs(min(np.log10(dfa[z].astype(float))))
        else:
            size = dfa[z]
        
        fig = px.scatter(dfa,
                     #x=x,
                     y=y,
                     size=size,
                     labels={z: seriesZ_label, y: seriesY_label, 'continent':'Continent' },
                     color="continent",
                     hover_name="country",
                     log_x=xlog,
                     log_y=ylog,
                     size_max=60)
        #fig.update_layout(yaxis_title=y)
        
    # z only    
    elif x==None and y==None and z!=None:
        dfa = dfz
        #print("z")
        
        #custom logic for log z as it is not available in px function
        if zlog == True:
            #get the log of the list, and then normalise it to 0 and above by adding the absolute value of the min to every element
            size = np.log10(dfa[z].astype(float))+abs(min(np.log10(dfa[z].astype(float))))
        else:
            size = dfa[z]
        
        fig = px.scatter(dfa,
                     #x=x,
                     #y=y,
                     size=size,
                     labels={z: seriesZ_label, 'continent':'Continent'},
                     color="continent",
                     hover_name="country",
                     log_x=xlog,
                     size_max=60)    
    
    # x y z
    else:
    
        #find the unique list of countries that are present in all 3 datasets
        common_countries = reduce(np.intersect1d,(dfx['country'].values,dfy['country'].values, dfz['country'].values))
        
        #strip out non common countries from the 3 datasets before merging
        dfx = dfx[dfx['country'].isin(common_countries)]
        dfy = dfy[dfy['country'].isin(common_countries)]
        dfz = dfz[dfz['country'].isin(common_countries)]
        
        #merge the dataframes on country    
        dfa = pd.merge(dfx,dfy[['country',y]],on='country', how='left')
        dfa = pd.merge(dfa,dfz[['country',z]],on='country', how='left')
        
        #print("xyz")
        
        #custom logic for log z as it is not available in px function
        if zlog == True:
            #get the log of the list, and then normalise it to 0 and above by adding the absolute value of the min to every element
            size = np.log10(dfa[z].astype(float))+abs(min(np.log10(dfa[z].astype(float))))
        else:
            size = dfa[z]
        
        #leave animation alone for now
        fig = px.scatter(dfa,
                         x=x,
                         y=y,
                         size=size,
                         #size=np.log10(z.astype(float)), #
                         labels={x: seriesX_label, y: seriesY_label, z: seriesZ_label, 'continent':'Continent'},
                         color="continent",
                         hover_name="country",
                         log_x=xlog,
                         log_y=ylog,
                         size_max=60,
                         #animation_frame="year",
                         #animation_group="country"
                         )
        #fig.update_layout(xaxis_title=x, yaxis_title=y)    
        
        '''
        #Could try this from plotly
        # Create figure
        fig = go.Figure()
        
        for continent_name, continent in continent_data.items():
            fig.add_trace(go.Scatter(
                x=continent['gdpPercap'], y=continent['lifeExp'],
                name=continent_name, text=continent['text'],
                marker_size=continent['size'],
                ))
        
        # Tune marker appearance and layout
        fig.update_traces(mode='markers', marker=dict(sizemode='area',
                                                      sizeref=sizeref, line_width=2))
        
        fig.update_layout(
            title='Life Expectancy v. Per Capita GDP, 2007',
            xaxis=dict(
                title='GDP per capita (2000 dollars)',
                gridcolor='white',
                type='log',
                gridwidth=2,
            ),
            yaxis=dict(
                title='Life Expectancy (years)',
                gridcolor='white',
                gridwidth=2,
            ),
            paper_bgcolor='rgb(243, 243, 243)',
            plot_bgcolor='rgb(243, 243, 243)',
        )
        '''
    #go.restyle(fig)
    return fig


def create_chart_sunburst(series, color, year, colorbar_sb):
    #Need to make robust based on data type, continuous vs discrete, etc.
    #probably need to go to graph object to tweak the colorscale    
    #might not need the store year
    
    logger.info("create_sunburst()\nseries is %r\ncolor is %r\nyear is %r\ncolorbar is %r", series, color,year, colorbar_sb)  
    
    x = series
    y = color
    #year = '2005' 
    
    #return from function if no datasets
    if (x == None and y == None) or year == None or year == '':
        #return blank scatter
        fig = px.scatter()
        return fig
    
    
    #Build 2 dataframes as precursor to chart data
    if x != None:
        dfx = pop[(pop['dataset_raw']==x) & (pop['year']==int(year))].rename(columns={"value":x})        #memory leak?
        dfx[x] = dfx[x].astype(float)
        seriesX_label = master_config[x].get("dataset_label") 
        
        #Need to revert the categoricals for this to work. TODO
        dfx['continent'] = dfx['continent'].astype(str)              
        dfx['country'] = dfx['country'].astype(str)
    
    if y != None:
        dfy = pop[(pop['dataset_raw']==y) & (pop['year']==int(year))].rename(columns={"value":y})             #memory leak?
        dfy[y] = dfy[y].astype(float)
        seriesY_label = master_config[y].get("dataset_label") 
        
        #Need to revert the categoricals for this to work. TODO
        dfy['continent'] = dfy['continent'].astype(str)
        dfy['country'] = dfy['country'].astype(str)
    
    # x only
    if x!=None and y==None:
        dfa = dfx
        print("x")
        logger.info("Sunburst chart data. Length %r, Cols %r",len(dfa), dfa.columns)
        fig = px.sunburst(
                      dfa,
                      path=['continent', 'country'], values=x,
                      #color=np.log10(dfa[x].astype(float)), #logarithmic scale for pizza
                      hover_data=['country'], 
                      color_continuous_scale=colorbar_sb,    #'inferno_r', #"_r" reverses colour scale                  
                      ) 
    
    # x and y
    if x!=None and y!=None:
        
        #interesect on country name (and year)
        common_countries = reduce(np.intersect1d,(dfx['country'].values,dfy['country'].values))
        #logger.info("common countries %r",common_countries)
        dfx = dfx[dfx['country'].isin(common_countries)]
        dfy = dfy[dfy['country'].isin(common_countries)]
        dfa = pd.merge(dfx,dfy[['country',y]],on='country', how='left')
        
        print("xy")        
        #logger.info("Sunburst chart data. Length %r, Cols %r",len(dfa), dfa.columns)        
        
        if len(dfa) > 0:
        
            fig = px.sunburst(
                          dfa,
                          path=['continent', 'country'],
                          values=x,
                          color=y,                          
                          labels={x: seriesX_label, x: seriesY_label,  'continent':'Continent'},                          
                          hover_name="country",
                          hover_data=['country'], 
                          
                          color_continuous_scale=colorbar_sb,    #'inferno_r', #"_r" reverses colour scale                  
                          ) 
        
        #no data
        else:
            return px.sunburst()
    
    
    fig.update_traces( 
            opacity=0.7,
        )
   
 
    
    return fig

def create_chart_geobar(series, year, colorscale, gj, jellybean):
    
    # subset master dataset     
    df = pop[(pop["year"] == int(year)) & (pop["dataset_raw"] == series)].copy() #memory leak ?
    
    #cast value to float
    df['value'] = df['value'].astype(float)               
    
    #fix for removing note and source columns
    df['fix1'] = "dummmy"
    df['fix2'] = "dummy"
    
    #add random colours (note moving these will fuck up column indexing that is hardcoded in subsequent statements)
    df['r'] = np.random.randint(0, 255, df.shape[0]).astype(str)
    df['g'] = np.random.randint(0, 255, df.shape[0]).astype(str)
    df['b'] = np.random.randint(0, 255, df.shape[0]).astype(str)        
    df['rgb'] = '[' + df['r'].map(str) + ',' + df['g'].map(str) + ',' + df['b'].map(str) + ']' #hoped to use this but as it turns out I need individual R/G/B vals 
    
    #now try to do proper colour interpolation
    
    #Linear               
    
    #ratio should be a proportion of the max value in the list                      
    df['f-linear'] = df['value'] / np.max(df["value"]) #i.e. what proportion is it of the max        
    #print("fraction linear", df['f-linear'])#should be between 0-1
    
    #Logarithmic
    
    #drop values below zero (they cannot be displayed on current choropleth style)
    df = df[df.value > 0]  
    
    #transform the data values to log10 (zeros introduced where log not computed)
    df['value_log10'] = np.log10(df['value'], out=np.zeros_like(df['value']), where=(df['value']!=0))        
    
    #now drop any rows with zero vals (or it will be affected by subsequent colour interpolation logic)
    df = df[df.value_log10 != 0]       
    
    #translate data range to positive
    mn = np.min(df["value_log10"])
    mx = np.max(df["value_log10"])
    if mn < 0.0:            
        print("Color correction, translating log vals")
        df['value_log10'] = df['value_log10'] + abs(mn)
    
    #now calculate the 0-1 ratio (normalise)
    df['f-log'] = df['value_log10'] / np.max(df["value_log10"]) #i.e. what proportion is it of the max             
    
    if colorscale[0][1][0] != "#":
        #i.e. we have an RGB color array (happens after settings are changed), so convert to hex
        print("RGB color array found in map data. Converting to hex")
        for i in range(0,len(colorscale)):              
            red = d.extractRed(colorscale[i][1])
            green = d.extractGreen(colorscale[i][1])
            blue = d.extractBlue(colorscale[i][1])
            hx = '#{:02x}{:02x}{:02x}'.format(red, green , blue)
            #print(red, green, blue, hx)
            colorscale[i][1] = hx #replace rgb string with hex string   
    
    #based on the value for each row, obtain the two colours and mixing to interpolate between them!
    df['c1'] = df.apply(lambda row : d.extractColorPositions(colorscale, row['f-log'])[0], axis =1).astype(str)
    df['c2'] = df.apply(lambda row : d.extractColorPositions(colorscale, row['f-log'])[1], axis =1).astype(str)
    df['mix'] = df.apply(lambda row : d.extractColorPositions(colorscale, row['f-log'])[2], axis =1).astype(float)
    
    #get hex val by linear interpolation between c1, c2, mix for each row, and also convert this into the component RGB vals (for deck.gl)
    df['hex'] = df.apply(lambda row : d.colorFader(row['c1'], row['c2'], row['mix']), axis =1) #linear interpolation between two hex colours
    
    #leave colours random (previously set) if jellybean is true
    if jellybean == False:
        df['r'] = df.apply(lambda row : ImageColor.getcolor(row['hex'], "RGB")[0], axis =1).astype(str) #return the red (index 0 of tuple) from the RGB tuble returned by getcolor 
        df['g'] = df.apply(lambda row : ImageColor.getcolor(row['hex'], "RGB")[1], axis =1).astype(str) #return the greeen (index 0 of tuple) from the RGB tuble returned by getcolor 
        df['b'] = df.apply(lambda row : ImageColor.getcolor(row['hex'], "RGB")[2], axis =1).astype(str) #return the blue (index 0 of tuple) from the RGB tuble returned by getcolor 
    
    # setup normalisation bins to tame the height of the polygons (target a max of 5000000, it's a map quirk in deck.gl)        
    mx = np.max(df["value"])
    norm = 1 #default normalisation multiplier
    if mx < 10:
        norm = 500000
    elif mx < 100:
        norm = 50000
    elif mx < 1000:
        norm = 10000
    elif mx < 10000:
        norm = 1000 #drop to 500?
    elif mx < 100000:
        norm = 50
    elif mx < 1000000:
        norm = 10 #testing
    elif mx < 10000000:
        norm = 1
    elif mx < 100000000:
        norm = 0.1
        
    #setup elevation string (parameter for deck function below)        
    elevation = "value * {:f}".format(norm) #note just using the ECONOMY feature.property as a spare from the json.        
    
    #logger.info("TESTING: Max: %r, Norm: %r, elevation: %r",mx,norm,elevation)   
    
    #remove antarctica from JSON
    for i in range(0, len(gj['features'])):
        try:
            if gj['features'][i]['properties']['UN_A3'] == '010':
                print("removing antactica from json!")
                del gj['features'][i]
        except IndexError as error:
            print("Area51: Exception thrown trying to remove antactica")
    
    #loop through all geojson features and set the colour value from the df for each
    for i in range(0, len(gj['features'])):
        try:                               
            
            #At this point, check if country name/val None (i.e. no data in DF), and grab the country name for the properties of the JSON, and set the value to 0
            
            #if no data exists for a country in this series, store the country name from json, set val to 0, and set a nice grey colour so it displays on jigsaw
            if gj['features'][i]['properties']['UN_A3'] not in df["m49_un_a3"].values:
                #print(gj['features'][i]['properties']['BRK_NAME'])
                gj['features'][i]['country'] = gj['features'][i]['properties']['BRK_NAME'] #grab country name from json              
                gj['features'][i]['value'] = "no data"                    
                gj['features'][i]['properties']['MAPCOLOR7'] = "224" #grey
                gj['features'][i]['properties']['MAPCOLOR8'] = "224"
                gj['features'][i]['properties']['MAPCOLOR9'] = "224"
                
            else:             
                #set country name and value (for tooltip, at feature level) and and add the colours from the df
                gj['features'][i]['country'] = df[df["m49_un_a3"]==gj['features'][i]['properties']['UN_A3']].iloc[0,1] #country name                
                gj['features'][i]['value'] = df[df["m49_un_a3"]==gj['features'][i]['properties']['UN_A3']].iloc[0,4] #value                      
                gj['features'][i]['properties']['MAPCOLOR7'] = df[df["m49_un_a3"]==gj['features'][i]['properties']['UN_A3']].iloc[0,10] #Red
                gj['features'][i]['properties']['MAPCOLOR8'] = df[df["m49_un_a3"]==gj['features'][i]['properties']['UN_A3']].iloc[0,11] #Green
                gj['features'][i]['properties']['MAPCOLOR9'] = df[df["m49_un_a3"]==gj['features'][i]['properties']['UN_A3']].iloc[0,12] #Blue   
        
        except IndexError as error:
            print("Area51: Exception thrown attempting to build custom dict from json (expected)")
    
    mapbox_api_token = os.getenv("MAPBOX_ACCESS_TOKEN")      
            
    LAND_COVER = [
        [[-123.0, 49.196], [-123.0, 49.324], [-123.306, 49.324], [-123.306, 49.196]]
    ]
    
    INITIAL_VIEW_STATE = pydeck.ViewState(
        latitude=30.44, longitude=27.60, zoom=1.3, max_zoom=10, pitch=45, bearing=0
    )  
    
    polygon = pydeck.Layer(
        "PolygonLayer", #not sure what this does
        LAND_COVER,
        stroked=False,           
        get_polygon="-",
        get_fill_color=[180, 0, 200, 140], #doesn't seem to do shit
    )                
    
    geojson = pydeck.Layer(
        "GeoJsonLayer", 
        gj, #specially prepared geojson coordinate feature collection with custom data input from df            
        opacity=0.8,
        stroked=False,
        filled=True,
        extruded=True,
        wireframe=True,
        pickable=True,
        auto_highlight=True,            
        get_elevation=elevation,
        #elevation_range=[0, 1], #could be useful to normalise elevation. Not tested.
        get_fill_color="[properties.MAPCOLOR7*1,properties.MAPCOLOR8*1,properties.MAPCOLOR9*1]", #Note this is super particular. The string must be parsed by deck-gl. Basically MUST have val * number for each RGB integer or it won't work            
        get_line_color=[255, 255, 255], #white (invisible)
    )
    
    r = pydeck.Deck(
        #views=[pydeck.View(width=1500, height=750)],
        layers=[polygon, geojson],
        initial_view_state=INITIAL_VIEW_STATE,
        mapbox_key=mapbox_api_token, #it's kind of cool without one. Jigsaw view!
    )
    
    geobar = dash_deck.DeckGL(r.to_json(),
                              id="deck-gl",
                              mapboxKey=r.mapbox_key,
                              #style={"background-color": '#b0dff7'},
                              #tooltip=True,
                              tooltip={"text": "{country} {value}"},                                 
                              )
    return geobar

def create_chart_globe(gj_land, gj_ocean):
                
    #GLOBE VIEW
    mapbox_api_token = os.getenv("MAPBOX_ACCESS_TOKEN") #So far seems to be working without a token
          
    layers = [
        
        
        pydeck.Layer(
            "GeoJsonLayer",
            id="base-map",
            data=gj_ocean, #OCEAN JSON
            stroked=False,
            filled=True, 
            pickable=False, #Key difference in this layer as I don't want tooltips when hovering over the ocean
            auto_highlight=True,
            get_line_color=[60, 60, 60],
            #get_fill_color=[160, 160, 160],
            get_fill_color="[properties.red*1,properties.green*1,properties.blue*1]",
            opacity=0.5,
            #extruded=True,
            #wireframe=True,                           
            #get_elevation="red * 10000",
        ),
        
        pydeck.Layer(
            "GeoJsonLayer",
            id="base-map",
            data=gj_land, #LAND JSON
            stroked=False,
            filled=True, 
            pickable=True,
            auto_highlight=True,
            get_line_color=[60, 60, 60],
            #get_fill_color=[160, 160, 160],
            get_fill_color="[properties.red*1,properties.green*1,properties.blue*1]",
            opacity=0.5,
            #extruded=True,
            #wireframe=True,                           
            #get_elevation="red * 10000",
        ),    
        
    ]
    
    r = pydeck.Deck(
        views=[pydeck.View(type="_GlobeView", controller=True)], # , width=1500, height=750
        initial_view_state=pydeck.ViewState(latitude=51.47, longitude=0.45, zoom=0.85),
        layers=layers,                  
        parameters={"cull": True}, # Note that this must be set for the globe to be opaque
    ) 
    
    globe = dash_deck.DeckGL(
        json.loads(r.to_json()),
        id="deck-gl",
        style={"background-color": "white"},
        #tooltip=True,
        tooltip={"text": "{COUNTRY} {value}"}, #these are cols from the dataframe (case senstivite due to json bullshit)
        mapboxKey=mapbox_api_token, #no key at mo
    ),
      

    return globe



def create_chart_globe_powerstations_xp1():
    # This is dirty. But it works.    
    
    LAND = geojson_globe_land_ne50m
    OCEANS = geojson_globe_ocean_ne50m 
    
    df = EXP_POWER_PLANTS

    def color_by_fuel(fuel_type):
        if fuel_type.lower() in "nuclear": return [10, 230, 120] #green
        elif fuel_type.lower() in ("wave and tidal", "hydro"): return [13, 23, 130] #dark blue
        elif fuel_type.lower() in "wind": return [106, 21, 176] #windy purple           
        elif fuel_type.lower() in ("biomass", "waste"): return [10, 230, 120] #purple
        elif fuel_type.lower() in "solar": return [250, 242, 2] #yellow
        elif fuel_type.lower() in "geothermal": return [156, 94, 19] #brown
        elif fuel_type.lower() in ("coal", "oil", "petcoke"): return [43, 42, 43] #black
        else: return [60,60,60]         

    df["color"] = df["primary_fuel"].apply(color_by_fuel)

    view_state = pydeck.ViewState(latitude=51.47, longitude=0.45, zoom=1.30)   
    view = pydeck.View(type="_GlobeView", controller=True, width='100%', height='100%')

    layers = [
                    
        pydeck.Layer(
            "GeoJsonLayer",
            id="base-map-ocean",
            data=OCEANS,
            stroked=False,
            filled=True, 
            pickable=False, #Key difference in this layer as I don't want tooltips when hovering over the ocean
            auto_highlight=True,
            get_line_color=[60, 60, 60],
            get_fill_color=[134, 181, 209],                
            opacity=0.5,                
        ),

        pydeck.Layer(
            "GeoJsonLayer",
            id="base-map",
            data=LAND,
            stroked=False,
            filled=True,
            get_line_color=[60, 60, 60],
            get_fill_color=[160, 160, 160],
            opacity=1,
        ),

        pydeck.Layer(
            "ColumnLayer",
            id="power-plant",
            data=df,
            get_elevation="capacity_mw",
            get_position=["longitude", "latitude"],
            elevation_scale=150,
            pickable=True,
            auto_highlight=True,
            radius=10000,
            get_fill_color="color",
        ),
    ]

    r = pydeck.Deck(
        views=[view],
        initial_view_state=view_state,
        layers=layers,            
        parameters={"cull": True},
    )

    fig = html.Div(
        dash_deck.DeckGL(
            json.loads(r.to_json()),
            id="deck-gl",                
            tooltip={"text": "{name}, {primary_fuel} plant, {capacity_mw}MW, {country_long}"},
        )
    )
    
    return fig



#@cache.memoize(timeout=CACHE_TIMEOUT)
def create_map_geomap_empty():
    #No method overloading in python, so have an empty map load for initial.
    logger.info("Creating geomap empty...")
    
    fig = go.Figure(
        go.Choroplethmapbox(        
        )
    )
    
    #zoom 1.6637151294876888 and centre {'lon': 27.607108241243623, 'lat': 3.4455217746834705}
    fig.update_layout(
        mapbox_style=mapbox_style[1], #default
        mapbox_zoom=INIT_ZOOM,
        mapbox_center={"lat": INIT_LATITUDE, "lon": INIT_LONGITUDE},   
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
    )
    return fig
    

#@cache.memoize(timeout=CACHE_TIMEOUT)
def create_map_geomap(df, geojson, series, zoom, center, selected_map_location, mapstyle, colorbarstyle, colorpalette_reverse):      
        
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

def create_dash_layout(app):

    #CONSTRUCT DASH LAYOUT
    
    # Header
    header = create_dash_layout_header()
    
    # Navigation menu    
    navbar = create_dash_layout_navbar()    
    
    # Body (i.e. the map centrepiece, with loaders to overlay ontop)
    body = create_dash_layout_body()     
       
    # Build low navigation menu                      
    nav_footer = create_dash_layout_nav_footer()    
    
    # dcc stores for settings
    dcc_stores = create_dash_layout_dcc_stores()        
        
    #hidden div triggers (for chaining callbacks)
    hidden_div_triggers = create_dash_hidden_div_triggers()
    
    #enable special clientside callbacks
    js_callback_clientside_blur(app)
    js_callback_clientside_share(app)
    js_callback_clientside_viewport(app) 

    # enable pathname API queries
    api = dcc.Location(id='url', refresh=False) 
    
    # Assemble dash layout 
    app.layout = html.Div([navbar, header, body, nav_footer, dcc_stores, hidden_div_triggers, api])    
    
    return app


def js_callback_clientside_blur(dash_app):

        #Special client side callback that removes unwanted focus on buttons that trigger modals (for hiding tooltip) using embedded javascript function
        dash_app.clientside_callback(
            """
            function() {
                //alert("Blur function trigger");
                //document.getElementById("some-other-component").focus();
                document.getElementById("about-button").blur();
                document.getElementById("uguide-button").blur();
                document.getElementById("settings-button").blur();
                document.getElementById("download-button").blur();
                document.getElementById("bar-button").blur();
                document.getElementById("line-button").blur();
                document.getElementById("sunburst-button").blur();
                document.getElementById("globe-button").blur();
                document.getElementById("geobar-button").blur();
                document.getElementById("bubble-button").blur();
                //document.getElementById("button-userguide-about").blur();
                //document.getElementById("download-popover").blur();
                return {};
            }
            """,
            Output('blur-hidden-div', 'style'),
            Input('about-button', 'n_clicks'),
            Input("uguide-button", 'n_clicks'),
            Input("settings-button", 'n_clicks'),
            Input("download-button", 'n_clicks'),
            Input("bar-button", 'n_clicks'),
            Input("line-button", 'n_clicks'),
            Input('sunburst-button', 'n_clicks'),
            Input("globe-button", 'n_clicks'),
            Input("geobar-button", 'n_clicks'),
            Input("bubble-button", 'n_clicks'),
            #Input("button-userguide-about", 'n_clicks'),
            #Input("btn-popover-map-download-land", 'n_clicks'),
            prevent_initial_call=True
        )
        return 


def js_callback_clientside_share(dash_app):

        # This javascript client side callback updates the overhead doc title, which is used by the shareon icons at the bottom of the screen.
        dash_app.clientside_callback(        
                    
            """
            function(path,label) {
                //alert(label);
                document.title = 'WORLD ATLAS 2.0 - ' + label;
                shareon();            
            }
            """,
            Output('js-social-share-dummy', 'children'),        
            Input('js-social-share-refresh', 'children'),
            State("my-series-label","data"), 
            prevent_initial_call=True
        )
        return


def js_callback_clientside_viewport(dash_app):
    # Detect viewport of client
    dash_app.clientside_callback(        
                
        """
        function() {
            //alert("Screen size: "+ screen.width +"x"+ screen.height + " pixels." + "Available screen size: "+ screen.availWidth +"x"+ screen.availHeight );
        
            return {
                'width': screen.width,
                'height': screen.height                 
            }                       
        }
        """,
        Output('js-detected-viewport', 'data'),               
        Input('js-detected-viewport-dummy', 'children'),        
        prevent_initial_call=False
    )
    return


def create_dash_layout_dcc_stores():
    
    dcc_stores = html.Div([
        dcc.Store(id='my-settings_json_store', storage_type='memory'),
        dcc.Store(id='my-settings_mapstyle_store', storage_type='memory'),
        dcc.Store(id='my-settings_colorbar_store', storage_type='memory'),
        dcc.Store(id='my-settings_colorbar_reverse_store', storage_type='memory'),  
        dcc.Store(id='my-series', storage_type='memory'),
        dcc.Store(id='my-series-label', storage_type='memory'),
        dcc.Store(id='my-year', storage_type='memory'),        
        dcc.Store(id='my-selection-m49', storage_type='memory'), #unused, for selecting region of geomap I think        
        dcc.Store(id='my-series-bar', storage_type='memory'),
        dcc.Store(id='my-year-bar', storage_type='memory'),
        dcc.Store(id='my-series-line', storage_type='memory'),        
        dcc.Store(id='my-xseries-bubble', storage_type='memory'),
        dcc.Store(id='my-yseries-bubble', storage_type='memory'),
        dcc.Store(id='my-zseries-bubble', storage_type='memory'),
        dcc.Store(id='my-year-bubble', storage_type='memory'),        
        dcc.Store(id='my-pizza-sunburst', storage_type='memory'),
        dcc.Store(id='my-toppings-sunburst', storage_type='memory'),
        dcc.Store(id='my-year-sunburst', storage_type='memory'),        
        dcc.Store(id="my-url-main-callback", storage_type='memory'),  #stores href data    
        dcc.Store(id="my-url-bar-callback", storage_type='memory'),
        dcc.Store(id="my-url-line-callback", storage_type='memory'),       
        dcc.Store(id="my-url-globe-callback", storage_type='memory'),
        dcc.Store(id="my-url-jigsaw-callback", storage_type='memory'),
        dcc.Store(id="my-url-root", storage_type='memory'),
        dcc.Store(id="my-url-path", storage_type='memory'),
        dcc.Store(id="my-url-series", storage_type='memory'),
        dcc.Store(id="my-url-year", storage_type='memory'),
        dcc.Store(id="my-url-view", storage_type='memory'),
        dcc.Store(id="my-url-map-trigger", storage_type='memory'),
        dcc.Store(id="my-url-bar-trigger", storage_type='memory'),
        dcc.Store(id="my-url-line-trigger", storage_type='memory'),
        dcc.Store(id="my-url-globe-trigger", storage_type='memory'),
        dcc.Store(id="my-url-jigsaw-trigger", storage_type='memory'),
        dcc.Store(id="js-detected-viewport", storage_type='memory'),
        dcc.Store(id="my-experimental-trigger", storage_type='memory'),

        ]) 
    return dcc_stores


def create_dash_hidden_div_triggers():
    triggers = html.Div([
        html.Div("Test div", id="timeslider-hidden-div", style={"display":"none"}), #CRITICAL. Hidden div for triggering main callback from secondary time-slider callback.
        html.Div("Test div", id="settings-hidden-div", style={"display":"none"}), #CRITICAL. Hidden div for triggering main callback from settings modal updates
        html.Div("Test div", id="blur-hidden-div", style={"display":"none"}),
        html.Div("Test div", id="blur-hidden-div-menu", style={"display":"none"}),
        html.Div("Test div", id="js-social-share-refresh", style={"display":"none"}),
        html.Div("Test div", id="js-social-share-dummy", style={"display":"none"}),        
        html.Div("Test div", id="js-detected-viewport-dummy", style={"display":"none"}),

        ],style={"display":"none"})
    return triggers


def create_dash_layout_header():
            
    #title of app in page
    title = html.Div([
        html.Span(INIT_TITLE_TEXT, style={"marginBottom": 0,
                                        #"marginTop": INIT_TITLE_PAD_TOP,
                                        #"marginLeft": 0,
                                        #'textAlign': 'center',
                                        'fontWeight': 'bold',
                                        'fontFamily': INIT_TITLE_FONT,
                                        'fontSize': INIT_TITLE_H,
                                        'height': INIT_TITLE_DIV_H,
                                        'color':INIT_TITLE_COL,
                                        'backgroundColor': INIT_TITLE_BG_COL,
                                        'opacity': INIT_TITLE_OPACITY}, 
        ),  
        ], style={"marginBottom": 0,
                                        "marginTop": INIT_TITLE_PAD_TOP,
                                        "marginLeft": 0,
                                        'textAlign': 'center',                                        
                                        'height': INIT_TITLE_DIV_H }, 
        )
   
    
    loader_main = html.Div(
                dcc.Loading(
                type=INIT_LOADER_TYPE,
                color=INIT_LOADER_DATASET_COLOR, #hex colour close match to nav bar ##515A5A
                children=html.Span("No data selected", id="my-loader-main", style={"marginBottom": 0, "marginTop": 10, "marginLeft": 0, 'textAlign': 'center', 'fontSize': INIT_SELECTION_H, 'fontFamily': 'Helvetica', 'fontWeight': '', 'backgroundColor': INIT_TITLE_BG_COL, 'opacity': INIT_TITLE_OPACITY  },), #style of span
                style={'textAlign': 'center' } #style of loader
                ),style={'textAlign': 'center', 'marginTop':10, 'marginBottom':10, 'color': INIT_TITLE_COL}, #style of div
    )
  
            
    #dataset selection
    #selection = html.Div(
    #        [  
    #            html.Span("No data selected", id="my-series",style={"display":"none"}), #this is essentially being used as a DCC store
    #            html.Span("No data selected", id='my-series-label'),
    #            html.Span(id="dataset-status-comma"), #for adding a comma between dataset and year
    #            html.Span(id="my-year"),     
    #        ], 
    #        style={"marginBottom": 10, "marginTop": 10, "marginLeft": 0, 'textAlign': 'center', 'fontSize': INIT_SELECTION_H, 'fontFamily': 'Helvetica', 'fontWeight': '',   },
    #        #id = 'my
    #        ) #'fontWeight': 'bold' #'color': '#d6b980' 
        
        
    #wrap the title, loader and selection up in a container called header
    header = dbc.Container([
        dbc.Row([
            dbc.Col([title, loader_main]),        
            ])            
        ],
        style={"marginBottom": 0,
               "marginTop": 0,
               "marginLeft": 0,
               "marginRight": 0,
               #"margin-left": "auto",
               #"margin-right": "auto",               
               #'backgroundColor':'white',
               "max-width": "none",
               "width": "100vw",
               "position": "absolute",
               "z-index": "2",
               #"top": "0vh",
               #"left": "5vw",
               }) 
            
    
    return header


def create_dash_layout_navbar():
    
    #construct the navbar by calling a function that recursively builds out components based on dataset_lkup
    navbar = html.Div([
        
        dbc.Row(
                children=create_dash_layout_navbar_menu(),      
                style={'margin-left': '1vw', 'margin-right': '1vw', 'display': 'flex', 'vertical-align': 'top' , 'align-items': 'center', 'justify-content': 'center'  }, 
                className="ml-auto"), #Format the row. This ensurs spill over buttons are also centre aligned
        
        dbc.Tooltip(
                "Randomly select a dataset!",
                target='random-button',
                placement='bottom',                
                ),
        ], 
               
        style={"height": INIT_NAVBAR_H,
               "width": INIT_NAVBAR_W,
               "zIndex":2,
               "backgroundColor": '#3E3F3A',
               'display': 'flex',
               'vertical-align': 'top',
               'align-items': 'center',
               'justify-content': 'center',               
               "marginBottom": 0,
               "marginTop": 0,
               "marginLeft": 0,
               "marginRight": 0,
               #"margin-left": "auto",
               #"margin-right": "auto",               
               #'backgroundColor':'white',               
               #"position": "absolute",
               #"z-index": "2",
               #"top": INIT_NAVBAR_POSITION, 
               #"left": "5vw",
               
               
               }, #format the navbar (div)
        
    ) #end div (navbar)    
    return navbar

def create_dash_layout_navbar_items(nav_cat):
    
    #build dropdown menu items for all instances of the nav_cat from master config
    #This is pretty inefficient but the logic is super hard, so I haven't wanted to fuck with it
    #dataframes are built from the robust dictionary in master config, and so changes to master config csv should not be breaking
        
    #blank list for returning
    items = []       
    
    # build df from master config using all datasets ids
    config_list = []
    for key in master_config_key_datasetid:
        config_list.append(master_config_key_datasetid[key]) #should be whole dict
    
    # convert list to df
    df_test= pd.DataFrame(config_list)
    
    # subset and reorganise cols to match structure needed for this patch 0 dataset id 1 dataset raw 2 dataset label
    df_test = df_test[['dataset_id', 'dataset_raw', 'dataset_label', 'nav_cat', 'nav_cat_nest']]
    
    # cast dataset id col to string (needed for callback creation)
    df_test['dataset_id'] = df_test['dataset_id'].astype(str)        
    
    # subset dataframe
    df = df_test[df_test['nav_cat']==nav_cat]
            
    #extract list of unique nesting cats
    nests = pd.unique(df['nav_cat_nest'])
    
    logger.info("Creating %r nav items for category: %r",len(df), nav_cat)  
    
    # case all root nesting, simply add items
    if len(nests) == 1 and nests[0] == 'root':
        #print("all roots baby")    
    
        #for each occurance in the category, add a dropdownmenu item and id based (ultimately) on master config
        for i in range(0,len(df)):    
                items.append(
                    dbc.DropdownMenuItem(
                        children=df.iloc[i][2], #dataset_label
                        id=df.iloc[i][0], #dataset_id        
                        #style={'marginTop':0, 'marginBottom':0},
                        ))
                
    # add nesting
    else:
        #print("not all roots")        
        
        #loop through categories and nest if needed
        for i in range(0,len(nests)):            
            if nests[i] == 'root':
                #subsample this nav_cat just to root items and add items menu
                r = df[df['nav_cat_nest']=='root'] 
                for j in range(0,len(r)):    
                    items.append(
                        dbc.DropdownMenuItem(
                            children=r.iloc[j][2], #dataset_label
                            id=r.iloc[j][0] #dataset_id        
                            ))
               
            #for anything not root, add nests
            else:
                #for each unique nest in this category, add a new submenu and populate
                items.append(
                    dbc.DropdownMenu(
                        label=nests[i],
                        direction='left',
                        toggle_style={'color':'grey', 'backgroundColor':'white', 'border': '0px', 'fontSize': INIT_NAVBAR_FONT_H, "marginBottom": 0, "marginTop": 0, "marginLeft": INIT_DROPDOWNITEM_LPAD, "marginRight": INIT_DROPDOWNITEM_RPAD,}, 
                        children=create_dash_layout_navbar_items_nests(nests[i], df),  
                    )
                )          
    
    return items


def create_dash_layout_navbar_items_nests(nest, df):
    #df is just for one particular nav_cat. Loop through and add any items to list
    items = []
    r = df[df['nav_cat_nest']==nest] 
    for j in range(0,len(r)):    
        items.append(
            dbc.DropdownMenuItem(                
                children=r.iloc[j][2], #dataset_label
                id=r.iloc[j][0] #dataset_id        
                ))    
    
    return items


def create_dash_layout_navbar_menu():    
    
    #construct the entire navbar menu recursively based on master config. Can return a list of dropdown menus, each with children (items) built recursively aswell
    logger.info("Building nav menu...")
    
    #define empty list
    menu_list=[]
    
    #Use dict of nav_cats to build the nav menu
    
    nav_cats = master_config_key_nav_cat 
    
    logger.info("Adding %r dataset categories...", len(nav_cats))
    
    #loop through unique nav_cats    
    for i in nav_cats:    
        logger.info("adding %r",nav_cats[i].get("nav_cat"))
        
        #logic for hiding unused categories
        if nav_cats[i].get("nav_cat") == "unused":
            display="none"
        else:
            display="block"        
        
        #extract colour for menuitem                    
        colour = nav_cats[i].get("colour")
        
        #add items to this menu list
        menu_list.append(
            dbc.DropdownMenu(
                children=create_dash_layout_navbar_items(nav_cats[i].get("nav_cat")),                
                bs_size="sm",
                label=nav_cats[i].get("nav_cat"), 
                toggle_style={"display":display, "color": colour, 'backgroundColor':'#3E3F3A', 'border': '0px', 'fontSize': INIT_NAVBAR_FONT_H, "marginBottom": 0, "marginTop": 0, "marginLeft": INIT_DROPDOWNITEM_LPAD, "marginRight": INIT_DROPDOWNITEM_RPAD,},               
            ))
            
    
        
        
    menu_list.append(dbc.Button(INIT_RANDOM_BTN_TEXT,  outline=INIT_BTN_OUTLINE, color="danger", id="random-button", style={'display': 'inline-block', 'opacity':INIT_BUTTON_OPACITY, 'fontSize': INIT_RANDOM_BTN_FONT, "marginBottom": 0, "marginTop": 0, "marginLeft": INIT_DROPDOWNITEM_LPAD, "marginRight": INIT_DROPDOWNITEM_RPAD,}, size=INIT_BUTTON_SIZE),)
    
    # add search DCC dropdown to list
    
    # get list of all datasets in config (list of dicts)
    dd_list = d.get_list_of_dataset_labels_and_raw(master_config,"all")
    
    # sort list by dataset raw by converting to df and back
    dd_list = pd.DataFrame(dd_list).sort_values(by="dataset_label").to_dict('records') 
    
    # construct drop down list
    search_menu_list = []
    for i in range(0,len(dd_list)):        
        search_menu_list.append({'label': dd_list[i].get("dataset_label"), 'value': dd_list[i].get("dataset_raw")})
    
    menu_list.append(
        dcc.Dropdown(
                options=search_menu_list,
                id="nav-search-menu",
                multi=False,
                placeholder=f'Search {DATASETS:>3,} datasets and {OBSERVATIONS:>3,} data points',
                clearable=True,
                style={'width':INIT_NAVBAR_SEARCH_WIDTH, "fontSize": INIT_NAVBAR_SEARCH_FONT},
                #className='ml-auto',
                
            ),
        ),
    
    
   
    return menu_list


def create_dash_layout_body():
    
    body = html.Div(
        children=[
            
            # loader for geobar
            dcc.Loading(
                #id="my-loader-geobar",
                type=INIT_LOADER_TYPE,
                color=INIT_LOADER_CHART_COLOR, #hex colour close match to nav bar ##515A5A
                children=html.Span(id="my-loader-geobar"),
                style={"zIndex":1, 'display': 'flex', 'vertical-align': 'center' , 'align-items': 'center', 'justify-content': 'center', "marginTop": '50vh'},
                ),
            
            # loader for bubble graph
            dcc.Loading(                
                type=INIT_LOADER_TYPE,
                color=INIT_LOADER_CHART_COLOR, #hex colour close match to nav bar
                children=html.Span(id="my-loader-bubble"),
                style={"zIndex":1, 'display': 'flex', 'vertical-align': 'center' , 'align-items': 'center', 'justify-content': 'center', "marginTop": '50vh'},
                ),
            
            # loader for line graph
            dcc.Loading(                
                type=INIT_LOADER_TYPE,
                color=INIT_LOADER_CHART_COLOR, #hex colour close match to nav bar
                children=html.Span(id="my-loader-line"),
                style={"zIndex":1, 'display': 'flex', 'vertical-align': 'center' , 'align-items': 'center', 'justify-content': 'center', "marginTop": '50vh'},
            ),
            
            # loader for sunburst
            dcc.Loading(                
                type=INIT_LOADER_TYPE,
                color=INIT_LOADER_CHART_COLOR, #hex colour close match to nav bar
                children=html.Span(id="my-loader-sunburst"),
                style={"zIndex":1, 'display': 'flex', 'vertical-align': 'center' , 'align-items': 'center', 'justify-content': 'center', "marginTop": '50vh'},
                ),
            
            # loader for the globe          
            dcc.Loading(                
                type=INIT_LOADER_TYPE,
                color=INIT_LOADER_CHART_COLOR, #hex colour close match to nav bar
                children=html.Span(id="my-loader-globe"),
                style={"zIndex":1, 'display': 'flex', 'vertical-align': 'center' , 'align-items': 'center', 'justify-content': 'center', "marginTop": '50vh'},
                ),
            
            # loader for bar graph
            dcc.Loading(                
                type=INIT_LOADER_TYPE,
                color=INIT_LOADER_CHART_COLOR, #hex colour close match to nav bar
                children=html.Span(id="my-loader-bar"),
                style={"zIndex":1, 'display': 'flex', 'vertical-align': 'center' , 'align-items': 'center', 'justify-content': 'center', "marginTop": '50vh'},
            ),

            # loader for bar graph
            dcc.Loading(                
                type=INIT_LOADER_TYPE,
                color=INIT_LOADER_CHART_COLOR, #hex colour close match to nav bar
                children=html.Span(id="my-loader-xp"),
                style={"zIndex":1, 'display': 'flex', 'vertical-align': 'center' , 'align-items': 'center', 'justify-content': 'center', "marginTop": '50vh'},
            ),

            
            # THE MAIN GRAPH CENTERPIECE
            dcc.Graph(
                style={"height": INIT_MAP_H, "width": INIT_MAP_W, 'z-index':'2' }, 
                id="geomap_figure",
                figure = create_map_geomap_empty(),
                config={'displayModeBar': False },              
            )
        ],)
    return body
    
    


def create_dash_layout_about_modal():    
       
    m = dbc.Modal(
            [
                dbc.ModalHeader(html.Div("This site is a front-end to thousands of datasets.", style={"fontFamily":INIT_MODAL_HEADER_FONT_GENERAL, "fontSize": INIT_MODAL_HEADER_FONT_SIZE, "fontWeight": INIT_MODAL_HEADER_FONT_WEIGHT })),
                dbc.ModalBody(modal_text.about_modal_body),
                dbc.ModalFooter([
                    dcc.Markdown(""" Built with ![Image](/static/img/heart1.png) in Python using [Dash](https://plotly.com/dash/)."""),
                    dbc.Button("Close", id="modal-about-close", className="ml-auto",size=INIT_BUTTON_SIZE)
                    ]
                ),
                #html.Div([html.Audio(id='audio', src='/static/img/encarta_intro.mp3', autoPlay=True, loop=False )]) #,controls=True
                
                
            ],
            id="dbc-modal-about",
            centered=True,
            size="xl",
            style={"max-width": "none", "width": INIT_ABOUT_MODAL_W}  #70%
        )
    return m

def create_dash_layout_userguide_modal():
    m = dbc.Modal(
            [
                #dbc.ModalHeader(dcc.Markdown(""" # User Guide # """), style={"fontFamily":INIT_MODAL_HEADER_FONT_UGUIDE}),                            
                dbc.ModalBody(html.Video(id='video', src='/static/img/user_guide.mp4', autoPlay=True, loop=False, controls=True, style={"width": "100%", 'height':"100%", "backgroundColor": 'transparent', "color":'transparent'}  ),), 
                dbc.ModalFooter([dcc.Markdown(""""""),
                    dbc.Button("Close", id="modal-uguide-close", className="ml-auto",size=INIT_BUTTON_SIZE)]
                ),                
            ],
            id="dbc-modal-uguide",
            centered=True,
            size="xl",
            style={"max-width": "none", "width": INIT_UGUIDE_MODAL_W}  
        )
    return m



def create_dash_layout_settings_modal():
    
    #First build the modal body as it is complex (modal itself built at end function)
    settings_modal_body = html.Div([
        
        
        dbc.Row([
                
                #Border resolution    
                html.Div([
                #dbc.Container([    
        
                    #RESOLUTION
                    dcc.Markdown(""" #### Border Resolution """, style={"marginTop":'1vw'}),
                    dcc.Markdown(""" The number of individual points used to draw a line around a region."""),
             
                    dbc.Row([
                     
                        dbc.Card(
                        [
                            dbc.CardImg(src="/static/img/border1.PNG", top=True),
                            dbc.CardBody(dbc.Button("LOW DETAIL", size=INIT_BUTTON_SIZE, outline=True, active = True, color="success", id='settingsbtn-resolution-low'),),
                        ],
                        style={"width": INIT_SETTINGS_BORDER_CARD_WIDTH, 'align-items': 'center', 'justify-content': 'center',"marginBottom": 0, "marginTop": '1vw', "marginLeft": 0, "marginRight": '1vw' },
                        ),
                        
                        dbc.Card(
                        [
                            dbc.CardImg(src="/static/img/border2.PNG", top=True),
                            dbc.CardBody(dbc.Button("MEDIUM DETAIL", size=INIT_BUTTON_SIZE, outline=True, active = False, color="warning", id='settingsbtn-resolution-med'),),
                        ],
                        style={"width": INIT_SETTINGS_BORDER_CARD_WIDTH, 'align-items': 'center', 'justify-content': 'center', "marginBottom": 0, "marginTop": '1vw', "marginLeft": 0, "marginRight": '1vw'},
                        ),
                        
                        dbc.Card(
                        [
                            dbc.CardImg(src="/static/img/border3.PNG", top=True),
                            dbc.CardBody(dbc.Button("INSANE DETAIL", size=INIT_BUTTON_SIZE, outline=True, active = False, color="danger", id='settingsbtn-resolution-high')),
                        ],
                        style={"width": INIT_SETTINGS_BORDER_CARD_WIDTH, 'align-items': 'center', 'justify-content': 'center', "marginBottom": 0, "marginTop": '1vw', "marginLeft": 0, "marginRight": '1vw'},
                        ),
                        
                    ], style={"marginBottom": 0, "marginTop": 0, "marginLeft": 0, "marginRight": 0, }) #end row
                
                ]), #end div , style={'margin-left': '1vw'}
                
                #Map style
                #dbc.Container([
                html.Div([    
                    #MAP STYLE
                    dcc.Markdown(""" #### Map Style  """, style={"marginTop":'1vw'}),
                    dcc.Markdown(""" Choose from the free tile-based map styles courtesy of [MapBox](https://www.mapbox.com/) """),                
                    
                    #Map style
                    dbc.Row([   
               
                 
                        dbc.Card(
                        [
                            dbc.CardImg(src="/static/img/osmp.PNG", top=True, ), #style={'height':'58%'}
                            dbc.CardBody(dbc.Button("opn-street-map", size=INIT_BUTTON_SIZE, outline=True, active = False, color="secondary", id='settingsbtn-mapstyle-openstreetmap'),),
                        ],
                        style={"width": INIT_SETTINGS_MAP_CARD_WIDTH, 'align-items': 'center', 'justify-content': 'center', "marginBottom": 0, "marginTop": '1vw', "marginLeft": '1vw', "marginRight": 0},
                        ),
                        
                        dbc.Card(
                        [
                            dbc.CardImg(src="/static/img/cart.PNG", top=True, ), #style={'height':'58%'}
                            dbc.CardBody(dbc.Button("carto-positron", size=INIT_BUTTON_SIZE, outline=True, active = True, color="secondary",id='settingsbtn-mapstyle-carto-positron'),),
                        ],
                        style={"width": INIT_SETTINGS_MAP_CARD_WIDTH, 'align-items': 'center', 'justify-content': 'center', "marginBottom": 0, "marginTop": '1vw', "marginLeft": '1vw', "marginRight": 0},
                        ),
                        
                        dbc.Card(
                        [
                            dbc.CardImg(src="/static/img/dark.PNG", top=True, ), #style={'height':'58%'}
                            dbc.CardBody(dbc.Button("carto-dark",size=INIT_BUTTON_SIZE, outline=True, active = False, color="secondary",id='settingsbtn-mapstyle-darkmatter'),),
                        ],
                        style={"width": INIT_SETTINGS_MAP_CARD_WIDTH, 'align-items': 'center', 'justify-content': 'center', "marginBottom": 0, "marginTop": '1vw', "marginLeft": '1vw', "marginRight": 0},
                        ),
                        
                        dbc.Card(
                        [
                            dbc.CardImg(src="/static/img/terrain.PNG",  top=True), #style={'height':'58%'}
                            dbc.CardBody(dbc.Button("terrain", size=INIT_BUTTON_SIZE,outline=True, active = False, color="secondary",id='settingsbtn-mapstyle-stamen-terrain'),),
                        ],
                        style={"width": INIT_SETTINGS_MAP_CARD_WIDTH, 'align-items': 'center', 'justify-content': 'center', "marginBottom": 0, "marginTop": '1vw', "marginLeft": '1vw', "marginRight": 0},
                        ),
                        
                        dbc.Card(
                        [
                            dbc.CardImg(src="/static/img/charlie3.png", top=True,), #style={'height':'57%'}
                            dbc.CardBody(dbc.Button("charlie",size=INIT_BUTTON_SIZE, outline=True, active = False, color="secondary",id='settingsbtn-mapstyle-stamen-toner'),),
                        ],
                        style={"width": INIT_SETTINGS_MAP_CARD_WIDTH, 'align-items': 'center', 'justify-content': 'center', "marginBottom": 0, "marginTop": '1vw', "marginLeft": '1vw', "marginRight": 0},
                        ),
                        
                        dbc.Card(
                        [
                            dbc.CardImg(src="/static/img/watercolour.PNG", top=True), # style={'height':'58%'}
                            dbc.CardBody(dbc.Button("watercolor", size=INIT_BUTTON_SIZE, outline=True, active = False, color="secondary",id='settingsbtn-mapstyle-stamen-watercolor'), ),
                        ],
                        style={"width": INIT_SETTINGS_MAP_CARD_WIDTH, 'align-items': 'center', 'justify-content': 'center', "marginBottom": 0, "marginTop": '1vw', "marginLeft": '1vw', "marginRight": 0},
                        ),
                    ]), #end row
               
                    
                ] ), #end div , style={'margin-left': '1vw'}
          ], style={'margin-left': '1vw'}),    # end main row
        
        
        #tool tips
        dbc.Tooltip(
                "High resolution borders will take much longer to load each dataset (~30 seconds).",
                target='settingsbtn-resolution-high',
                placement='bottom',
                style={},
        ),
        
        dbc.Tooltip(
                "Default resolution. Fastest performance.",
                target='settingsbtn-resolution-low',
                placement='bottom',
                style={},
        ),
                
        html.Div(html.Br()),    
        
        #COLOURSCALE BUTTON GROUP
        
        html.Div([    
        
                #COLOUR SCHEME
                dcc.Markdown(""" #### Colour Scheme  """),
                modal_text.settings_colour_scheme,
                                
                #Create colorscale buttons recursively by calling a special function
                html.Div(children=[create_dash_layout_settings_modal_colorscale_button(i) for i in range(0,93)]),
                
                #Create reverse toggle button for reversing colorscale
                html.Div([                   
                        html.H6("Reverse Color Scale",style={"marginLeft": 0, "marginBottom": 0, "marginTop":10, 'marginRight':10, 'display':'inline-block'}),
                        dbc.ButtonGroup([  
                            dbc.Button("OFF", color="danger", outline=True, id='settingsbtn-normal-colorscale',style={"marginLeft": 1, "marginBottom": 0, "marginTop":5}, size=INIT_BUTTON_SIZE),
                            dbc.Button("ON", color="success", outline=True, id='settingsbtn-reverse-colorscale',style={"marginLeft": 0, "marginBottom": 0, "marginTop":5}, size=INIT_BUTTON_SIZE),
                            
                            ],style={'display':'inline-block'})                           
                        ])
               
        ], style={'margin-left': '1vw'}),    # end main row) 
    ])
    
    
    #Build the actual modal
    m = dbc.Modal(
        [
            dbc.ModalHeader(html.Div("Settings", style={"fontFamily":INIT_MODAL_HEADER_FONT_GENERAL, "fontSize": INIT_MODAL_HEADER_FONT_SIZE, "fontWeight": INIT_MODAL_HEADER_FONT_WEIGHT })),
            dbc.ModalBody(settings_modal_body),
            dbc.ModalFooter([ 
                dbc.Button("Close", id="modal-settings-close", className="",size=INIT_BUTTON_SIZE),
                dbc.Button("Apply settings", id="modal-settings-apply", className="", color="dark", size=INIT_BUTTON_SIZE)                               
                ]
            ),  
            
        ],
        id="dbc-modal-settings",
        centered=True,
        size="xl",
        style={"max-width": "none", "width": INIT_SETTINGS_MODAL_W}
    )
    return m
  

#construct colorscale button
def create_dash_layout_settings_modal_colorscale_button(i):
    
    #hide the first 'auto' option as this messes with the ability to get the colorwheel
    if i == 0:
        return dbc.Button(children=geomap_colorscale[i], color="light", className="mr-1", id=geomap_colorscale[i], style={'display': 'none'})
    
    else:
        return dbc.Button(children=geomap_colorscale[i], color="light", className="mr-1", id=geomap_colorscale[i], size=INIT_BUTTON_SIZE, style={'marginBottom':3})


def create_dash_layout_bargraph_modal():
    
    m =  dbc.Modal(
                [                            
                    dbc.ModalHeader(html.Div(id="bar-graph-modal-title",style={"fontFamily":INIT_MODAL_HEADER_FONT_GENERAL, "fontSize": INIT_MODAL_HEADER_FONT_SIZE, "fontWeight": INIT_MODAL_HEADER_FONT_WEIGHT }), ),                           
                    
                    dbc.ModalBody(html.Div([                        
                        
                        # the dropdown components
                        dbc.Row([                        
                            dbc.Col([                        
                                html.H5("Highlight specific countries"),
                                dcc.Dropdown(
                                    options=[],
                                    id="bar-graph-dropdown-countrieselector",
                                    multi=True,
                                    placeholder='Select countries or type to search',
                                ),
                            ]),                            
                            dbc.Col([
                                html.H5("Change datasets"),
                                dcc.Dropdown(
                                    options=[],
                                    id="bar-graph-dropdown-dataset",
                                    multi=False,
                                    placeholder='Select dataset or type to search',
                                ),
                            ]),
                            dbc.Col([
                                html.H5("Change year"),
                                dcc.Dropdown(
                                    options=[],
                                    id="bar-graph-dropdown-year",
                                    multi=False,
                                    placeholder='Select year',
                                    clearable=False,
                                ),
                            ],width=2),
                        ], style={'marginBottom':10}), #end row
                            
                        # loader for component refreshes
                        dcc.Loading(
                            #id="my-loader-geobar",
                            type=INIT_LOADER_TYPE,
                            color=INIT_LOADER_CHART_COMPONENT_COLOR,              #INIT_LOADER_COLOR, #hex colour close match to nav bar ##515A5A
                            children=html.Span(id="my-loader-bar-refresh"),
                            style={"zIndex":1, 'display': 'flex', 'vertical-align': 'center' , 'align-items': 'center', 'justify-content': 'center', 'paddingTop':50 },
                        ),
                        
                        # the main bargraph
                        dcc.Graph(id='bar-graph',
                                  #animate=True,
                                  #animation_options={ 'frame': { 'redraw': True, }, 'transition': { 'duration': 500, 'ease': 'cubic-in-out', }, },
                                  style={"backgroundColor": "#1a2d46", 'color': '#ffffff', 'height': INIT_BAR_H},
                                  config={'displayModeBar': False },),
                    ])),                           
                    
                    dbc.ModalFooter([
                        html.Div([
                            html.Span("Data source: "),
                            html.Span(id='bar-graph-modal-footer'), 
                            html.Div(dcc.Link(href='', target="_blank", id="bar-graph-modal-footer-link", style={'display':'inline-block'})),
                        ], style={"fontSize": INIT_MODAL_FOOTER_FONT_SIZE, } ),
                       
                            
                        html.Div([       
                            dbc.Button("About", id='modal-bar-guide-popover-target', color='info', className="mr-1", outline=False, size=INIT_BUTTON_SIZE),
                            dbc.Button("Instructions", id='modal-bar-instruction-popover-target', color='warning', className="mr-1", outline=False, size=INIT_BUTTON_SIZE),
                            dbc.Button("Download", id='modal-bar-download', color='success', className="mr-1", outline=False, size=INIT_BUTTON_SIZE),
                            Download(id='download_dataset_bar'),                           
                            dbc.Button("Close", id="modal-bar-close", className="mr-1", size=INIT_BUTTON_SIZE),
                        ],className="ml-auto"),                        
                        
                        
                        dbc.Popover(
                            [
                                dbc.PopoverHeader("Instructions", style={'fontWeight':'bold'}),
                                dbc.PopoverBody(hovertip_text.bargraph_instructions),
                            ],
                            #id="modal-bar-instruction-popover",
                            #is_open=False,
                            target="modal-bar-instruction-popover-target",
                            trigger="hover",
                            placement="top",
                            hide_arrow=False,
                            style={"zIndex":1}
                        ),
                        
                        dbc.Popover(
                            [
                                dbc.PopoverHeader("About", style={'fontWeight':'bold'}),
                                dbc.PopoverBody(hovertip_text.bargraph_about)                                    
                            ],
                            #id="modal-bar-guide-popover",
                            #is_open=False,
                            target="modal-bar-guide-popover-target",
                            trigger="hover",
                            placement="top",
                            hide_arrow=False,
                            #style={"zIndex":1}
                        ),
                        
                        dbc.Popover(
                          [
                          dbc.PopoverHeader("Download", style={'fontWeight':'bold'}),
                          dbc.PopoverBody([
                              html.Div('Raw data'),
                              dbc.Button(".xlsx", outline=True, color="secondary", className="mr-1", id="btn-popover-bar-download-xls", style={}, size=INIT_BUTTON_SIZE),
                              dbc.Button(".csv", outline=True, color="secondary", className="mr-1", id="btn-popover-bar-download-csv", style={}, size=INIT_BUTTON_SIZE),
                              dbc.Button(".json", outline=True, color="secondary", className="mr-1", id="btn-popover-bar-download-json", style={}, size=INIT_BUTTON_SIZE),
                              html.Div('Chart', style={'marginTop':5}),
                              dbc.Button(".pdf", outline=True, color="secondary", className="mr-1", id="btn-popover-bar-download-pdf", style={}, size=INIT_BUTTON_SIZE),
                              dbc.Button(".jpg", outline=True, color="secondary", className="mr-1", id="btn-popover-bar-download-jpg", style={}, size=INIT_BUTTON_SIZE),
                              dbc.Button(".png", outline=True, color="secondary", className="mr-1", id="btn-popover-bar-download-png", style={}, size=INIT_BUTTON_SIZE),
                              dbc.Button(".svg", outline=True, color="secondary", className="mr-1", id="btn-popover-bar-download-svg", style={}, size=INIT_BUTTON_SIZE),
                              html.Div('Advanced', style={'marginTop':5,'display':'none'}),
                              dbc.Button("Downloads Area", outline=True, color="secondary", className="mr-1", id="btn-popover-bar-download-land", style={'display':'none'}, size=INIT_BUTTON_SIZE),  
                              ]),
                          ],
                          id="download-popover-bar",                                        
                          target="modal-bar-download",
                          #style={'maxHeight': '300px', 'overflowY': 'auto'},
                          trigger="legacy",
                          placement="top",
                          hide_arrow=False,
                          
                          ), 
                        
                        
                        
                    ]),
                ],
                id="dbc-modal-bar",
                centered=True,
                size="xl",
                style={"max-width": "none", "width": INIT_BAR_MODAL_W, 'max-height': "100vh"} 
            )
    
    return m

def create_dash_layout_linegraph_modal():
    m = dbc.Modal(
            [                            
                dbc.ModalHeader(html.H1(id="line-graph-modal-title",style={"fontFamily":INIT_MODAL_HEADER_FONT_GENERAL, "fontSize": INIT_MODAL_HEADER_FONT_SIZE, "fontWeight": INIT_MODAL_HEADER_FONT_WEIGHT }),),                           
                
                dbc.ModalBody(html.Div([                    
                    dbc.Row([                    
                        
                        dbc.Col([                    
                            html.H5("Select countries"),                            
                            dcc.Dropdown(
                                options=[],
                                value=['United States of America', 'China', 'India', 'United Kingdom'],
                                id="line-graph-dropdown-countries",
                                multi=True,
                                placeholder='Select countries',
                                #style={'max-height': '100px'},
                            ),                             
                            
                            dbc.Button("Select all countries",  outline=True, color="secondary", id="linegraph-allcountries-button", style={"marginLeft": 0, 'marginTop':10, "marginBottom": 0, 'display': 'inline-block', 'opacity':INIT_BUTTON_OPACITY}, size=INIT_BUTTON_SIZE),
                            dbc.Button("Remove all countries",  outline=True, color="secondary", id="linegraph-nocountries-button", style={"marginLeft": 10, 'marginTop':10, "marginBottom": 0, 'display': 'inline-block', 'opacity':INIT_BUTTON_OPACITY}, size=INIT_BUTTON_SIZE),
                            
                             dbc.Tooltip(
                                "Only for the brave!",
                                target='linegraph-allcountries-button',
                                placement='bottom',                
                                ),
                                                        
                        ]),
                        dbc.Col([                        
                            html.H5("Change datasets"),
                            dcc.Dropdown(
                                options=[],
                                id="line-graph-dropdown-dataset",
                                multi=False,
                                placeholder='Select dataset or type to search'
                            ),
                        ]),                        
                    ]),                    
                    
                    # loader for component refreshes
                    dcc.Loading(
                        #id="my-loader-geobar",
                        type=INIT_LOADER_TYPE,
                        color=INIT_LOADER_CHART_COMPONENT_COLOR, #hex colour close match to nav bar ##515A5A
                        children=html.Span(id="my-loader-line-refresh"),
                        style={"zIndex":1, 'display': 'flex', 'vertical-align': 'center' , 'align-items': 'center', 'justify-content': 'center', 'paddingTop':100 },
                    ),
                    
                    dcc.Graph(id='line-graph',
                              animate=False,
                              style={"backgroundColor": "#1a2d46", 'color': '#ffffff', 'height': INIT_LINE_H},
                              config={'displayModeBar': False },),])),                           
                
                dbc.ModalFooter([
                    
                    html.Div([   
                        html.Span("Data source: "),
                        html.Span(id='line-graph-modal-footer'),
                        html.Div(dcc.Link(href='', target="_blank", id="line-graph-modal-footer-link")),
                    ], style={'fontSize':INIT_MODAL_FOOTER_FONT_SIZE}), #end div
                    
                    html.Div([
                        dbc.Button("About", id='modal-line-guide-popover-target', color='info', className="mr-1", size=INIT_BUTTON_SIZE),
                        dbc.Button("Instructions", id='modal-line-instructions-popover-target', color='warning', className="mr-1", size=INIT_BUTTON_SIZE),
                        dbc.Button("Download", id='modal-line-download', color='success', className="mr-1", size=INIT_BUTTON_SIZE),
                        Download(id='download_dataset_line'),
                        dbc.Button("Close", id="modal-line-close", className="mr-1", size=INIT_BUTTON_SIZE)
                        
                    ], className='ml-auto'),
                    
                                        
                    dbc.Popover(
                        [
                            dbc.PopoverHeader("Instructions", style={'fontWeight':'bold'}),
                            dbc.PopoverBody(hovertip_text.linegraph_instructions)
                        ],
                        #id="modal-line-instructions-popover",
                        #is_open=False,
                        target="modal-line-instructions-popover-target",
                        trigger="hover",
                        placement="top",
                        hide_arrow=False,
                        #style={"zIndex":1}
                    ),
                    
                    dbc.Popover(
                        [
                            dbc.PopoverHeader("About", style={'fontWeight':'bold'}),
                            dbc.PopoverBody(hovertip_text.linegraph_about),
                        ],
                        #id="modal-line-guide-popover",
                        #is_open=False,
                        target="modal-line-guide-popover-target",
                        trigger="hover",
                        placement="top",
                        hide_arrow=False,                        
                        style={"zIndex":1}
                    ),
                    
                    dbc.Popover(
                          [
                          dbc.PopoverHeader("Download", style={'fontWeight':'bold'}),
                          dbc.PopoverBody([          
                              html.Div('Raw data'),
                              dbc.Button(".xlsx", outline=True, color="secondary", className="mr-1", id="btn-popover-line-download-xls", style={}, size=INIT_BUTTON_SIZE),
                              dbc.Button(".csv", outline=True, color="secondary", className="mr-1", id="btn-popover-line-download-csv", style={}, size=INIT_BUTTON_SIZE),
                              dbc.Button(".json", outline=True, color="secondary", className="mr-1", id="btn-popover-line-download-json", style={}, size=INIT_BUTTON_SIZE),
                              html.Div('Chart', style={'marginTop':5}),
                              dbc.Button(".pdf", outline=True, color="secondary", className="mr-1", id="btn-popover-line-download-pdf", style={}, size=INIT_BUTTON_SIZE),
                              dbc.Button(".jpg", outline=True, color="secondary", className="mr-1", id="btn-popover-line-download-jpg", style={}, size=INIT_BUTTON_SIZE),
                              dbc.Button(".png", outline=True, color="secondary", className="mr-1", id="btn-popover-line-download-png", style={}, size=INIT_BUTTON_SIZE),
                              dbc.Button(".svg", outline=True, color="secondary", className="mr-1", id="btn-popover-line-download-svg", style={}, size=INIT_BUTTON_SIZE),
                              html.Div('Advanced', style={'marginTop':5,'display':'none'}),
                              dbc.Button("Downloads Area", outline=True, color="secondary", className="mr-1", id="btn-popover-line-download-land", style={'display':'none'}, size=INIT_BUTTON_SIZE),
                              ]),
                          ],
                          id="download-popover-line",                                        
                          target="modal-line-download",
                          #style={'maxHeight': '300px', 'overflowY': 'auto'},
                          trigger="legacy",
                          placement="top",
                          hide_arrow=False,
                          
                    ), 
                    
                ]), #end footer
                
            ],
            id="dbc-modal-line",
            centered=True,
            size="xl",
            style={"max-width": "none", "width": INIT_LINE_MODAL_W} 
        )
    return m

def create_dash_layout_globe_modal():
    m = dbc.Modal(
                [
                    dbc.ModalHeader(html.Div(html.H1(id="globe-modal-title",style={"fontFamily":INIT_MODAL_HEADER_FONT_GENERAL, "fontSize": INIT_MODAL_HEADER_FONT_SIZE, "fontWeight": INIT_MODAL_HEADER_FONT_WEIGHT })),),
                    
                    dbc.ModalBody([
                        html.Div(id='globe-body', style={'height': INIT_GLOBE_H, },),
                        
                        # loader for globe refreshes
                        dcc.Loading(
                            #id="my-loader-geobar",
                            type=INIT_LOADER_TYPE,
                            color=INIT_LOADER_CHART_COMPONENT_COLOR, #hex colour close match to nav bar ##515A5A
                            children=html.Span(id="my-loader-globe-refresh"),
                            style={"zIndex":1, 'display': 'flex', 'vertical-align': 'center' , 'align-items': 'center', 'justify-content': 'center', },
                        ),
                    
                        
                        ]), #'height': "50pc", 'width': '100%', # 'display': 'flex', 'align-items': 'center', 'justify-content': 'center'
                    
                    dbc.ModalFooter([                           
                            
                            #dbc.Row([
                                
                            #    dbc.Col([
                            
                                    html.Div([
                                        html.Span("Data source: "),
                                        html.Span(id='globe-modal-footer'), 
                                        html.Div(dcc.Link(href='', target="_blank", id="globe-modal-footer-link", style={'display':'inline-block'})),
                                    ], style={"fontSize": INIT_MODAL_FOOTER_FONT_SIZE, } ),
                                    
                             #   ]),
                             #   dbc.Col([
                            
                                    html.Div([
                                        dbc.Button("About", id='modal-globe-guide-popover-target', color='info', className="mr-1", outline=False, size=INIT_BUTTON_SIZE),
                                        dbc.Button("Instructions", id='modal-globe-instructions-popover-target', color='warning', className="mr-1", outline=False, size=INIT_BUTTON_SIZE), 
                                        dbc.Button("High Resolution", color="primary", id="modal-globe-ne50m", className="mr-1", size=INIT_BUTTON_SIZE ),
                                        dbc.Button("Jellybean Mode", color="success", id="modal-globe-jelly", className="mr-1", size=INIT_BUTTON_SIZE),
                                        dbc.Button("Close", id="modal-globe-close", className="mr-1", size=INIT_BUTTON_SIZE ),
                                    ], className="ml-auto", style={'display':'inline-block'}) ,
                              #  ]),
                            #]),
                                
                            
                            dbc.Popover(
                            [
                                dbc.PopoverHeader("Instructions", style={'fontWeight':'bold'}),
                                dbc.PopoverBody(hovertip_text.globe_instructions),
                            ],
                            #id="modal-globe-instructions-popover",
                            #is_open=False,
                            target="modal-globe-instructions-popover-target",
                            trigger="hover",
                            placement="top",
                            hide_arrow=False,
                            style={"zIndex":1}
                            ),
                            
                            dbc.Popover(
                                [
                                    dbc.PopoverHeader("About", style={'fontWeight':'bold'}),
                                    dbc.PopoverBody(hovertip_text.globe_about),                                    
                                ],
                                #id="modal-globe-guide-popover",
                                #is_open=False,
                                target="modal-globe-guide-popover-target",
                                trigger="hover",
                                placement="top",
                                hide_arrow=False,
                                style={"zIndex":1}
                            ),
                        
                        ],),
                    
                    #tool tip high resolution
                    dbc.Tooltip(
                                "Allow up to 30 seconds to load",
                                target='modal-globe-ne50m',
                                placement='top',
                                style={},
                        
                    ),
                ],
                id="dbc-modal-globe",
                centered=True,
                size="xl",
                style={"max-width": "none", "width": INIT_GLOBE_MODAL_W} #85%
            )
    return m

def create_dash_layout_geobar_modal():
    m = dbc.Modal(
            [
                dbc.ModalHeader(html.Div([
                    html.H1(id="geobar-modal-title",style={"fontFamily":INIT_MODAL_HEADER_FONT_GENERAL, "fontSize": INIT_MODAL_HEADER_FONT_SIZE, "fontWeight": INIT_MODAL_HEADER_FONT_WEIGHT }),
                    
                ]),),
                
                dbc.ModalBody([                  
                    html.Div(id='geobar-test', style={'height': INIT_JIGSAW_H, 'display': 'flex', 'align-items': 'center', 'justify-content': 'center'},),  
                    
                     # loader for component refreshes
                    dcc.Loading(                        
                        type=INIT_LOADER_TYPE,
                        color=INIT_LOADER_CHART_COMPONENT_COLOR, #hex colour close match to nav bar ##515A5A
                        children=html.Span(id="my-loader-geobar-refresh"),
                        style={"zIndex":1, 'display': 'flex', 'vertical-align': 'center' , 'align-items': 'center', 'justify-content': 'center', },
                    ),
                
                ]), #, 'width': INIT_JIGSAW_W
                
                dbc.ModalFooter([
                            
                            html.Div([
                                html.Span("Data source: "),
                                html.Span(id='geobar-modal-footer'), 
                                html.Div(dcc.Link(href='', target="_blank", id="geobar-modal-footer-link",)),
                            ], style={"fontSize": INIT_MODAL_FOOTER_FONT_SIZE, 'display':'inline-block'} ),
                      
                            html.Div([
                                dbc.Button("About", id='modal-geobar-guide-popover-target', color='info', className="mr-1", outline=False, size=INIT_BUTTON_SIZE),
                                dbc.Button("Instructions", id='modal-geobar-instructions-popover-target', color='warning', className="mr-1", outline=False, size=INIT_BUTTON_SIZE),                            
                                dbc.Button("Jellybean Mode", color="success", id="modal-geobar-jelly", className="mr-1",size=INIT_BUTTON_SIZE),
                                dbc.Button("Close", id="modal-geobar-close", className="mr-1",size=INIT_BUTTON_SIZE),
                            ], className="ml-auto" ), 
                            
                
                            dbc.Popover(
                                [
                                dbc.PopoverHeader("Instructions", style={'fontWeight':'bold'}),
                                dbc.PopoverBody(hovertip_text.jigsaw_instructions),
                                ],
                                #id="modal-geobar-instructions-popover",
                                #is_open=False,
                                target="modal-geobar-instructions-popover-target",
                                trigger="hover",
                                placement="top",
                                hide_arrow=False,
                                #style={"zIndex":1}
                            ),
                            
                            dbc.Popover(
                                [
                                dbc.PopoverHeader("About", style={'fontWeight':'bold'}),
                                dbc.PopoverBody(hovertip_text.jigsaw_about),
                                #dbc.PopoverBody(dcc.Markdown(""" Built with ![Image](media/heart1.png) in Python using [Dash](https://plotly.com/dash/)."""), style={'display':'inline-block'}),
                                ],
                                #id="modal-geobar-guide-popover",
                                #is_open=False,
                                target="modal-geobar-guide-popover-target",
                                trigger="hover",
                                placement="top",
                                hide_arrow=False,
                                #style={"zIndex":1}
                            ),
                        ]),
                
                
            ],
            id="dbc-modal-geobar",
            centered=True,
            size="xl",
            style={"max-width": "none", "width": INIT_JIGSAW_MODAL_W} #85%
        )
    return m


def create_dash_layout_sunburst_modal():
    m = dbc.Modal(
            [
                dbc.ModalHeader(html.H1(id="sunburst-graph-modal-title",style={"fontFamily":INIT_MODAL_HEADER_FONT_GENERAL, "fontSize": INIT_SUNBURST_MODAL_HEADER_FONT_SIZE, "fontWeight": INIT_MODAL_HEADER_FONT_WEIGHT }),),
                dbc.ModalBody(html.Div([
                    
                    dbc.Row([                        
                        dbc.Col([
                            #Dropdown quantitative data
                            html.H5("Quantitative data (pizza slices)"),                            
                            dcc.Dropdown(
                                options=[],
                                value='Population, total',
                                id="sunburst-dropdown-pizza",
                                multi=False,
                                placeholder='Select dataset',
                                clearable=False,
                            ),
                        ]),                                               
                        dbc.Col([
                            #Dropdown color axis
                            html.H5("Color data (pizza toppings)"),
                            dcc.Dropdown(
                                options=[],
                                value='Life expectancy at birth, data from IHME',
                                id="sunburst-dropdown-toppings",
                                multi=False,
                                placeholder='Select dataset',
                                clearable=False,
                            ),
                        ]),
                        dbc.Col([
                            #Dropdown years
                            #html.H5("Available years"),
                            dcc.Dropdown(
                                options=[],
                                id="sunburst-dropdown-years",
                                multi=False,
                                placeholder='Select...',
                                clearable=False,
                                style={'display':'none'}
                            ),
                        ], width=2),
                    ]),              
                    
                    dcc.Graph(id='sunburst-graph', animate=False, style={"backgroundColor": "#1a2d46", 'color': '#ffffff',  'height':INIT_SUNBURST_H}, config={'displayModeBar': False },),  
                    
                    # loader for component refreshes
                    dcc.Loading(                        
                        type=INIT_LOADER_TYPE,
                        color=INIT_LOADER_CHART_COMPONENT_COLOR, #hex colour close match to nav bar ##515A5A
                        children=html.Span(id="my-loader-sunburst-refresh"),
                        style={"zIndex":1, 'display': 'flex', 'vertical-align': 'center' , 'align-items': 'center', 'justify-content': 'center', 'paddingTop':0 },
                    ),    
                    
                ])),
                
                
                dbc.ModalFooter([
                    
                    html.Div([                    
                        html.Span("Data source: "),
                        html.Span(id='sunburst-graph-modal-footer'),    
                        html.Div(dcc.Link(href='', target="_blank", id="sunburst-graph-modal-footer-link")),
                    ], style={"fontSize": 12, 'display':'inline-block'} ),
                        
                    html.Div([
                        dbc.Button("About", id='modal-sunburst-guide-popover-target', color='info', className="mr-1", size=INIT_BUTTON_SIZE),
                        dbc.Button("Instructions", id='modal-sunburst-instructions-popover-target', color='warning', className="mr-1", size=INIT_BUTTON_SIZE),
                        dbc.Button("Show Example", id='modal-sunburst-examplebtn', color='light', className="mr-1", size=INIT_BUTTON_SIZE),
                        dbc.Button("Download", id='modal-sunburst-download', color='success', className="mr-1", size=INIT_BUTTON_SIZE),
                        Download(id='download_dataset_sunburst_csv'),
                        dbc.Button("Close", id="modal-sunburst-close", className="mr-1", size=INIT_BUTTON_SIZE), 
                        
                    ], className="ml-auto"),
                    
                    dbc.Popover(
                        [
                            dbc.PopoverHeader("About", style={'fontWeight':'bold'}),
                            dbc.PopoverBody(hovertip_text.sunburst_about),
                        ],
                        #id="modal-sunburst-guide-popover",
                        #is_open=False,
                        target="modal-sunburst-guide-popover-target",
                        trigger="hover",
                        placement="top",
                        hide_arrow=False,
                        #style={"zIndex":1}
                    ),
                    
                    dbc.Popover(
                        [
                            dbc.PopoverHeader("Instructions", style={'fontWeight':'bold'}),
                            dbc.PopoverBody(hovertip_text.sunburst_instructions),
                        ],
                        #id="modal-sunburst-instructions-popover",
                        #is_open=False,
                        target="modal-sunburst-instructions-popover-target",
                        trigger="hover",
                        placement="top",
                        hide_arrow=False,
                        #style={"zIndex":1}
                    ),
                    
                    dbc.Popover(
                          [
                          dbc.PopoverHeader("Download format:", style={'fontWeight':'bold'}),
                          dbc.PopoverBody([
                              html.Div('Raw data'),
                              dbc.Button(".xlsx", outline=True, color="secondary", className="mr-1", id="btn-popover-sunburst-download-xls", style={}, size=INIT_BUTTON_SIZE),
                              dbc.Button(".csv", outline=True, color="secondary", className="mr-1", id="btn-popover-sunburst-download-csv", style={}, size=INIT_BUTTON_SIZE),
                              dbc.Button(".json", outline=True, color="secondary", className="mr-1", id="btn-popover-sunburst-download-json", style={}, size=INIT_BUTTON_SIZE),
                              html.Div('Chart', style={'marginTop':5}),
                              dbc.Button(".pdf", outline=True, color="secondary", className="mr-1", id="btn-popover-sunburst-download-pdf", style={}, size=INIT_BUTTON_SIZE),
                              dbc.Button(".png", outline=True, color="secondary", className="mr-1", id="btn-popover-sunburst-download-png", style={}, size=INIT_BUTTON_SIZE),
                              dbc.Button(".svg", outline=True, color="secondary", className="mr-1", id="btn-popover-sunburst-download-svg", style={}, size=INIT_BUTTON_SIZE),
                              dbc.Button(".jpg", outline=True, color="secondary", className="mr-1", id="btn-popover-sunburst-download-jpg", style={}, size=INIT_BUTTON_SIZE),
                              html.Div('Advanced', style={'marginTop':5,'display':'none'}),
                              dbc.Button("Downloads Area", outline=True, color="secondary", className="mr-1", id="btn-popover-sunburst-download-land", style={'display':'none'}, size=INIT_BUTTON_SIZE), 
                              
                              ]),
                          ],
                          id="download-popover-sunburst",                                        
                          target="modal-sunburst-download",
                          #style={'maxHeight': '300px', 'overflowY': 'auto'},
                          trigger="legacy",
                          placement="top",
                          hide_arrow=False,
                          
                    ), 
                    
                    
                ]),
            ],
            id="dbc-modal-sunburst",
            centered=True,
            size="xl",
            style={"max-width": "none", "width": INIT_SUNBURST_MODAL_W}  #70%
        )
    return m


def create_dash_layout_bubblegraph_modal():
    m = dbc.Modal(
            [                            
                dbc.ModalHeader(html.H1(id="bubble-graph-modal-title",style={"fontFamily":INIT_MODAL_HEADER_FONT_GENERAL, "fontSize": INIT_MODAL_HEADER_FONT_SIZE, "fontWeight": INIT_MODAL_HEADER_FONT_WEIGHT }),),                           
                
                dbc.ModalBody(html.Div([                    
                    dbc.Row([                        
                        dbc.Col([
                            #Dropdown x axis
                            html.H5("Vertical axis"),
                            dcc.Dropdown(
                                options=[],
                                value='GDP/capita (US$, inflation-adjusted)',
                                id="bubble-graph-dropdownX",
                                multi=False,
                                placeholder='Select dataset'
                            ),
                        ]),                                               
                        dbc.Col([
                            #Dropdown y axis
                            html.H5("Horizontal axis"),
                            dcc.Dropdown(
                                options=[],
                                value='Life expectancy at birth, data from IHME',
                                id="bubble-graph-dropdownY",
                                multi=False,
                                placeholder='Select dataset'
                            ),
                        ]),
                    ]),
                    
                    dbc.Row([                        
                        dbc.Col([                    
                            #Dropdown z axis
                            html.H5("Bubble size"),
                            dcc.Dropdown(
                                options=[],
                                value='Population, total',
                                id="bubble-graph-dropdownZ",
                                multi=False,
                                placeholder='Select dataset'
                            ),
                        ]),
                        dbc.Col([
                            
                            dbc.Row([
                                
                                dbc.Col([
                                    #Dropdown year axis
                                    html.H5("Available years"),
                                    dcc.Dropdown(
                                        options=[],
                                        id="bubble-graph-dropdownyear",
                                        multi=False,
                                        clearable=False,
                                    ),
                                ], width=6),
                                
                                dbc.Col([
                                
                                    html.H5("Logarithmic scale"),
                                    dcc.Checklist(
                                        options=[
                                            {'label': 'X axis', 'value': 'x'},
                                            {'label': 'Y axis', 'value': 'y'}, 
                                            {'label': 'Bubbles', 'value': 'z'}, 
                                        ],
                                        value=['x'],
                                        labelStyle={'display':'inline-block',"margin-left": "15px"},
                                        inputStyle={"margin-right": "10px"},
                                        style={'marginTop': 0},
                                        id='chklist-bubble-log',
                                    ),
                                ]),
                            ]),
                            
                        ]),
                    ], style={"marginTop": 10}),
                    
                    # loader for component refreshes
                    dcc.Loading(                        
                        type=INIT_LOADER_TYPE,
                        color=INIT_LOADER_CHART_COMPONENT_COLOR, #hex colour close match to nav bar ##515A5A
                        children=html.Span(id="my-loader-bubble-refresh"),
                        style={"zIndex":1, 'display': 'flex', 'vertical-align': 'center' , 'align-items': 'center', 'justify-content': 'center', 'paddingTop':50 },
                    ),
                    
                    dcc.Graph(id='bubble-graph',
                              #animate=False,
                              #animation_options={ 'frame': { 'redraw': True, }, 'transition': { 'duration': 500, 'ease': 'cubic-in-out', }, }, #working 95%, just doesn't resize the chart!! Need a way to mimic the double click javascript event to resize
                              #https://github.com/plotly/dash-core-components/blob/40a0d87479064e0f56286adac1c0493cf903d2b7/src/components/Graph.react.js#L71
                              #https://plotly.com/python/animations/
                              style={"backgroundColor": "#1a2d46", 'color': '#ffffff', 'height': INIT_BUBBLE_H },
                              config={'displayModeBar': False, 'responsive': True, 'autosizable': True },
                              ),
                ])),                           
                
                dbc.ModalFooter([
                    
                    #dbc.Row([                    
                    
                        #dbc.Col([    
                        html.Div([
                            #html.Span("Data source: "),
                            #html.Span(id='bubble-graph-modal-footer'),    
                            #html.Div(dcc.Link(href='', target="_blank", id="bubble-graph-modal-footer-link")),
                            html.Img(src='/static/img/bubblebobble1.png'), 
                            #dcc.Markdown(""" ![Image](bubblebobble1.png) """),
                            #'display': 'flex', 'vertical-align': 'top' , 'align-items': 'center', 'justify-content': 'center'
                            #dcc.Markdown(""" Built with ![Image](heart1.png) in Python using [Dash](https://plotly.com/dash/)."""),
                        ]),
                        #],width=3, style={'justify-content':'center', 'display':'flex','align-items': 'center'}),
                        
                        #dbc.Col([
                        html.Div([                            
                            dbc.Button("About", id='modal-bubble-guide-popover-target', color='info', className="mr-1", size=INIT_BUTTON_SIZE),
                            dbc.Button("Instructions", id='modal-bubble-instructions-popover-target', color='warning', className="mr-1", size=INIT_BUTTON_SIZE),
                            dbc.Button("Show Example", id='modal-bubble-examplebtn', color='light', className="mr-1", size=INIT_BUTTON_SIZE),
                            dbc.Button("Clear Chart", id='modal-bubble-resetbtn', color='light', className="mr-1", size=INIT_BUTTON_SIZE),
                            dbc.Button("Download", id='modal-bubble-download', color='success', className="mr-1", size=INIT_BUTTON_SIZE),
                            Download(id='download_dataset_bubble'),
                            dbc.Button("Close", id="modal-bubble-close", className="mr-1", size=INIT_BUTTON_SIZE),
                        ], className="ml-auto"),
                        #])
                    #]),
                    
                    dbc.Popover(
                        [
                            dbc.PopoverHeader("About", style={'fontWeight':'bold'}),
                            dbc.PopoverBody(hovertip_text.bubblegraph_about),
                        ],
                        #id="modal-bubble-guide-popover",
                        #is_open=False,
                        target="modal-bubble-guide-popover-target",
                        trigger="hover",
                        placement="top",
                        hide_arrow=False,
                        #style={"zIndex":1}
                    ),
                    
                    dbc.Popover(
                        [
                            dbc.PopoverHeader("Instructions", style={'fontWeight':'bold'}),
                            dbc.PopoverBody(hovertip_text.bubblegraph_instructions),
                        ],
                        #id="modal-bubble-instructions-popover",
                        #is_open=False,
                        target="modal-bubble-instructions-popover-target",
                        trigger="hover",
                        placement="top",
                        hide_arrow=False,
                        #style={"zIndex":1}
                    ),
                    
                    dbc.Popover(
                          [
                          dbc.PopoverHeader("Download format:", style={'fontWeight':'bold'}),
                          dbc.PopoverBody([
                              html.Div('Raw data'),
                              dbc.Button(".xlsx", outline=True, color="secondary", className="mr-1", id="btn-popover-bubble-download-xls", style={}, size=INIT_BUTTON_SIZE),
                              dbc.Button(".csv", outline=True, color="secondary", className="mr-1", id="btn-popover-bubble-download-csv", style={}, size=INIT_BUTTON_SIZE),
                              dbc.Button(".json", outline=True, color="secondary", className="mr-1", id="btn-popover-bubble-download-json", style={}, size=INIT_BUTTON_SIZE),
                              html.Div('Chart', style={'marginTop':5}),
                              dbc.Button(".pdf", outline=True, color="secondary", className="mr-1", id="btn-popover-bubble-download-pdf", style={}, size=INIT_BUTTON_SIZE),
                              dbc.Button(".png", outline=True, color="secondary", className="mr-1", id="btn-popover-bubble-download-png", style={}, size=INIT_BUTTON_SIZE),
                              dbc.Button(".svg", outline=True, color="secondary", className="mr-1", id="btn-popover-bubble-download-svg", style={}, size=INIT_BUTTON_SIZE),
                              dbc.Button(".jpg", outline=True, color="secondary", className="mr-1", id="btn-popover-bubble-download-jpg", style={}, size=INIT_BUTTON_SIZE),
                              html.Div('Advanced', style={'marginTop':5,'display':'none'}),
                              dbc.Button("Downloads Area", outline=True, color="secondary", className="mr-1", id="btn-popover-bubble-download-land", style={'display':'none'}, size=INIT_BUTTON_SIZE), 
                              ]),
                          ],
                          id="download-popover-bubble",                                        
                          target="modal-bubble-download",
                          #style={'maxHeight': '300px', 'overflowY': 'auto'},
                          trigger="legacy",
                          placement="top",
                          hide_arrow=False,
                          
                    ), 
                    
                ])
                
                
                
                
            ],
            id="dbc-modal-bubble",
            centered=True,
            size="xl",
            style={"max-width": "none", "width": INIT_BAR_BUBBLE_W} 
        )
    return m

def create_dash_layout_downloads_modal():
    m = dbc.Modal(
            [
                Download(id='download_object_downloads_modal'), 
                
                #dbc.ModalHeader(html.Div( /static/img/rainbow2.png) Download Land ![Image](/static/img/rainbow1.png) """), style={"fontFamily":INIT_MODAL_HEADER_FONT_GENERAL, "fontSize": INIT_MODAL_HEADER_FONT_SIZE, "fontWeight": INIT_MODAL_HEADER_FONT_WEIGHT }),
                dbc.ModalHeader(
                    html.Div([
                        html.Img(src='/static/img/rainbow2.png', width=50),
                        html.Div("Download Land", style={"fontFamily":INIT_MODAL_HEADER_FONT_GENERAL, "fontSize": INIT_MODAL_HEADER_FONT_SIZE, "fontWeight": INIT_MODAL_HEADER_FONT_WEIGHT, 'padding-left':20, 'padding-right':20 }),
                        html.Img(src='/static/img/rainbow1.png', width=50),  
                    ],style={'display':'flex', 'align-items': 'center', 'justify-content': 'center', 'background-color':'transparent'}),
                style={'background-color':'transparent', 'align-items':'center', 'justify-content': 'center'}
                    
                ),
                
                dbc.ModalBody([                    

                    dcc.Markdown(""" 
                        Welcome to a magical place where dreams come true. 
                        Here you can export larger chunks of data beyond what the other download buttons can do.
                        For example, you might want all available data just for two regions of the world, or all available data in a given year.
                        Please be aware the tools below are live-querying the main dataset and preparing a zipped comma-separated-value (CSV) file.                      To minimise file size and query load, I've stripped out source information. 
                        Please also note you are getting the raw series names as they originally came, and not my curated re-labelled series names.
                        This area is really intended for advanced users who are comfortable working with datasets larger than 100,000 rows.
                        
                        
                        #### How do you like your data sliced?
                    """),

                    dbc.Row([
                        dbc.Card(
                        [                            
                            dbc.CardHeader(html.H5("Series")),
                            dbc.CardBody([  
                                html.Div("Download all available data (i.e. all regions, all years) for the selected series."),
                                html.Br(),
                                dcc.Dropdown(
                                    options=[],
                                    id="downloads-series-selector",
                                    multi=True,
                                    placeholder='Select series',
                                ),
                                html.Br(),
                                dbc.Button("Download ZIP", size=INIT_BUTTON_SIZE, outline=True, active = True, color="success", id='btn-downloads-series'),                                
                            ]),
                        ],
                        style={"width": '100%', "marginBottom": 0, "marginTop": '1vw', "marginLeft": 0, "marginRight": '1vw'},
                        ),
                    ], style={"marginBottom": 0, "marginTop": 0, "marginLeft": 0, "marginRight": 0, }), #end row
                    
                    dbc.Row([
                     
                        dbc.Card(
                        [                            
                            dbc.CardHeader(html.H5("country/Region")),
                            dbc.CardBody([  
                                html.Div("Download all available data (i.e. all data series) for the selected countries."),
                                html.Br(),
                                dcc.Dropdown(
                                    options=[],
                                    id="downloads-countries-selector",
                                    multi=True,
                                    placeholder='Select countries',
                                ),
                                html.Br(),
                                dbc.Button("Download ZIP", size=INIT_BUTTON_SIZE, outline=True, active = True, color="success", id='btn-downloads-countries'),
                            ]),
                        ],
                        style={"width": INIT_SETTINGS_DL_CARD_WIDTH, "marginBottom": 0, "marginTop": '1vw', "marginLeft": 0, "marginRight": '1vw' },
                        ),                       
                        
                        
                        dbc.Card(
                        [
                            dbc.CardHeader(html.H5("year")),
                            dbc.CardBody([ 
                                html.Div("Download all available data (i.e. all data series, all regions) for the selected year(s)."),
                                html.Br(),
                                dcc.Dropdown(
                                    options=[],
                                    id="downloads-year-selector",
                                    multi=True,
                                    placeholder='Select years',
                                ),
                                html.Br(),
                                dbc.Button("Download ZIP", size=INIT_BUTTON_SIZE, outline=True, active = True, color="success", id='btn-downloads-years'),
                            ]),
                        ],
                        style={"width": INIT_SETTINGS_DL_CARD_WIDTH, "marginBottom": 0, "marginTop": '1vw', "marginLeft": 0, "marginRight": '1vw'},
                        ),

                        dbc.Card(
                        [                            
                            dbc.CardHeader(html.H5("Everything")),
                            dbc.CardBody([ 
                                html.Div("Download the entire dataset (2500+ series) as a zipped CSV. Advanced users only."),
                                html.Br(),
                                html.Div("Allow up to 1 min to process. TEMPORARILY DISABLED"),
                                html.Br(),
                                dbc.Button("Download ZIP (136MB)", size=INIT_BUTTON_SIZE, outline=True, active = True, color="success", id='btn-downloads-all-data', style={'padding-top':5}, disabled=True),
                            ]),
                        ],
                        style={"width": INIT_SETTINGS_DL_CARD_WIDTH,"marginBottom": 0, "marginTop": '1vw', "marginLeft": 0, "marginRight": '1vw' },
                        ),
                        
                        
                    ], style={"marginBottom": 0, "marginTop": 0, "marginLeft": 0, "marginRight": 0, }), #end row 

                    dcc.Loading(                            
                        type=INIT_LOADER_TYPE,
                        color=INIT_LOADER_CHART_COLOR, 
                        children=html.Span(id="my-spinner-dl-series"),
                        style={"zIndex":1, 'display': 'flex', 'vertical-align': 'center' , 'align-items': 'center', 'justify-content': 'center'},
                    ),

                                  
                dbc.Tooltip(
                        "Temporarily disabled to preserve server availability. Solution coming soon.",
                        target='btn-downloads-all-data',
                        placement='top',                        
                    ), 

                dbc.Tooltip(
                        "Click this button and wait patiently for download to start. Expect ~5s processing time per country selected.",
                        target='btn-downloads-countries',
                        placement='top',                        
                    ), 

                dbc.Tooltip(
                        "Click this button and wait patiently for download to start. Expect ~5s processing time per series selected.",
                        target='btn-downloads-series',
                        placement='top',                        
                    ), 
                
                dbc.Tooltip(
                        "Click this button and wait patiently for download to start. Expect ~5s processing time per year selected.",
                        target='btn-downloads-years',
                        placement='top',                        
                    ),

                





                ]),                  
                dbc.ModalFooter([
                    dbc.Button("Close", id="modal-downloads-close", className="ml-auto"),
                    ]), 
            ],
            id="dbc-modal-download-land",
            centered=True,
            size="xl",            
            style={"max-width": "none", "width": INIT_DL_MODAL_W, 'max-height': "100vh"} 
        )
    return m



def create_dash_layout_experiments_modal():
    m = dbc.Modal(
            [
                #dbc.ModalHeader(html.H1('Area 51')),
                dbc.ModalHeader(html.Div(
                    html.H1(id="xp-modal-title",style={"fontFamily":INIT_MODAL_HEADER_FONT_GENERAL, "fontSize": INIT_MODAL_HEADER_FONT_SIZE, "fontWeight": INIT_MODAL_HEADER_FONT_WEIGHT}),
                    ),style={'background-color':'transparent'}),

                dbc.ModalBody([                  
                    html.Div(id='xp-modal-body', style={'height': INIT_EXPERIMENT_H, 'background-color':'transparent',  },),
                ]), 
                
                #dbc.ModalFooter([   ]),
                
                
            ],
            id="dbc-modal-experiments",
            centered=True,
            #fullscreen=True,
            size="xl",
            style={"max-width": "none", "width": '80%', "height": '100%', } 
        )
    return m



def create_dash_layout_nav_footer():
    
    #Builds out the nav footer including all modals
    
    # Bottom navbar (buttons for now)
    nav_footer = html.Div(
        [                  
            #The button and slider column
            dbc.Row(
            #html.Div(
                [
                             
                    #Button column
                    dbc.Col(
                    #html.Div(

                            html.Div([                                     
                                  
                                  dbc.Row([                                                                 
                                  dbc.Button("USER GUIDE",  outline=INIT_BTN_OUTLINE, color="primary", className="mr-1", id="uguide-button", style={"marginRight": 0, "marginBottom": 10, 'display': 'inline-block', 'opacity':INIT_BUTTON_OPACITY, 'fontSize': INIT_NAVFOOTER_BTN_FONT }, size=INIT_BUTTON_SIZE),
                                  dbc.Button("SETTINGS", outline=INIT_BTN_OUTLINE, color="warning", className="mr-1", id="settings-button", style={"marginLeft": 0, "marginBottom": 10, 'display': 'inline-block', 'opacity':INIT_BUTTON_OPACITY, 'fontSize': INIT_NAVFOOTER_BTN_FONT}, size=INIT_BUTTON_SIZE),                                                                                                                                             
                                  dbc.Button("DOWNLOAD", outline=INIT_BTN_OUTLINE, color="success", className="mr-1", id="download-button", disabled=False, style={"marginLeft": 0, "marginBottom": 10, 'display': 'none', 'opacity':INIT_BUTTON_OPACITY, 'fontSize': INIT_NAVFOOTER_BTN_FONT}, size=INIT_BUTTON_SIZE), #disabled on initial
                                  Download(id='download_dataset_main'),                                  
                                  #dbc.Button("STAR TREK MODE", outline=INIT_BTN_OUTLINE, color="danger", className="mr-1", id="startrek-button", disabled=False, style={"marginLeft": 0, "marginBottom": 10, 'display': 'none', 'opacity':INIT_BUTTON_OPACITY}, size=INIT_BUTTON_SIZE), #disabled on initial
                                  dbc.Button("ABOUT", outline=INIT_BTN_OUTLINE, color="info", className="mr-1", id="about-button", style={"marginLeft": 0, "marginBottom": 10, 'display': 'inline-block', 'opacity':INIT_BUTTON_OPACITY, 'fontSize': INIT_NAVFOOTER_BTN_FONT}, size=INIT_BUTTON_SIZE),
                                  ]),
                                                               
                                  dbc.Row([                                  
                                  dbc.Button("BAR", outline=INIT_BTN_OUTLINE, color="dark", className="mr-1", id="bar-button", style={"marginLeft": 0, "marginBottom": 0, 'display': 'none', 'fontSize': INIT_NAVFOOTER_BTN_FONT}, size=INIT_BUTTON_SIZE), #disabled on initial 
                                  dbc.Button("LINE", outline=INIT_BTN_OUTLINE, color="dark", className="mr-1", id="line-button", style={"marginLeft": 0, "marginBottom": 0, 'display': 'none', 'fontSize': INIT_NAVFOOTER_BTN_FONT}, size=INIT_BUTTON_SIZE), #disabled on initial 
                                  dbc.Button("BUBBLE", outline=INIT_BTN_OUTLINE, color="dark", className="mr-1", id="bubble-button", style={"marginLeft": 0, "marginBottom": 0, 'display': 'none', 'fontSize': INIT_NAVFOOTER_BTN_FONT}, size=INIT_BUTTON_SIZE),
                                  dbc.Button("PIZZA", outline=INIT_BTN_OUTLINE, color="dark", className="mr-1", id='sunburst-button', style={"marginLeft": 0, "marginBottom": 0, 'display': 'none', 'fontSize': INIT_NAVFOOTER_BTN_FONT}, size=INIT_BUTTON_SIZE), #disabled on initial 
                                  dbc.Button("JIGSAW", outline=INIT_BTN_OUTLINE, color="dark", className="mr-1", id="geobar-button", style={"marginLeft": 0, "marginBottom": 0, 'display': 'none', 'fontSize': INIT_NAVFOOTER_BTN_FONT}, size=INIT_BUTTON_SIZE),
                                  dbc.Button("GLOBE", outline=INIT_BTN_OUTLINE, color="dark", className="mr-1", id="globe-button", style={"marginLeft": 0, "marginBottom": 0, 'display': 'none', 'fontSize': INIT_NAVFOOTER_BTN_FONT}, size=INIT_BUTTON_SIZE),
                                  ]),        
                               
                            ],
                            id = 'button-panel-style',
                            style = {'display': 'block', "marginLeft":"1vw" }, #I think this is needed somehow to make the secondary buttons wrap properly, it gets set to flexc
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
                          #style={'maxHeight': '300px', 'overflowY': 'auto'},
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
                    
                    
                    #Globe view modal                
                    create_dash_layout_globe_modal(),                    
                    
                    #Jigsaw view modal                
                    create_dash_layout_geobar_modal(),                    
                    
                    #Bar graph modal                     
                    create_dash_layout_bargraph_modal(),
                    
                    #Line graph modal                     
                    create_dash_layout_linegraph_modal(),
                    
                    #bubble graph modal                     
                    create_dash_layout_bubblegraph_modal(),
                    
                    #Sunburst Modal
                    create_dash_layout_sunburst_modal(),   
                    
                    #About modal
                    create_dash_layout_about_modal(),
                    
                    #User guide modal
                    create_dash_layout_userguide_modal(),
                    
                    #Settings modal
                    create_dash_layout_settings_modal(),

                    #Download land
                    create_dash_layout_downloads_modal(), 

                    #Experimental modal
                    create_dash_layout_experiments_modal(),                   
                    
                               
                    #year Slider Column
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
                            style={'display': 'none'}, #use only one style value, to udpate with callback (initially slider is invisible)
                        ),
                        ], 
                        style={"marginTop": 15, "marginLeft": 0, 'backgroundColor': 'transparent', 'width':'33%', 'display':'inline-block', 'minWidth':INIT_NAVFOOTER_COMPONENT_MINWIDTH}, #use col to move slider down
                        align='end',
                    ),
                    
                    #Data source column
                    dbc.Col(
                    #html.Div(

                        [
                              
                            html.Div([
                                html.Span("Data source: ", style={'fontSize':INIT_SOURCE_FONT}),
                                html.Span("No data selected", id="my-source", style={'fontSize':INIT_SOURCE_FONT}),
                                #html.Span(" "),
                                html.Div(dcc.Link(href='', target="_blank", id="my-source-link", style={'fontSize':INIT_SOURCE_FONT, 'color':'LightBlue'})),
                                #html.Span(")")
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
                    style = {'display': 'none'}, #default hidden 
                    align='end',               
                    
                    ),                                                      
                ],                
                #style={'display': 'flex', 'align-items': 'flex-end'}
                #style={'align-items': 'center', 'justify-content': 'center'}
                
            ),
            
            
        ],style={
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


def init_callbacks(dash_app):


    #COMPLETE INPUT LIST FOR MAIN CALLBACK
    def callback_main_create_inputs():
        #this should return the input chain for this callback
        
        c=[]
        
        #construct input triggers for timeslider and settings changes   
        c.append(Input("timeslider-hidden-div", "children"))
        #c.append(Input('geomap_figure', 'clickData'))
        c.append(Input('my-settings_json_store', 'data')) #these act purely as triggers after apply button pushed (like the hidden div), to call the main callback
        c.append(Input('my-settings_mapstyle_store', 'data')) #these act purely as triggers after apply button pushed (like the hidden div), to call the main callback
              
        # Don't fuck with this. Some odd parsing going on. Need to cast df to string and then back to numpy.Dash parser issue.
                
        # get all dataset ids from master config
        keysList = list(master_config_key_datasetid.keys())        
        df = pd.DataFrame(keysList, columns=['dataset_id'])
        df['dataset_id'] = df['dataset_id'].astype(str)
        ids=df['dataset_id'].to_numpy()     #critical   
               
        #recursively add input ids for all datasets in dataset_lkup
        for i in range(0,len(ids)):         
            c.append(Input(ids[i],"n_clicks"))                        
        #print(c)
        
        #add random button
        c.append(Input('random-button', "n_clicks"))
        
        #add search menu
        c.append(Input('nav-search-menu', 'value'))
        
        #add api
        c.append(Input('my-url-map-trigger', 'data'))        
        
        return c


    #Main callback for handling dataset selection change
    @dash_app.callback(
        [
            Output("my-series","data"),
            Output("my-series-label","data"),
            Output("geomap_figure", "figure"),
            Output("my-source", "children"),
            Output("my-source-link", "href"),         
            Output("download-button", "style"), #download button                         
            Output("bar-button", "style"),
            Output("line-button", "style"),
            Output("geobar-button", "style"),
            Output("sunburst-button", "style"),
            Output("globe-button", "style"),
            Output("bubble-button", "style"),        
            Output('my-year', "data"),
            Output('my-loader-main', "children"), #used to trigger loader. Use null string "" as output
            Output('button-panel-style', "style"), #used to hide initially
            Output('year-slider-style', "style"), #used to hide initially
            Output('data-source-style', 'style'), #used to hide initially         
            Output("year-slider", "max"),         
            Output("year-slider", "marks"),
            Output("year-slider", "value"),         
            Output("year-slider-title","style"),
            Output("year-slider-title","children"),
            Output("my-selection-m49", "data"), #NEW, to save the m49 location of the selected map
            #Output("my-series-data","data"),         
            Output("my-url-main-callback","data"), #to set url in another callback
            Output("my-url-bar-trigger", "data"),  # chain to bar
            Output("my-url-line-trigger", "data"), # chain to line
            Output("my-url-globe-trigger", "data"),# chain to globe
            Output("my-url-jigsaw-trigger", "data"),# chain to globe
            Output("source-popover","children"), #popover with explanatory notes
            Output("my-experimental-trigger", "data") #trigger for experimental modal  
        
        ],
        
        callback_main_create_inputs(), #build list of input items programmatically 
        
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
    #@cache.memoize(timeout=CACHE_TIMEOUT)
    def callback_main(*args):
        logger.info("MAIN CALLBACK")
        #print('GC threshold: ',gc.get_threshold())
        #print('GC count: ',gc.get_count())    
        
        #first check triggers and context 
        ctx = dash.callback_context 
        selection = ctx.triggered[0]["prop_id"].split(".")[0] #this is the series selection (component id from navbar top), except if the year slider is the trigger!!
        print("Selection triggered is", selection)
        
        # retrieve dcc component states from states dict
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
        search_query = states['my-url-path.data']              #api
        #maptrigger = states['my-url-map-trigger.data']  #api signal
        #url_view = states['my-url-view.data']  #api
        maptrigger = 'map'
        url_view = 'map' #override when necessary
        url_year = states['my-url-year.data']  #api        
        viewport = states['js-detected-viewport.data'] 
        logger.info('DETECTED VIEWPORT: %r x %r',viewport['width'], viewport['height'])           
        
        # special trigger for experimental data                
        experiment_trigger = "" # trigger for experiments (i.e. the power station globe)

        # load settings data: border 
        if settings_json is None: geojson = geojson_LOWRES                 
        else:             
            if int(settings_json) == 0: geojson = geojson_LOWRES
            elif int(settings_json)==1: geojson = geojson_MEDRES
            elif int(settings_json)==2: geojson = geojson_HIRES
        
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
            source = master_config[series].get("source") 
            link = master_config[series].get("link")    
            year = int(d.get_years(pop.loc[(pop['dataset_raw'] == series)])[year_slider_selected]) #expensive            
            
        
        #MAIN CALLBACK LOGIC pt1 (Determine what the event was)
        
        #MAP CLICK (PRESENTLY DISABLED: CHECK CALLBACK INPUT TO SWITCH BACK ON)
        if selection == "geomap_figure":
            #Grab some shit about the click data, yeeeh baby. We got some click data. We gonna do shit with it. Yeeh.
            selected_map_location = ctx.triggered[0]['value']['points'][0]['location'] #this is the M49 code of selected country
            selection_m49 = selected_map_location
            #logger.info("Map click detected. Click data is %r, location is %r.", ctx.triggered, selected_map_location)        
            #OK GOT THE STORE FOR SELECTION WORKING, CAN OUTPUT AND RETRIEVE FROM STATE. NEED TO RESOLVE LOGIC TO BUILD MAP WITH TRACE, PLUS NEW LOGIC TO SUBSET DF TO SELECTION + ALL YRS FOR country ETC.
            #MIGHT BE A BIT TRICKY. COULD POSSIBLY HAVE TO RETURN OUT OF MAIN CALLBACK HERES        
            #return series, create_map_geomap(pop, geojson, series, years[year], zoom, center, selected_map_location), d.get_source(logger, pop, series, years[year]), "https://www.google.com"
            #This still needs work
        
        #year SLIDER CHANGE
        elif selection == "timeslider-hidden-div":  
            # reset fonts
            for i in range(0,len(year_slider_marks)):
                year_slider_marks[str(i)]['style']['fontWeight']='normal'     
            year_slider_marks[str(year_slider_selected)]['style']['fontWeight']='bold'
            
            
        #SETTINGS CHANGE
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
                year_check = d.check_year(pop, series, year) #expensive
                if year_check == False:
                    print("year not found in dataset, breaking out of callback")
                    raise PreventUpdate()       
            else:
                # grab years and auto select most recent
                year_dict = d.get_years(pop.loc[(pop['dataset_raw'] == series)])
                year_index = list(year_dict)[-1]
                year = year_dict[year_index] 
                
            # update all vars        
            series_label = master_config[series].get("dataset_label")  
            source = master_config[series].get("source") 
            link = master_config[series].get("link")    
            year_slider_marks = d.get_year_slider_marks(series, pop, INIT_year_SLIDER_FONTSIZE, INIT_year_SLIDER_FONTCOLOR, year_slider_selected)
            year_slider_max = len(year_slider_marks)-1                        
            year_slider_selected = d.get_year_slider_index(pop, series, year)
            year_slider_marks[year_slider_selected]['style']['fontWeight']='bold' #mark selected year bold          
        
        
        #NAVBAR SELECTION
        else:
            #New dataset is selected, query available years and rebuild year slider vals        
            #logger.info("Main callback: navbar selection logic, or search pressed") 
                   
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
            year_dict = d.get_years(pop.loc[(pop['dataset_raw'] == series)])
            
            # it the datasets has data in at least 1 year, set the year slider
            if len(year_dict) > 0:
                year_index = list(year_dict)[-1]
                year = year_dict[year_index] #what is returned
                year_slider_marks = d.get_year_slider_marks(series, pop, INIT_year_SLIDER_FONTSIZE, INIT_year_SLIDER_FONTCOLOR, year_slider_selected)
                year_slider_max = len(year_slider_marks)-1
                year_slider_selected = year_slider_max #select the most recent year by default
                year_slider_marks[year_slider_selected]['style']['fontWeight']='bold' #mark selected year bold          
            
        #MAIN CALLBACK LOGIC Pt2 (Get ready to return) 
                        
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
        
        return \
        series, series_label, \
        create_map_geomap(df, geojson, series, zoom, center, selected_map_location, mapstyle, colorbarstyle, settings_colorpalette_reverse), \
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



    # Receive URL path from variouos inputs
    @dash_app.callback(               
                [
                Output('url', 'href'),
                Output('js-social-share-refresh','children'),
                ],
                [
                Input("my-url-main-callback","data"),
                Input("my-url-bar-callback","data"),
                Input("my-url-line-callback","data"),
                Input("my-url-globe-callback","data"),
                Input("my-url-jigsaw-callback","data"),
                
                
                ],  
                prevent_initial_call=True)
    def callback_api_set_URL(url_maincb, url_bar, url_line, url_globe, url_jigsaw):    
        
        # determine each input trigger, and return the relevant URL    
        ctx = dash.callback_context 
        trigger = ctx.triggered[0]["prop_id"].split(".")[0] #this is the series selection (component id from navbar top), except if the year slider is the trigger!!
        #print("URL Update. URL trigger:",trigger)
            
        
        if trigger == 'my-url-main-callback': return url_maincb, url_maincb
        elif trigger == 'my-url-bar-callback': return url_bar, url_bar
        elif trigger == 'my-url-line-callback': return url_line, url_line
        elif trigger == 'my-url-globe-callback': return url_globe, url_line
        elif trigger == 'my-url-jigsaw-callback': return url_jigsaw, url_jigsaw        
        
        return None
    


        
        
    # Detect URL change, and chain to other callbacks   
    @dash_app.callback([
                Output("my-url-root", 'data'), 
                Output("my-url-path", 'data'),            
                Output("my-url-series", 'data'),
                Output("my-url-year", 'data'),
                Output("my-url-view", 'data'),   
                Output("my-url-map-trigger", "data"),                
                ],
                [
                Input('url', 'href'),               
                ], 
                State('url', 'pathname'),              
                prevent_initial_call=True)
    def callback_api_get_URL(href, pathname):
        
        # root/series/year/view    
        
        # get root path
        blah = href.split('/') 
        root = blah[0]+'//'+blah[2]+'/'             
        
        #rint('pathname: ',pathname) 
        #print('href: ',href)  
        #print('blah: ',blah)  
        #print('root: ',root)         

        # condition on first load (root path). Avoid key error if assigning series/year/view to None
        if len(blah) == 4:
            #print('FIRST LOAD DETECTED')
            series = ""
            year = ""
            view = ""
          
        # all other conditions we want a path
        else:
            series = blah[3]
            year = blah[4]
            view = blah[5]            
        
        #print("root:",root,"\nseries:",series,"\nyear:",year,"\nview:",view)
        
        # now set signal logic
        if view == 'map': maptrigger = 'map'      
        elif view == 'bar': maptrigger = 'bar'
        elif view == 'line': maptrigger = 'line'
        elif view == 'globe': maptrigger = 'globe'
        elif view == 'jigsaw': maptrigger = 'jigsaw'
        else: maptrigger = ''   
        
        #special pathname check (fix bug when loading from url path and not root. Path seemed to get stuck on original url)
        path_chk = '/'+series+'/'+year+'/'+view
        #print('path check ', path_chk)
        if pathname != '/':
            #print('Path is not /')
            if pathname != path_chk:
                #print('Path check discrepancy, resetting path')
                pathname = '/'

        return root, pathname, series, year, view, maptrigger





    



    '''
    #Map click data
    @dash_app.callback(Output('map-zone', 'data'),
                Input('geomap_figure', 'clickData'),
                #State('zone', 'data'),
                prevent_initial_call=True)
    def map_selection(click_data_geomap):

        # What triggered the callback
        trg = dash.callback_context.triggered
        

    # if trg is not None:
            
        zone_name = trg[0]['value']['points'][0]['location']
        zone = 4 #zone_name_to_index[zone_name]  #need to work this shit out and reverese engineer for my purposes.

        # if click_data_geomap is not None:
        #     zone_name = click_data_geomap['points'][0]['location']
        #     zone = zone_name_to_index[zone_name]
        
        logger.info('Interaction: Geomap clicked. Click data is %r, inferred zone name is %r', trg, zone_name)
        #in theory, this callback can be integrated into the main one. But keep it separate for testing here.
        return zone
    '''

    #COMPLETE OUTPUT LIST FOR SETTINGS CALLBACK
    def callback_settings_create_outputs():
        #this should return the Output('blah', "active") style
            
        c=[]
        
        #First add border and map style button outputs
        c.append(Output('settingsbtn-resolution-low', "active"))
        c.append(Output('settingsbtn-resolution-med', "active"))
        c.append(Output('settingsbtn-resolution-high', "active"))     
        c.append(Output('settingsbtn-mapstyle-openstreetmap', "active"))
        c.append(Output('settingsbtn-mapstyle-carto-positron', "active"))
        c.append(Output('settingsbtn-mapstyle-darkmatter', "active"))
        c.append(Output('settingsbtn-mapstyle-stamen-terrain', "active"))
        c.append(Output('settingsbtn-mapstyle-stamen-toner', "active"))
        c.append(Output('settingsbtn-mapstyle-stamen-watercolor', "active"))
        
        #Add the coloscale outputs    
        for i in geomap_colorscale:
            c.append(Output(i,"active"))
        
        #Add reverse toggles
        c.append(Output('settingsbtn-reverse-colorscale', "active"))
        c.append(Output('settingsbtn-normal-colorscale', "active"))    
    
        #print(c)
        return c


    #COMPLETE INPUT LIST FOR SETTINGS CALLBACK
    def callback_settings_create_inputs():
        #returns the input chain for this callback
        
        c=[]
        
        c.append(Input('settingsbtn-resolution-low', "n_clicks"))
        c.append(Input('settingsbtn-resolution-med', "n_clicks"))
        c.append(Input('settingsbtn-resolution-high', "n_clicks"))     
        c.append(Input('settingsbtn-mapstyle-openstreetmap', "n_clicks"))
        c.append(Input('settingsbtn-mapstyle-carto-positron', "n_clicks"))
        c.append(Input('settingsbtn-mapstyle-darkmatter', "n_clicks"))
        c.append(Input('settingsbtn-mapstyle-stamen-terrain', "n_clicks"))
        c.append(Input('settingsbtn-mapstyle-stamen-toner', "n_clicks"))
        c.append(Input('settingsbtn-mapstyle-stamen-watercolor', "n_clicks"))    
        c.append(Input("dbc-modal-settings", "is_open")) #bool for understanding if modal has just been opened
        
        for i in geomap_colorscale:         
            c.append(Input(i,"n_clicks"))                        
        #print(c)
        
        #Add reverse button
        c.append(Input('settingsbtn-reverse-colorscale', "n_clicks"))
        c.append(Input('settingsbtn-normal-colorscale', "n_clicks"))
        
        return c
        
    #COMPLETE STATE LIST FOR SETTINGS CALLBACK
    def callback_settings_create_states():
        
        c=[]
        
        #first add all other states for buttons and stores
        c.append(State('settingsbtn-resolution-low', "active")) 
        c.append(State('settingsbtn-resolution-med', "active"))
        c.append(State('settingsbtn-resolution-high', "active"))    
        c.append(State('settingsbtn-mapstyle-openstreetmap', "active"))
        c.append(State('settingsbtn-mapstyle-carto-positron', "active"))
        c.append(State('settingsbtn-mapstyle-darkmatter', "active"))
        c.append(State('settingsbtn-mapstyle-stamen-terrain', "active"))
        c.append(State('settingsbtn-mapstyle-stamen-toner', "active"))
        c.append(State('settingsbtn-mapstyle-stamen-watercolor', "active"))
        c.append(State('my-settings_json_store', 'data'))
        c.append(State('my-settings_mapstyle_store', 'data'))
        c.append(State("my-settings_colorbar_store", 'data'))
        c.append(State("my-settings_colorbar_reverse_store", 'data'))

        #Add the coloscale states    
        for i in geomap_colorscale:
            c.append(State(i,"active"))
        #print(c)
        
        #Add reverse button
        c.append(State('settingsbtn-reverse-colorscale', "active"))
        c.append(State('settingsbtn-normal-colorscale', "active"))
        
        return c 


    #Settings modal button logic
    @dash_app.callback(   
        
        callback_settings_create_outputs(), 
        
        callback_settings_create_inputs(),    
        
        callback_settings_create_states(),
            
        prevent_initial_call=True,
    )
    def callback_settings(nbtn_low, nbtn_med, nbtn_high, 
                                nbtn_ms_1, nbtn_ms_2, nbtn_ms_3, nbtn_ms_4, nbtn_ms_5, nbtn_ms_6,
                                settings_modal_open,
                                nc1, nc2, nc3, nc4, nc5, nc6, nc7, nc8, nc9, nc10, nc11, nc12, nc13, nc14, nc15, nc16, nc17, nc18, nc19, nc20, nc21, nc22, nc23, nc24, nc25, nc26, nc27, nc28, nc29, nc30, nc31, nc32, nc33, nc34, nc35, nc36, nc37, nc38, nc39, nc40, nc41, nc42, nc43, nc44, nc45, nc46, nc47, nc48, nc49, nc50, nc51, nc52, nc53, nc54, nc55, nc56, nc57, nc58, nc59, nc60, nc61, nc62, nc63, nc64, nc65, nc66, nc67, nc68, nc69, nc70, nc71, nc72, nc73, nc74, nc75, nc76, nc77, nc78, nc79, nc80, nc81, nc82, nc83, nc84, nc85, nc86, nc87, nc88, nc89, nc90, nc91, nc92, nc93, \
                                nbtn_reverse, nbtn_normal,
                                btn_low_active, btn_med_active, btn_high_active,
                                btn_openstreetmap_active, btn_cartopositron_active, btn_darkmatter_active, btn_stamenterrain_active, btn_stamentoner_active, btn_stamenwatercolor_active,                             
                                settings_json_store, settings_mapstyle_store, settings_colorbar_store, settings_colorbar_reverse_store,
                                nc1a, nc2a, nc3a, nc4a, nc5a, nc6a, nc7a, nc8a, nc9a, nc10a, nc11a, nc12a, nc13a, nc14a, nc15a, nc16a, nc17a, nc18a, nc19a, nc20a, nc21a, nc22a, nc23a, nc24a, nc25a, nc26a, nc27a, nc28a, nc29a, nc30a, nc31a, nc32a, nc33a, nc34a, nc35a, nc36a, nc37a, nc38a, nc39a, nc40a, nc41a, nc42a, nc43a, nc44a, nc45a, nc46a, nc47a, nc48a, nc49a, nc50a, nc51a, nc52a, nc53a, nc54a, nc55a, nc56a, nc57a, nc58a, nc59a, nc60a, nc61a, nc62a, nc63a, nc64a, nc65a, nc66a, nc67a, nc68a, nc69a, nc70a, nc71a, nc72a, nc73a, nc74a, nc75a, nc76a, nc77a, nc78a, nc79a, nc80a, nc81a, nc82a, nc83a, nc84a, nc85a, nc86a, nc87a, nc88a, nc89a, nc90a, nc91a, nc92a, nc93a, \
                                btn_reverse_active, btn_normal_active
                                ):
        
        #Interrogate the trigger event to handle logic
        ctx = dash.callback_context 
        selection = ctx.triggered[0]["prop_id"].split(".")[0]      
        
        #logger.info("SETTINGS MODAL TRIGGER IS %r", selection)
        #logger.info("SETTINGS MODAL BUTTON STATEsS %r, btn low %r, btn med %r, btn high %r, map 1 %r, map 2 %r, map3 %r, map4 %r, map5, %r, map6, %r.", selection, btn_low_active, btn_med_active, btn_high_active, btn_openstreetmap_active, btn_cartopositron_active, btn_darkmatter_active, btn_stamenterrain_active, btn_stamentoner_active, btn_stamenwatercolor_active)
        
        #Toggle Resolution logic    
        if selection == 'settingsbtn-resolution-low' or selection == 'settingsbtn-resolution-med' or selection == 'settingsbtn-resolution-high':
            
            print("resolution button push detected")
            
            #override button active 'state' based on the actual selection
            if selection == 'settingsbtn-resolution-low':
                print("button low pushed")
                btn_low_active = True
                btn_med_active = False
                btn_high_active = False 
            
            elif selection == 'settingsbtn-resolution-med': 
                print("button med pushed")
                btn_low_active = False
                btn_med_active = True
                btn_high_active = False        
            
            elif selection == 'settingsbtn-resolution-high': 
                print("button high pushed")
                btn_low_active = False
                btn_med_active = False
                btn_high_active = True        
            
            else:
                print("Error with resolution button logic.")
                
        
        #Toggle reverse colorscale button logic
        elif selection == 'settingsbtn-reverse-colorscale' or selection == 'settingsbtn-normal-colorscale':
            #override active state based on the user click logic
            if selection == 'settingsbtn-reverse-colorscale':
                btn_reverse_active = True
                btn_normal_active = False
            elif selection == 'settingsbtn-normal-colorscale':
                btn_reverse_active = False
                btn_normal_active = True
        
        
        #Toggle Map style logic
        elif selection == 'settingsbtn-mapstyle-openstreetmap' or selection == 'settingsbtn-mapstyle-carto-positron' or selection == 'settingsbtn-mapstyle-darkmatter' or selection == 'settingsbtn-mapstyle-stamen-terrain' or selection =='settingsbtn-mapstyle-stamen-toner' or selection == 'settingsbtn-mapstyle-stamen-watercolor':
            
            #logger.info("We have movement. Repeat, we have moevement.")
            
            #override button active 'state' based on the actual selection
            if selection == 'settingsbtn-mapstyle-openstreetmap':
                    print("Btn open street map pushed bitch")
                    btn_openstreetmap_active = True
                    btn_cartopositron_active = False
                    btn_darkmatter_active = False
                    btn_stamenterrain_active = False
                    btn_stamentoner_active = False
                    btn_stamenwatercolor_active = False
                
            elif selection == 'settingsbtn-mapstyle-carto-positron':
                    print("Btn carto positron bitch")
                    btn_openstreetmap_active = False
                    btn_cartopositron_active = True
                    btn_darkmatter_active = False
                    btn_stamenterrain_active = False
                    btn_stamentoner_active = False
                    btn_stamenwatercolor_active = False
                    
            elif selection == 'settingsbtn-mapstyle-darkmatter':
                    print("Btn dark hoe")
                    btn_openstreetmap_active = False
                    btn_cartopositron_active = False
                    btn_darkmatter_active = True
                    btn_stamenterrain_active = False
                    btn_stamentoner_active = False
                    btn_stamenwatercolor_active = False
                    
            elif selection == 'settingsbtn-mapstyle-stamen-terrain':
                    logger.info("Btn stamen terran yeeeeh")
                    btn_openstreetmap_active = False
                    btn_cartopositron_active = False
                    btn_darkmatter_active = False
                    btn_stamenterrain_active = True
                    btn_stamentoner_active = False
                    btn_stamenwatercolor_active = False
                    
            elif selection == 'settingsbtn-mapstyle-stamen-toner':
                    print("Btn stamen toner!")
                    btn_openstreetmap_active = False
                    btn_cartopositron_active = False
                    btn_darkmatter_active = False
                    btn_stamenterrain_active = False
                    btn_stamentoner_active = True
                    btn_stamenwatercolor_active = False
                    
            elif selection == 'settingsbtn-mapstyle-stamen-watercolor':
                    print("Btn dark hoe")
                    btn_openstreetmap_active = False
                    btn_cartopositron_active = False
                    btn_darkmatter_active = False
                    btn_stamenterrain_active = False
                    btn_stamentoner_active = False
                    btn_stamenwatercolor_active = True

            else:
                print("SOmething baddd happened. Also I've been drinking. Just fyi in case this error ever comes up...")
        
        elif selection == "dbc-modal-settings":
            #this triggers on load (true), and in clicking out (close) or apply button, where it is set to (false) and visible here in last run through. It's the change of state that actually triggers this logic.
            #logger.info("SETTINGS MODAL CB: detected change in settings modal open/closed state. TRUE = settings modal has been opened, FALSE = user clicked out, or clicked apply. value:%r", settings_modal_open)
            if settings_modal_open == True:
                #modal has just opened so load defaults by checking if anything stored, if not, set to default
                
                #logger.info("SPECIAL TEST: settings modal load, acaheck store for val or set default. Store val is %r", settings_json_store)
                
                #BORDER RESOLUTION
                if settings_json_store is None:            
                    #no json store has been created so set button states to defaults! (i.e. no settings have been apply-saved yet)
                    btn_low_active = True
                    btn_med_active = False
                    btn_high_active = False             
                    
                elif int(settings_json_store) == 0:                
                    btn_low_active = True
                    btn_med_active = False
                    btn_high_active = False
                    
                elif int(settings_json_store) == 1:                
                    btn_low_active = False
                    btn_med_active = True
                    btn_high_active = False   
                    
                elif int(settings_json_store) == 2:                
                    btn_low_active = False
                    btn_med_active = False
                    btn_high_active = True
                    
                #MAPSTYLE
                if settings_mapstyle_store is None:
                    #no json store, so set to default
                    btn_openstreetmap_active = False
                    btn_cartopositron_active = True
                    btn_darkmatter_active = False
                    btn_stamenterrain_active = False
                    btn_stamentoner_active = False
                    btn_stamenwatercolor_active = False
                
                elif int(settings_mapstyle_store) == 0:
                    btn_openstreetmap_active = True
                    btn_cartopositron_active = False
                    btn_darkmatter_active = False
                    btn_stamenterrain_active = False
                    btn_stamentoner_active = False
                    btn_stamenwatercolor_active = False
                    
                elif int(settings_mapstyle_store) == 1:
                    btn_openstreetmap_active = False
                    btn_cartopositron_active = True
                    btn_darkmatter_active = False
                    btn_stamenterrain_active = False
                    btn_stamentoner_active = False
                    btn_stamenwatercolor_active = False
                
                elif int(settings_mapstyle_store) == 2:
                    btn_openstreetmap_active = False
                    btn_cartopositron_active = False
                    btn_darkmatter_active = True
                    btn_stamenterrain_active = False
                    btn_stamentoner_active = False
                    btn_stamenwatercolor_active = False    
                    
                elif int(settings_mapstyle_store) == 3:
                    btn_openstreetmap_active = False
                    btn_cartopositron_active = False
                    btn_darkmatter_active = False
                    btn_stamenterrain_active = True
                    btn_stamentoner_active = False
                    btn_stamenwatercolor_active = False
                    
                elif int(settings_mapstyle_store) == 4:
                    btn_openstreetmap_active = False
                    btn_cartopositron_active = False
                    btn_darkmatter_active = False
                    btn_stamenterrain_active = False
                    btn_stamentoner_active = True
                    btn_stamenwatercolor_active = False
                
                elif int(settings_mapstyle_store) == 5:
                    btn_openstreetmap_active = False
                    btn_cartopositron_active = False
                    btn_darkmatter_active = False
                    btn_stamenterrain_active = False
                    btn_stamentoner_active = False
                    btn_stamenwatercolor_active = True
                
                #COLORBAR
                #logger.info("settings store for reverse color is %r", settings_colorbar_reverse_store)            
                if settings_colorbar_reverse_store is None:
                    btn_reverse_active = INIT_COLOR_PALETTE_REVERSE
                    btn_normal_active = not INIT_COLOR_PALETTE_REVERSE            
                if settings_colorbar_reverse_store is True:                
                    btn_reverse_active = True
                    btn_normal_active = False
                elif settings_colorbar_reverse_store is False:                
                    btn_reverse_active = False
                    btn_normal_active = True
                
                #Could have If clauses here to catch and set the stored color scheme but the log will mean a ridiculous number of rows. And it's not super important.
                
            else: #settings_modal_open == False:
                #modal has been clicked out of, or apply button pushed. So it has closed. Reset all buttons to default. Dirty, should also leave as the current store vars...but meh
                btn_low_active = True
                btn_med_active = False
                btn_high_active = False             
                btn_openstreetmap_active = True
                btn_cartopositron_active = False
                btn_darkmatter_active = False
                btn_stamenterrain_active = False
                btn_stamentoner_active = False
                btn_stamenwatercolor_active = False
                btn_reverse_active = INIT_COLOR_PALETTE_REVERSE
                btn_normal_active = not INIT_COLOR_PALETTE_REVERSE 
        
        else:
            print("Settings Callback: Input detected for colorpallete, setting active state for palette:",selection)
            
            #set all to false
            nc1a=False
            nc2a=False
            nc3a=False
            nc4a=False
            nc5a=False
            nc6a=False
            nc7a=False
            nc8a=False
            nc9a=False
            nc10a=False
            nc11a=False
            nc12a=False
            nc13a=False
            nc14a=False
            nc15a=False
            nc16a=False
            nc17a=False
            nc18a=False
            nc19a=False
            nc20a=False
            nc21a=False
            nc22a=False
            nc23a=False
            nc24a=False
            nc25a=False
            nc26a=False
            nc27a=False
            nc28a=False
            nc29a=False
            nc30a=False
            nc31a=False
            nc32a=False
            nc33a=False
            nc34a=False
            nc35a=False
            nc36a=False
            nc37a=False
            nc38a=False
            nc39a=False
            nc40a=False
            nc41a=False
            nc42a=False
            nc43a=False
            nc44a=False
            nc45a=False
            nc46a=False
            nc47a=False
            nc48a=False
            nc49a=False
            nc50a=False
            nc51a=False
            nc52a=False
            nc53a=False
            nc54a=False
            nc55a=False
            nc56a=False
            nc57a=False
            nc58a=False
            nc59a=False
            nc60a=False
            nc61a=False
            nc62a=False
            nc63a=False
            nc64a=False
            nc65a=False
            nc66a=False
            nc67a=False
            nc68a=False
            nc69a=False
            nc70a=False
            nc71a=False
            nc72a=False
            nc73a=False
            nc74a=False
            nc75a=False
            nc76a=False
            nc77a=False
            nc78a=False
            nc79a=False
            nc80a=False
            nc81a=False
            nc82a=False
            nc83a=False
            nc84a=False
            nc85a=False
            nc86a=False
            nc87a=False
            nc88a=False
            nc89a=False
            nc90a=False
            nc91a=False
            nc92a=False
            nc93a=False
            
            #conditional ifs 
            if selection == "auto":
                nc1a=True
            elif selection == "aggrnyl":
                nc2a=True
            elif selection == "agsunset":
                nc3a=True
            elif selection == "algae":
                nc4a=True
            elif selection == "amp":
                nc5a=True
            elif selection == "armyrose":
                nc6a=True
            elif selection == "balance":
                nc7a=True
            elif selection == "blackbody":
                nc8a=True
            elif selection == "bluered":
                nc9a=True
            elif selection == "blues":
                nc10a=True
            elif selection == "blugrn":
                nc11a=True
            elif selection == "bluyl":
                nc12a=True
            elif selection == "brbg":
                nc13a=True
            elif selection == "brwnyl":
                nc14a=True
            elif selection == "bugn":
                nc15a=True
            elif selection == "bupu":
                nc16a=True
            elif selection == "burg":
                nc17a=True
            elif selection == "burgyl":
                nc18a=True
            elif selection == "cividis":
                nc19a=True
            elif selection == "curl":
                nc20a=True
            elif selection == "darkmint":
                nc21a=True
            elif selection == "deep":
                nc22a=True
            elif selection == "delta":
                nc23a=True
            elif selection == "dense":
                nc24a=True
            elif selection == "earth":
                nc25a=True
            elif selection == "edge":
                nc26a=True
            elif selection == "electric":
                nc27a=True
            elif selection == "emrld":
                nc28a=True
            elif selection == "fall":
                nc29a=True
            elif selection == "geyser":
                nc30a=True
            elif selection == "gnbu":
                nc31a=True
            elif selection == "gray":
                nc32a=True
            elif selection == "greens":
                nc33a=True
            elif selection == "greys":
                nc34a=True
            elif selection == "haline":
                nc35a=True
            elif selection == "hot":
                nc36a=True
            elif selection == "hsv":
                nc37a=True
            elif selection == "ice":
                nc38a=True
            elif selection == "icefire":
                nc39a=True
            elif selection == "inferno":
                nc40a=True
            elif selection == "jet":
                nc41a=True
            elif selection == "magenta":
                nc42a=True
            elif selection == "magma":
                nc43a=True
            elif selection == "matter":
                nc44a=True
            elif selection == "mint":
                nc45a=True
            elif selection == "mrybm":
                nc46a=True
            elif selection == "mygbm":
                nc47a=True
            elif selection == "oranges":
                nc48a=True
            elif selection == "orrd":
                nc49a=True
            elif selection == "oryel":
                nc50a=True
            elif selection == "peach":
                nc51a=True
            elif selection == "phase":
                nc52a=True
            elif selection == "picnic":
                nc53a=True
            elif selection == "pinkyl":
                nc54a=True
            elif selection == "piyg":
                nc55a=True
            elif selection == "plasma":
                nc56a=True
            elif selection == "plotly3":
                nc57a=True
            elif selection == "portland":
                nc58a=True
            elif selection == "prgn":
                nc59a=True
            elif selection == "pubu":
                nc60a=True
            elif selection == "pubugn":
                nc61a=True
            elif selection == "puor":
                nc62a=True
            elif selection == "purd":
                nc63a=True
            elif selection == "purp":
                nc64a=True
            elif selection == "purples":
                nc65a=True
            elif selection == "purpor":
                nc66a=True
            elif selection == "rainbow":
                nc67a=True
            elif selection == "rdbu":
                nc68a=True
            elif selection == "rdgy":
                nc69a=True
            elif selection == "rdpu":
                nc70a=True
            elif selection == "rdylbu":
                nc71a=True
            elif selection == "rdylgn":
                nc72a=True
            elif selection == "redor":
                nc73a=True
            elif selection == "reds":
                nc74a=True
            elif selection == "solar":
                nc75a=True
            elif selection == "spectral":
                nc76a=True
            elif selection == "speed":
                nc77a=True
            elif selection == "sunset":
                nc78a=True
            elif selection == "sunsetdark":
                nc79a=True
            elif selection == "teal":
                nc80a=True
            elif selection == "tealgrn":
                nc81a=True
            elif selection == "tealrose":
                nc82a=True
            elif selection == "tempo":
                nc83a=True
            elif selection == "temps":
                nc84a=True
            elif selection == "thermal":
                nc85a=True
            elif selection == "tropic":
                nc86a=True
            elif selection == "turbid":
                nc87a=True
            elif selection == "twilight":
                nc88a=True
            elif selection == "viridis":
                nc89a=True
            elif selection == "ylgn":
                nc90a=True
            elif selection == "ylgnbu":
                nc91a=True
            elif selection == "ylorbr":
                nc92a=True
            elif selection == "ylorrd":
                nc93a=True     
            

        return btn_low_active, btn_med_active, btn_high_active, btn_openstreetmap_active, btn_cartopositron_active, btn_darkmatter_active, btn_stamenterrain_active, btn_stamentoner_active, btn_stamenwatercolor_active, \
            nc1a, nc2a, nc3a, nc4a, nc5a, nc6a, nc7a, nc8a, nc9a, nc10a, nc11a, nc12a, nc13a, nc14a, nc15a, nc16a, nc17a, nc18a, nc19a, nc20a, nc21a, nc22a, nc23a, nc24a, nc25a, nc26a, nc27a, nc28a, nc29a, nc30a, nc31a, nc32a, nc33a, nc34a, nc35a, nc36a, nc37a, nc38a, nc39a, nc40a, nc41a, nc42a, nc43a, nc44a, nc45a, nc46a, nc47a, nc48a, nc49a, nc50a, nc51a, nc52a, nc53a, nc54a, nc55a, nc56a, nc57a, nc58a, nc59a, nc60a, nc61a, nc62a, nc63a, nc64a, nc65a, nc66a, nc67a, nc68a, nc69a, nc70a, nc71a, nc72a, nc73a, nc74a, nc75a, nc76a, nc77a, nc78a, nc79a, nc80a, nc81a, nc82a, nc83a, nc84a, nc85a, nc86a, nc87a, nc88a, nc89a, nc90a, nc91a, nc92a, nc93a, \
                btn_reverse_active, btn_normal_active
    

    #COMPLETE STATE LIST FOR SETTINGS APPLY CALLBACK
    def callback_settings_modal_apply_create_states():
        
        c = []
        
        #first add other states required
        c.append(State('settingsbtn-resolution-low', "active")) 
        c.append(State('settingsbtn-resolution-med', "active"))
        c.append(State('settingsbtn-resolution-high', "active"))    
        c.append(State('settingsbtn-mapstyle-openstreetmap', "active"))
        c.append(State('settingsbtn-mapstyle-carto-positron', "active"))
        c.append(State('settingsbtn-mapstyle-darkmatter', "active"))
        c.append(State('settingsbtn-mapstyle-stamen-terrain', "active"))
        c.append(State('settingsbtn-mapstyle-stamen-toner', "active"))
        c.append(State('settingsbtn-mapstyle-stamen-watercolor', "active"))
        
        #now add colorscale states
        for i in geomap_colorscale:
            c.append(State(i,"active"))
        #print(c)
        
        #Add reverse button
        c.append(State('settingsbtn-reverse-colorscale', "active"))
        c.append(State('settingsbtn-normal-colorscale', "active"))
        
        return c


    #Settings modal apply button trigger 
    @dash_app.callback(                      
        [    
        Output('my-settings_json_store', 'data'),
        Output('my-settings_mapstyle_store', 'data'),
        Output("my-settings_colorbar_store", 'data'),
        Output('my-settings_colorbar_reverse_store', 'data'),
        ],
        Input("modal-settings-apply", "n_clicks"),
        
        callback_settings_modal_apply_create_states(),
        
        prevent_initial_call=True,
    )
    def callback_settings_modal_apply(n1,
                                    btn_low_active, btn_med_active, btn_high_active,
                                    btn_openstreetmap_active, btn_cartopositron_active, btn_darkmatter_active, btn_stamenterrain_active, btn_stamentoner_active, btn_stamenwatercolor_active,
                                    nc1a, nc2a, nc3a, nc4a, nc5a, nc6a, nc7a, nc8a, nc9a, nc10a, nc11a, nc12a, nc13a, nc14a, nc15a, nc16a, nc17a, nc18a, nc19a, nc20a, nc21a, nc22a, nc23a, nc24a, nc25a, nc26a, nc27a, nc28a, nc29a, nc30a, nc31a, nc32a, nc33a, nc34a, nc35a, nc36a, nc37a, nc38a, nc39a, nc40a, nc41a, nc42a, nc43a, nc44a, nc45a, nc46a, nc47a, nc48a, nc49a, nc50a, nc51a, nc52a, nc53a, nc54a, nc55a, nc56a, nc57a, nc58a, nc59a, nc60a, nc61a, nc62a, nc63a, nc64a, nc65a, nc66a, nc67a, nc68a, nc69a, nc70a, nc71a, nc72a, nc73a, nc74a, nc75a, nc76a, nc77a, nc78a, nc79a, nc80a, nc81a, nc82a, nc83a, nc84a, nc85a, nc86a, nc87a, nc88a, nc89a, nc90a, nc91a, nc92a, nc93a,
                                    btn_reverse_active, btn_normal_active
                                    ):
        #This callback must be separate as year slider is created from main callback, so this acts as a trigger for the main
        #logger.info("Settings APPLY button detected, trigger main callback")
        
        #logger.info("Settings APPLY BUTTON DETECTED. values are btn low %r, btn med %r, btn high %r, map 1 %r, map 2 %r, map3 %r, map4 %r, map5, %r, map6, %r.", btn_low_active, btn_med_active, btn_high_active, btn_openstreetmap_active, btn_cartopositron_active, btn_darkmatter_active, btn_stamenterrain_active, btn_stamentoner_active, btn_stamenwatercolor_active)
        
        #initialise default store vals
        dcc_settings_json = INIT_BORDER_RES
        dcc_settings_mapstyle = INIT_MAP_STYLE
        dcc_settings_colorbar = INIT_COLOR_PALETTE      
        dcc_settings_colorbar_reverse = INIT_COLOR_PALETTE_REVERSE
        
        #Logic for border resolution
        if btn_low_active == True:
            print("Setting dcc store setting json to LOW")
            dcc_settings_json = 0
        elif btn_med_active == True:
            print("Setting dcc store setting json to MED")
            dcc_settings_json = 1
        elif btn_high_active == True:
            print("Setting dcc store setting json to HIGH")
            dcc_settings_json = 2
            
        #logic for map style
        if btn_openstreetmap_active == True:
            print("Setting dcc store setting mapstyle to openstreet")
            dcc_settings_mapstyle = 0
        elif btn_cartopositron_active == True:
            print("Setting dcc store setting mapstyle to cartro")
            dcc_settings_mapstyle = 1
        elif btn_darkmatter_active == True:
            print("Setting dcc store setting mapstyle to darky")
            dcc_settings_mapstyle = 2
        elif btn_stamenterrain_active == True:
            print("Setting dcc store setting mapstyle to stamenterrain")
            dcc_settings_mapstyle = 3
        elif btn_stamentoner_active == True:
            print("Setting dcc store setting mapstyle to stamentoner")
            dcc_settings_mapstyle = 4
        elif btn_stamenwatercolor_active == True:
            print("Setting dcc store setting mapstyle to stamenwatercolour")
            dcc_settings_mapstyle = 5
    
        #logic for colorbar
        if nc1a==True: dcc_settings_colorbar = 0
        elif nc2a==True: dcc_settings_colorbar = 1 
        elif nc3a==True: dcc_settings_colorbar = 2
        elif nc4a==True: dcc_settings_colorbar = 3
        elif nc5a==True: dcc_settings_colorbar = 4
        elif nc6a==True: dcc_settings_colorbar = 5
        elif nc7a==True: dcc_settings_colorbar = 6
        elif nc8a==True: dcc_settings_colorbar = 7
        elif nc9a==True: dcc_settings_colorbar = 8
        elif nc10a==True: dcc_settings_colorbar = 9
        elif nc11a==True: dcc_settings_colorbar = 10
        elif nc12a==True: dcc_settings_colorbar = 11
        elif nc13a==True: dcc_settings_colorbar = 12
        elif nc14a==True: dcc_settings_colorbar = 13
        elif nc15a==True: dcc_settings_colorbar = 14
        elif nc16a==True: dcc_settings_colorbar = 15
        elif nc17a==True: dcc_settings_colorbar = 16
        elif nc18a==True: dcc_settings_colorbar = 17
        elif nc19a==True: dcc_settings_colorbar = 18
        elif nc20a==True: dcc_settings_colorbar = 19
        elif nc21a==True: dcc_settings_colorbar = 20
        elif nc22a==True: dcc_settings_colorbar = 21
        elif nc23a==True: dcc_settings_colorbar = 22
        elif nc24a==True: dcc_settings_colorbar = 23
        elif nc25a==True: dcc_settings_colorbar = 24
        elif nc26a==True: dcc_settings_colorbar = 25
        elif nc27a==True: dcc_settings_colorbar = 26
        elif nc28a==True: dcc_settings_colorbar = 27
        elif nc29a==True: dcc_settings_colorbar = 28
        elif nc30a==True: dcc_settings_colorbar = 29
        elif nc31a==True: dcc_settings_colorbar = 30
        elif nc32a==True: dcc_settings_colorbar = 31
        elif nc33a==True: dcc_settings_colorbar = 32
        elif nc34a==True: dcc_settings_colorbar = 33
        elif nc35a==True: dcc_settings_colorbar = 34
        elif nc36a==True: dcc_settings_colorbar = 35
        elif nc37a==True: dcc_settings_colorbar = 36
        elif nc38a==True: dcc_settings_colorbar = 37
        elif nc39a==True: dcc_settings_colorbar = 38
        elif nc40a==True: dcc_settings_colorbar = 39
        elif nc41a==True: dcc_settings_colorbar = 40
        elif nc42a==True: dcc_settings_colorbar = 41
        elif nc43a==True: dcc_settings_colorbar = 42
        elif nc44a==True: dcc_settings_colorbar = 43
        elif nc45a==True: dcc_settings_colorbar = 44
        elif nc46a==True: dcc_settings_colorbar = 45
        elif nc47a==True: dcc_settings_colorbar = 46
        elif nc48a==True: dcc_settings_colorbar = 47
        elif nc49a==True: dcc_settings_colorbar = 48
        elif nc50a==True: dcc_settings_colorbar = 49
        elif nc51a==True: dcc_settings_colorbar = 50
        elif nc52a==True: dcc_settings_colorbar = 51
        elif nc53a==True: dcc_settings_colorbar = 52
        elif nc54a==True: dcc_settings_colorbar = 53
        elif nc55a==True: dcc_settings_colorbar = 54
        elif nc56a==True: dcc_settings_colorbar = 55
        elif nc57a==True: dcc_settings_colorbar = 56
        elif nc58a==True: dcc_settings_colorbar = 57
        elif nc59a==True: dcc_settings_colorbar = 58
        elif nc60a==True: dcc_settings_colorbar = 59
        elif nc61a==True: dcc_settings_colorbar = 60
        elif nc62a==True: dcc_settings_colorbar = 61
        elif nc63a==True: dcc_settings_colorbar = 62
        elif nc64a==True: dcc_settings_colorbar = 63
        elif nc65a==True: dcc_settings_colorbar = 64
        elif nc66a==True: dcc_settings_colorbar = 65
        elif nc67a==True: dcc_settings_colorbar = 66
        elif nc68a==True: dcc_settings_colorbar = 67
        elif nc69a==True: dcc_settings_colorbar = 68
        elif nc70a==True: dcc_settings_colorbar = 69
        elif nc71a==True: dcc_settings_colorbar = 70
        elif nc72a==True: dcc_settings_colorbar = 71
        elif nc73a==True: dcc_settings_colorbar = 72
        elif nc74a==True: dcc_settings_colorbar = 73
        elif nc75a==True: dcc_settings_colorbar = 74
        elif nc76a==True: dcc_settings_colorbar = 75
        elif nc77a==True: dcc_settings_colorbar = 76
        elif nc78a==True: dcc_settings_colorbar = 77
        elif nc79a==True: dcc_settings_colorbar = 78
        elif nc80a==True: dcc_settings_colorbar = 79
        elif nc81a==True: dcc_settings_colorbar = 80
        elif nc82a==True: dcc_settings_colorbar = 81
        elif nc83a==True: dcc_settings_colorbar = 82
        elif nc84a==True: dcc_settings_colorbar = 83
        elif nc85a==True: dcc_settings_colorbar = 84
        elif nc86a==True: dcc_settings_colorbar = 85
        elif nc87a==True: dcc_settings_colorbar = 86
        elif nc88a==True: dcc_settings_colorbar = 87
        elif nc89a==True: dcc_settings_colorbar = 88
        elif nc90a==True: dcc_settings_colorbar = 89
        elif nc91a==True: dcc_settings_colorbar = 90
        elif nc92a==True: dcc_settings_colorbar = 91
        elif nc93a==True: dcc_settings_colorbar = 92   
        
        #logic for reverse button group
        if btn_reverse_active==True: dcc_settings_colorbar_reverse = True
        elif btn_normal_active==True: dcc_settings_colorbar_reverse = False
        
        return dcc_settings_json, dcc_settings_mapstyle, dcc_settings_colorbar, dcc_settings_colorbar_reverse



    #Download dataset MAIN
    @dash_app.callback(Output('download_dataset_main', 'data'),
                [Input('btn-popover-map-download-xls', 'n_clicks'),
                Input('btn-popover-map-download-csv', 'n_clicks'),
                Input('btn-popover-map-download-json', 'n_clicks'),
                #Input('btn-popover-map-download-land', 'n_clicks'),               
                ],
                State("my-series","data"), 
                State('geomap_figure', 'figure'),
                prevent_initial_call=True,)
    def callback_download_dataset_main(n1, n2,n3, series, fig): 
        
        ctx = dash.callback_context 
        trigger = ctx.triggered[0]["prop_id"].split(".")[0]
        print('trigger is ',trigger)
        
        # gather userful vars        
        series_label = master_config[series].get("dataset_label")         
        source = master_config[series].get("source")        
        link = master_config[series].get("link") 
            
        #subset master dataset to selected series, and sort by year, then country
        df = pop.loc[(pop['dataset_raw'] == series)].sort_values(by=['year', 'country'])      
        
        # make it pretty
        df['m49_un_a3'] = df['m49_un_a3'].astype(str).str.zfill(3) 
        df['United Nations m49 country code'] = df['m49_un_a3']        
        df = df.rename(columns={'value':series_label}) 
        df = df.drop(columns=['dataset_raw', 'm49_un_a3', 'continent'])        
                        
        #merge in source information     
        df['Source'] = source+" "+link
        
        # return based on trigger selection
        if trigger == 'btn-popover-map-download-xls':
            filename = "WORLD_ATLAS_2.0 "+series_label+".xlsx" 
            def to_xlsx(bytes_io):
                xslx_writer = pd.ExcelWriter(bytes_io, engine="xlsxwriter")
                df.to_excel(xslx_writer, index=False, sheet_name="sheet1")
                xslx_writer.save()    
            return send_bytes(to_xlsx, filename)
        
        elif trigger == 'btn-popover-map-download-csv':
            filename = "WORLD_ATLAS_2.0 "+series_label+".csv"     
            return send_data_frame(df.to_csv, filename, index=False)
        
        elif trigger == 'btn-popover-map-download-json':          
            filename = "WORLD_ATLAS_2.0 "+series_label+".json"        
            return send_data_frame(df.to_json, filename, orient='table', index=False)
        
        elif trigger == 'btn-popover-map-download-pdf':
            year='blah'
            f = go.Figure(fig)        
            f.update_layout(
                #title={'text':'WORLD ATLAS 2.0 - '+series_label+' in '+year,'font':{'size':36,'color':'black'},'x':0,'xref':'container', 'xanchor':'left','pad':{'b':0,'t':40,'l':40,'r':0}, 'y':1, 'yref':'container', 'yanchor':'auto'},
                #annotations=[{'text':'Source: '+source,'font':{'size':14,'color':'black'},'x':0,'xref':'paper', 'xanchor':'left','y':0, 'yref':'paper', 'yanchor':'auto'}],
                #xaxis={'title':{'text':'This chart was generated at https://worldatlas.org based on dataset: '+source+'. Originally sourced from '+link , 'font':{'size':22}}},
                height=600,
                width=4096,            
                )
            path = "tmp/WORLD_ATLAS_2.0 "+series_label+" ["+year+"].pdf" 
            plotly.io.write_image(fig=f, file=path, engine="kaleido")
            return send_file(path)


    #Download dataset BAR
    @dash_app.callback(Output('download_dataset_bar', 'data'),
                [
                #Input('modal-bar-download', 'n_clicks')
                Input('btn-popover-bar-download-csv', 'n_clicks'),
                Input('btn-popover-bar-download-json', 'n_clicks'),
                Input('btn-popover-bar-download-xls', 'n_clicks'),
                Input('btn-popover-bar-download-pdf', 'n_clicks'),
                Input('btn-popover-bar-download-jpg', 'n_clicks'),
                Input('btn-popover-bar-download-png', 'n_clicks'),
                Input('btn-popover-bar-download-svg', 'n_clicks'),
                ],              
                State('my-series-bar','data'),
                State('my-year-bar','data'),
                State('bar-graph', 'figure'),  
                prevent_initial_call=True,)
    def callback_download_dataset_bar(n1,n2,n3,n4,n5,n6,n7, myseries_bar, myyear_bar, fig):   
        
        ctx = dash.callback_context 
        trigger = ctx.triggered[0]["prop_id"].split(".")[0]
        
        series = myseries_bar
        year = int(myyear_bar)        
        series_label = master_config[series].get("dataset_label")         
        source = master_config[series].get("source")        
        link = master_config[series].get("link")         
        
        #subset master dataset to selected series and selected year
        df = pop.loc[(pop['dataset_raw'] == series) & (pop['year'] == year)].sort_values('country')   
        
        # make it pretty
        df['m49_un_a3'] = df['m49_un_a3'].astype(str).str.zfill(3) 
        df['United Nations m49 country code'] = df['m49_un_a3']
        df = df.rename(columns={'value':series_label})   
        df = df.drop(columns=['dataset_raw', 'm49_un_a3', 'continent'])     

        #merge in source information 
        df['Source'] = source+" "+link
        
        # nest function for returning chart
        def chart(extension):
            f = go.Figure(fig)        
            f.update_layout(
                title={'text':'WORLD ATLAS 2.0 - '+series_label+' in '+str(year),'font':{'size':36,'color':'black'},'x':0,'xref':'container', 'xanchor':'left','pad':{'b':0,'t':40,'l':40,'r':0}, 'y':1, 'yref':'container', 'yanchor':'auto'},
                #annotations=[{'text':'Source: '+source,'font':{'size':14,'color':'black'},'x':0,'xref':'paper', 'xanchor':'left','y':0, 'yref':'paper', 'yanchor':'auto'}],
                xaxis={'title':{'text':'Source: This chart was generated at https://worldatlas.org based on dataset: '+source+'. Originally sourced from '+link , 'font':{'size':22}}},
                height=600,
                width=4096,            
                )
            path = "tmp/WORLD_ATLAS_2.0 "+series_label+" ["+str(year)+"]"+extension
            plotly.io.write_image(fig=f, file=path, engine="kaleido")
            return send_file(path)    
        
        # main logic to return data or chart
        if trigger == 'btn-popover-bar-download-xls':
            filename = "WORLD_ATLAS_2.0 "+series_label+" ["+str(year)+"].xlsx" 
            def to_xlsx(bytes_io):
                xslx_writer = pd.ExcelWriter(bytes_io, engine="xlsxwriter")
                df.to_excel(xslx_writer, index=False, sheet_name="sheet1")
                xslx_writer.save()    
            return send_bytes(to_xlsx, filename)    

        elif trigger == 'btn-popover-bar-download-csv':       
            filename = "WORLD_ATLAS_2.0 "+series_label+" ["+str(year)+"].csv" 
            return send_data_frame(df.to_csv, filename, index=False)
        
        elif trigger == 'btn-popover-bar-download-json':          
            filename = "WORLD_ATLAS_2.0 "+series_label+" ["+str(year)+"].json"        
            return send_data_frame(df.to_json, filename, orient='table', index=False)
        
        elif trigger == 'btn-popover-bar-download-pdf': return chart('.pdf')
        elif trigger == 'btn-popover-bar-download-png': return chart('.png')
        elif trigger == 'btn-popover-bar-download-jpg': return chart('.jpg')
        elif trigger == 'btn-popover-bar-download-svg': return chart('.svg')
        else: return None
    


    #Download dataset LINE
    @dash_app.callback(Output('download_dataset_line', 'data'),
                [
                Input('btn-popover-line-download-xls','n_clicks'),
                Input('btn-popover-line-download-csv','n_clicks'),
                Input('btn-popover-line-download-json','n_clicks'),
                Input('btn-popover-line-download-pdf', 'n_clicks'),
                Input('btn-popover-line-download-jpg', 'n_clicks'),
                Input('btn-popover-line-download-png', 'n_clicks'),
                Input('btn-popover-line-download-svg', 'n_clicks'),
                ],              
                State('my-series-line','data'), 
                State('line-graph', 'figure'),
                State('line-graph-dropdown-countries', 'value'),
                prevent_initial_call=True,)
    def callback_download_dataset_line(n1,n2,n3,n4,n5,n6,n7, series, fig, countries):   
        
        ctx = dash.callback_context 
        trigger = ctx.triggered[0]["prop_id"].split(".")[0]
        
        # gather userful vars       
        series_label = master_config[series].get("dataset_label")         
        source = master_config[series].get("source")        
        link = master_config[series].get("link")   
        
        # optimise size of chart based on no. selected countries
        title_font=32
        footer_font=12
        if len(countries) <= 10:
            height=700
            width = 1920
        elif len(countries) > 10 and len(countries) <= 40:
            height=1080
            width = 1920
        else:
            height=4096
            width=1920
        
        #subset master dataset to selected series and selected year
        df = pop.loc[(pop['dataset_raw'] == series)].sort_values(['year','country'])   
        
        # make it pretty
        df['m49_un_a3'] = df['m49_un_a3'].astype(str).str.zfill(3) 
        df['United Nations m49 country code'] = df['m49_un_a3']
        df = df.rename(columns={'value':series_label})   
        df = df.drop(columns=['dataset_raw', 'm49_un_a3', 'continent'])   
        
        #merge in source information 
        df['Source'] = source+" "+link
        
        # nest function to help return charts
        def chart(extension):
            f = go.Figure(fig)        
            f.update_layout(
                title={'text':'WORLD ATLAS 2.0 - '+series_label,'font':{'size':title_font,'color':'black'},'x':0,'xref':'container', 'xanchor':'left','pad':{'b':0,'t':40,'l':40,'r':0}, 'y':1, 'yref':'container', 'yanchor':'auto'},            
                xaxis={'title':{'text':'Source: This chart was generated at https://worldatlas.org based on dataset: '+source+'. Originally sourced from '+link , 'font':{'size':footer_font}}},
                yaxis={'title':{'font':{'size':footer_font}}},            
                height=height,
                width=width,            
                )
            path = "tmp/WORLD_ATLAS_2.0 "+series_label+extension
            plotly.io.write_image(fig=f, file=path, engine="kaleido")
            return send_file(path)
        
        # main logic to return data or chart
        if trigger == 'btn-popover-line-download-xls':
            filename = "WORLD_ATLAS_2.0 "+series_label+".xlsx" 
            def to_xlsx(bytes_io):
                xslx_writer = pd.ExcelWriter(bytes_io, engine="xlsxwriter")
                df.to_excel(xslx_writer, index=False, sheet_name="sheet1")
                xslx_writer.save()    
            return send_bytes(to_xlsx, filename)
            
        elif trigger == 'btn-popover-line-download-csv':
            filename = "WORLD_ATLAS_2.0 "+series_label+".csv" 
            return send_data_frame(df.to_csv, filename, index=False)
        
        elif trigger == 'btn-popover-line-download-json':
            filename = "WORLD_ATLAS_2.0 "+series_label+".json" 
            return send_data_frame(df.to_json, filename, orient='table', index=False)
        
        elif trigger == 'btn-popover-line-download-pdf': return chart('.pdf')
        elif trigger == 'btn-popover-line-download-svg': return chart('.svg')
        elif trigger == 'btn-popover-line-download-png': return chart('.png')
        elif trigger == 'btn-popover-line-download-jpg': return chart('.jpg')
        else: return None
            


    #Download dataset SUNBURST
    @dash_app.callback(Output('download_dataset_sunburst_csv', 'data'),
                [              
                Input('btn-popover-sunburst-download-xls','n_clicks'),
                Input('btn-popover-sunburst-download-csv','n_clicks'), 
                Input('btn-popover-sunburst-download-json','n_clicks'), 
                Input('btn-popover-sunburst-download-pdf','n_clicks'),  
                Input('btn-popover-sunburst-download-png','n_clicks'),  
                Input('btn-popover-sunburst-download-svg','n_clicks'),  
                Input('btn-popover-sunburst-download-jpg','n_clicks'),  
                ],              
                [
                State('my-pizza-sunburst','data'),
                State('my-toppings-sunburst','data'),
                State('my-year-sunburst','data'),
                State('sunburst-graph', 'figure'),
                ],
                prevent_initial_call=True,)
    def callback_download_dataset_sunburst(n1,n2,n3,n4,n5,n6,n7, pizza, toppings, year, fig ):   
        #logger.info("download dataset sunburst callback:\npizza %r\ntoppings %r\nyear %r",pizza, toppings, year)
        
        ctx = dash.callback_context 
        trigger = ctx.triggered[0]["prop_id"].split(".")[0]
        
        # set some useful vars
        year = int(year)
        x = pizza #series
        y = toppings #series      
        pizza = master_config[pizza].get("dataset_label") 
        toppings = master_config[toppings].get("dataset_label") 
        
        
        height=800
        width=1200
        title_font=32
        subtitle_font=16
        footer_font=10    
        link='test link baby'      
        ds1=master_config[x].get("source")+" "+master_config[x].get("link")
        ds2=master_config[y].get("source")+" "+master_config[y].get("link")      
              
        title='WORLD ATLAS 2.0'
        subtitle1='Pizza slice width: '+pizza
        subtitle2='Pizza slice colour: '+toppings
        source1='Source: This chart was generated at https://worldatlas.org'
        source2='Dataset1: '+ds1
        source3='Dataset2: '+ds2
        series_label='WORLD_ATLAS_2.0 '+pizza+' VS '+toppings
        
        #build data frames from master
        dfx = pop[(pop['dataset_raw']==x) & (pop['year']==year)].rename(columns={"value":x})        
        dfx[x] = dfx[x].astype(float)
            
        dfy = pop[(pop['dataset_raw']==y) & (pop['year']==year)].rename(columns={"value":y})
        dfy[y] = dfy[y].astype(float)
            
        # merge dataframes on common countries
        common_countries = reduce(np.intersect1d,(dfx['country'].values,dfy['country'].values))
        dfx = dfx[dfx['country'].isin(common_countries)]
        dfy = dfy[dfy['country'].isin(common_countries)]
        df = pd.merge(dfx,dfy[['country',y]],on='country', how='left')
        
        # make pretty   
        df['m49_un_a3'] = df['m49_un_a3'].astype(str).str.zfill(3) 
        df['United Nations m49 country code'] = df['m49_un_a3']
        df = df.drop(columns=['dataset_raw', 'continent', 'm49_un_a3'])    
        df = df.rename(columns={x:pizza, y:toppings})    
        
        #merge in source information 
        df['Source1'] = ds1  
        df['Source2'] = ds2
        
        # prepare nested func to return chart
        def chart(extension):
            print('in function test')
            f = go.Figure(fig)        
            f.update_layout(
                title={'text':title,'font':{'size':title_font,'color':'black'},'x':0,'xref':'container', 'xanchor':'left','pad':{'b':0,'t':40,'l':40,'r':0}, 'y':1, 'yref':'container', 'yanchor':'auto'},
                annotations=[
                    {'text':source1,'font':{'size':footer_font,'color':'black'},'x':0,'xref':'paper', 'xanchor':'left','y':-0.09, 'yref':'paper', 'yanchor':'auto', 'showarrow':False},
                    {'text':source2,'font':{'size':footer_font,'color':'black'},'x':0,'xref':'paper', 'xanchor':'left','y':-0.12, 'yref':'paper', 'yanchor':'auto', 'showarrow':False},
                    {'text':source3,'font':{'size':footer_font,'color':'black'},'x':0,'xref':'paper', 'xanchor':'left','y':-0.15, 'yref':'paper', 'yanchor':'auto', 'showarrow':False},
                    {'text':subtitle1,'font':{'size':subtitle_font,'color':'black'},'x':0,'xref':'paper', 'xanchor':'left','y':1.10, 'yref':'paper', 'yanchor':'auto', 'showarrow':False},
                    {'text':subtitle2,'font':{'size':subtitle_font,'color':'black'},'x':0,'xref':'paper', 'xanchor':'left','y':1.06, 'yref':'paper', 'yanchor':'auto', 'showarrow':False}
                    ],            
                margin=dict(t=130, b=100),
                height=height,
                width=width,            
                )
            path = "tmp/"+series_label+extension 
            plotly.io.write_image(fig=f, file=path, engine="kaleido")
            return send_file(path)        
            
        # main logic to return data             
        if trigger == 'btn-popover-sunburst-download-csv':        
            filename = "WORLD_ATLAS_2.0 "+pizza+" and "+toppings+" ["+str(year)+"].csv" 
            return send_data_frame(df.to_csv, filename, index=False)
        
        elif trigger == 'btn-popover-sunburst-download-json': 
            filename = "WORLD_ATLAS_2.0 "+pizza+" and "+toppings+" ["+str(year)+"].json"     
            return send_data_frame(df.to_json, filename, orient='table', index=False)
        
        elif trigger == 'btn-popover-sunburst-download-xls':
            filename = "WORLD_ATLAS_2.0 "+pizza+" and "+toppings+" ["+str(year)+"].xls"
            def to_xlsx(bytes_io):
                xslx_writer = pd.ExcelWriter(bytes_io, engine="xlsxwriter")
                df.to_excel(xslx_writer, index=False, sheet_name="sheet1")
                xslx_writer.save()    
            return send_bytes(to_xlsx, filename)
        
        elif trigger == 'btn-popover-sunburst-download-pdf': return chart('.pdf')
        elif trigger == 'btn-popover-sunburst-download-png': return chart('.png')
        elif trigger == 'btn-popover-sunburst-download-jpg': return chart('.jpg')
        elif trigger == 'btn-popover-sunburst-download-svg': return chart('.svg')
        else: return None
        

    #Download dataset BUBBLE
    @dash_app.callback(Output('download_dataset_bubble', 'data'),
                [              
                Input('btn-popover-bubble-download-xls','n_clicks'),
                Input('btn-popover-bubble-download-csv','n_clicks'),
                Input('btn-popover-bubble-download-json','n_clicks'),
                Input('btn-popover-bubble-download-pdf','n_clicks'),
                Input('btn-popover-bubble-download-png','n_clicks'),
                Input('btn-popover-bubble-download-jpg','n_clicks'),
                Input('btn-popover-bubble-download-svg','n_clicks'),             
                ],              
                State('my-xseries-bubble', 'data'),
                State('my-yseries-bubble', 'data'),
                State('my-zseries-bubble', 'data'),
                State('my-year-bubble', 'data'),
                State('bubble-graph','figure'),
                #State('my-year-bar','data'),
                prevent_initial_call=True,)
    def callback_download_dataset_bubble(n1,n2,n3,n4,n5,n6,n7, x, y, z, year, fig ):   
        logger.info("download dataset bubble graph callback:\nx %r\ny %r\nz %r\nyear %r",x, y, z, str(year))
        
        ctx = dash.callback_context 
        trigger = ctx.triggered[0]["prop_id"].split(".")[0]
        
        # gather and set some useful vars    
        year = int(year)
        
        
        #Build 3 dataframes as precursor to chart data
        if x != None: dfx = pop[(pop['dataset_raw']==x) & (pop['year']==year)].rename(columns={"value":x})   
        if y != None: dfy = pop[(pop['dataset_raw']==y) & (pop['year']==year)].rename(columns={"value":y})
        if z != None: dfz = pop[(pop['dataset_raw']==z) & (pop['year']==year)].rename(columns={"value":z})
            
        #we're gonna need logic for every input combination
        
        # x only
        if x!=None and y==None and z==None:
            dfa = dfx
            print("x")      
        
        # x y only
        elif x!=None and y!=None and z==None:
            common_countries = reduce(np.intersect1d,(dfx['country'].values,dfy['country'].values))
            dfx = dfx[dfx['country'].isin(common_countries)]
            dfy = dfy[dfy['country'].isin(common_countries)]
            dfa = pd.merge(dfx,dfy[['country',y]],on='country', how='left')
            print("xy")
            
        # x z only
        elif x!=None and y==None and z!=None:    
            common_countries = reduce(np.intersect1d,(dfx['country'].values, dfz['country'].values))
            dfx = dfx[dfx['country'].isin(common_countries)]        
            dfz = dfz[dfz['country'].isin(common_countries)]
            dfa = pd.merge(dfx,dfz[['country',z]],on='country', how='left')
            print("xz")
            
        # y only    
        elif x==None and y!=None and z==None:
            dfa = dfy
            print("y")        
        
        # y z only
        elif x==None and y!=None and z!=None:
            common_countries = reduce(np.intersect1d,(dfy['country'].values, dfz['country'].values))        
            dfy = dfy[dfy['country'].isin(common_countries)]
            dfz = dfz[dfz['country'].isin(common_countries)]
            dfa = pd.merge(dfy,dfz[['country',z]],on='country', how='left')
            print("yz")
            
        # z only    
        elif x==None and y==None and z!=None:
            dfa = dfz
            print("z")
        
        # x y z
        else:
        
            #find the unique list of countries that are present in all 3 datasets
            common_countries = reduce(np.intersect1d,(dfx['country'].values,dfy['country'].values, dfz['country'].values))
            
            #strip out non common countries from the 3 datasets before merging
            dfx = dfx[dfx['country'].isin(common_countries)]
            dfy = dfy[dfy['country'].isin(common_countries)]
            dfz = dfz[dfz['country'].isin(common_countries)]
            
            #merge the dataframes on country    
            dfa = pd.merge(dfx,dfy[['country',y]],on='country', how='left')
            dfa = pd.merge(dfa,dfz[['country',z]],on='country', how='left')
            
        # prepare final data frame for download
        
        # rename columns to datset labels   
        if x in dfa.columns: dfa = dfa.rename(columns={x:master_config[x].get("dataset_label") })        
        if y in dfa.columns: dfa = dfa.rename(columns={y:master_config[y].get("dataset_label") })    
        if z in dfa.columns: dfa = dfa.rename(columns={z:master_config[z].get("dataset_label") })    
        
        # make pretty   
        #dfa['Continent'] = dfa['continent']
        dfa['m49_un_a3'] = dfa['m49_un_a3'].astype(str).str.zfill(3) 
        dfa['United Nations m49 country code'] = dfa['m49_un_a3']
        dfa = dfa.drop(columns=['continent','m49_un_a3', 'dataset_raw'])    
        dfa = dfa.sort_values(by=['country'])  
        
        #chart vars
        height = 800
        width = 1200
        title = 'WORLD ATLAS 2.0'
        title_font=32
        series_label='WORLD_ATLAS_2.0 - Bubble Chart Multiseries'
        subtitle1= 'Horizontal axis: '+master_config[x].get("dataset_label") 
        subtitle2= 'Vertical axis: '+master_config[y].get("dataset_label") 
        subtitle3= 'Bubble size: '+master_config[z].get("dataset_label") 
        subtitle4= 'year: '+str(year)
        subtitle_font=16
        source1='Source: This chart was generated at https://worldatlas.org'
        source2='Dataset1: '+master_config[x].get("source") +" "+master_config[x].get("link") 
        source3='Dataset2: '+master_config[y].get("source") +" "+master_config[y].get("link") 
        source4='Dataset3: '+master_config[z].get("source") +" "+master_config[z].get("link") 
        footer_font=12
        
        
        # prepare nested func to return chart
        def chart(extension):        
            f = go.Figure(fig)        
            f.update_layout(
                title={'text':title,'font':{'size':title_font,'color':'black'},'x':0,'xref':'container', 'xanchor':'left','pad':{'b':0,'t':40,'l':40,'r':0}, 'y':1, 'yref':'container', 'yanchor':'auto'},
                annotations=[
                    {'text':source1,'font':{'size':footer_font,'color':'black'},'x':0,'xref':'paper', 'xanchor':'left','y':-0.23, 'yref':'paper', 'yanchor':'auto', 'showarrow':False},
                    {'text':source2,'font':{'size':footer_font,'color':'black'},'x':0,'xref':'paper', 'xanchor':'left','y':-0.27, 'yref':'paper', 'yanchor':'auto', 'showarrow':False},
                    {'text':source3,'font':{'size':footer_font,'color':'black'},'x':0,'xref':'paper', 'xanchor':'left','y':-0.31, 'yref':'paper', 'yanchor':'auto', 'showarrow':False},
                    {'text':source4,'font':{'size':footer_font,'color':'black'},'x':0,'xref':'paper', 'xanchor':'left','y':-0.35, 'yref':'paper', 'yanchor':'auto', 'showarrow':False},
                    
                    {'text':subtitle1,'font':{'size':subtitle_font,'color':'black'},'x':0,'xref':'paper', 'xanchor':'left','y':1.25, 'yref':'paper', 'yanchor':'auto', 'showarrow':False},
                    {'text':subtitle2,'font':{'size':subtitle_font,'color':'black'},'x':0,'xref':'paper', 'xanchor':'left','y':1.20, 'yref':'paper', 'yanchor':'auto', 'showarrow':False},
                    {'text':subtitle3,'font':{'size':subtitle_font,'color':'black'},'x':0,'xref':'paper', 'xanchor':'left','y':1.15, 'yref':'paper', 'yanchor':'auto', 'showarrow':False},
                    {'text':subtitle4,'font':{'size':subtitle_font,'color':'black'},'x':0,'xref':'paper', 'xanchor':'left','y':1.10, 'yref':'paper', 'yanchor':'auto', 'showarrow':False},
                    ],            
                margin=dict(t=200, b=200),
                height=height,
                width=width,            
                )
            path = "tmp/"+series_label+extension 
            plotly.io.write_image(fig=f, file=path, engine="kaleido")
            return send_file(path)  
        
        if trigger == 'btn-popover-bubble-download-csv':
            filename = "WORLD_ATLAS_2.0 Bubble Graph Multiseries.csv" 
            return send_data_frame(dfa.to_csv, filename, index=False)
        
        elif trigger == 'btn-popover-bubble-download-json':
            filename = "WORLD_ATLAS_2.0 Bubble Graph Multiseries.json" 
            return send_data_frame(dfa.to_json, filename, orient='table', index=False)
        
        elif trigger == 'btn-popover-bubble-download-xls':
            filename = "WORLD_ATLAS_2.0 Bubble Graph Multiseries.xlsx" 
            def to_xlsx(bytes_io):
                xslx_writer = pd.ExcelWriter(bytes_io, engine="xlsxwriter")
                dfa.to_excel(xslx_writer, index=False, sheet_name="sheet1")
                xslx_writer.save()    
            return send_bytes(to_xlsx, filename)
        
        elif trigger == 'btn-popover-bubble-download-pdf': return chart('.pdf')
        elif trigger == 'btn-popover-bubble-download-png': return chart('.png')
        elif trigger == 'btn-popover-bubble-download-jpg': return chart('.jpg')
        elif trigger == 'btn-popover-bubble-download-svg': return chart('.svg')
        else: return None


    #Download dataset DOWNLOADS
    @dash_app.callback(
                [
                Output('download_object_downloads_modal', 'data'),
                Output('my-spinner-dl-series', 'children'),
                ],
                [
                Input('btn-downloads-all-data', 'n_clicks'),
                Input('btn-downloads-countries', 'n_clicks'),
                Input('btn-downloads-series', 'n_clicks'),
                Input ('btn-downloads-years', 'n_clicks'),                                            
                ],
                State('downloads-countries-selector','value'), #selected countries
                State('downloads-series-selector','value'), #selected series
                State('downloads-year-selector', 'value'), # selected years
                prevent_initial_call=True,)
    def callback_download_dataset_downloads(n1, n2, n3, n4, countrieselection, seriesSelection, yearSelection): 
        
        ctx = dash.callback_context 
        trigger = ctx.triggered[0]["prop_id"].split(".")[0]
        print('DOWNLOADS modal. trigger is ',trigger)
               
                    
        if trigger == 'btn-downloads-all-data':
            
            #sort master dataset
            df = pop.sort_values(by=['Series','year', 'country'])  
            
            # make it pretty
            df['m49_un_a3'] = df['m49_un_a3'].astype(str).str.zfill(3) 
            df['United Nations m49 country code'] = df['m49_un_a3'] 
            df = df.drop(columns=['m49_un_a3', 'region_un', 'region_wb', 'continent'])   
            #print(len(df))
            
            path = "./tmp/WORLD_ATLAS_alldata.zip"
            df.to_csv(path, index=False, compression={'method': 'zip', 'archive_name':'WORLD_ATLAS_alldata.csv', 'compresslevel': 1}) 
            return send_file(path),''

        elif trigger == 'btn-downloads-countries':

            # return if no country selected
            if countrieselection == None or countrieselection == []: return None, ''

            #sort master dataset favouring country first
            df = pop.sort_values(by=['country','Series', 'year']) 

            # make it pretty and strip 
            df['m49_un_a3'] = df['m49_un_a3'].astype(str).str.zfill(3) 
            df['United Nations m49 country code'] = df['m49_un_a3'] 
            df = df.drop(columns=['m49_un_a3', 'region_un', 'region_wb', 'continent'])  

            #query it based on selected countries
            df = df.loc[df['country'].isin(countrieselection)]

            # return dataframe as zipped csv
            path = "./tmp/WORLD_ATLAS_custom_query_by_region.zip"
            df.to_csv(path, index=False, compression={'method': 'zip', 'archive_name':'WORLD_ATLAS_custom_query_by_region.csv', 'compresslevel': 1}) 
            return send_file(path), ''

        elif trigger == 'btn-downloads-series':            

            # return if no series selected
            if seriesSelection == None or seriesSelection == []: return None,''
            
            #sort master dataset favouring country first
            df = pop.sort_values(by=['Series','country', 'year']) 

            # make it pretty and strip 
            df['m49_un_a3'] = df['m49_un_a3'].astype(str).str.zfill(3) 
            df['United Nations m49 country code'] = df['m49_un_a3'] 
            df = df.drop(columns=['m49_un_a3', 'region_un', 'region_wb', 'continent'])  

            #query it based on selected countries
            df = df.loc[df['Series'].isin(seriesSelection)]

            # return dataframe as zipped csv
            path = "./tmp/WORLD_ATLAS_custom_query_by_series.zip"
            df.to_csv(path, index=False, compression={'method': 'zip', 'archive_name':'WORLD_ATLAS_custom_query_by_series.csv', 'compresslevel': 1}) 
            return send_file(path), ''

        elif trigger == 'btn-downloads-years':
            
            # return if no series selected
            if yearSelection == None or yearSelection == []: return None,''
            
            #sort master dataset favouring year first
            df = pop.sort_values(by=['year','Series', 'country']) 

            # make it pretty and strip 
            df['m49_un_a3'] = df['m49_un_a3'].astype(str).str.zfill(3) 
            df['United Nations m49 country code'] = df['m49_un_a3'] 
            df = df.drop(columns=['m49_un_a3', 'region_un', 'region_wb', 'continent'])  

            #query it based on selected countries
            df = df.loc[df['year'].isin(yearSelection)]  ##cast to int??

            # return dataframe as zipped csv
            path = "./tmp/WORLD_ATLAS_custom_query_by_year.zip"
            df.to_csv(path, index=False, compression={'method': 'zip', 'archive_name':'WORLD_ATLAS_custom_query_by_year.csv', 'compresslevel': 1}) 
            return send_file(path), ''
          

        else: return None, ''

       




    #year slider callback 
    @dash_app.callback(                      
        Output("timeslider-hidden-div", "children"),    
        Input("year-slider", "value"),    
        prevent_initial_call=True,
    )
    def callback_year_slider_change(year_index):
        #This callback must be separate as year slider is created from main callback, so this acts as a trigger for the main
        #logger.info("CALLBACK: Time slider change. year input change detected. Selected year index is %r, marks are %r", year_index) 
        return "dummy"


    #Bar graph modal
    @dash_app.callback(
        [
        Output("dbc-modal-bar", "is_open"),
        Output('bar-graph', 'figure'),
        Output("bar-graph-modal-title", "children"),
        Output("bar-graph-modal-footer", "children"),
        Output("bar-graph-modal-footer-link", "href"),
        Output('my-loader-bar', "children"), #used to trigger loader. Use null string "" as output
        Output('bar-graph-dropdown-countrieselector', 'options'),
        Output('bar-graph-dropdown-dataset', 'options'), 
        Output('bar-graph-dropdown-year', 'options'),
        Output('my-series-bar','data'),
        Output('my-year-bar','data'),     
        Output("my-url-bar-callback","data"),
        Output('my-loader-bar-refresh','children'),
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
        State("my-series", "data"), #super useful. Use state of selections as global vars via state.     
        #State("my-series-data","data"),     
        State("year-slider", "value"),  
        State("year-slider", "marks"),     
        State('bar-graph-dropdown-year','options'),
        State('url','href'),
        State("my-url-view", 'data'),       
        State("my-url-series", 'data'),
        State("my-url-year", 'data'),
        ],
        prevent_initial_call=True
    )
    #@cache.memoize(timeout=CACHE_TIMEOUT)
    def callback_toggle_modal_bar(bar_trigger, n1, n2, dropdown_countrieselector, dropdown_dataset, dropdown_year, is_open, series, yearid, yeardict, dropdown_year_list, href, url_view, url_series, url_year):
            
        #first check triggers and context 
        ctx = dash.callback_context 
        trigger = ctx.triggered[0]["prop_id"].split(".")[0] #this is the series selection (component id from navbar top), except if the year slider is the trigger!!
        #logger.info("bargraph callback. Trigger is %r, open state is %r, n1 %r, n2 %r, dropdown_countries %r, dropdown_dataset %r dropdown_year %r", trigger, is_open, n1, n2, dropdown_countrieselector, dropdown_dataset, dropdown_year)   
        #print("Series is ",series)
        
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
        
        # case: entry from map mode (use series store and year from slider)    
        elif trigger == 'bar-button':
            
            year = str(d.get_years(pop.loc[(pop['dataset_raw'] == series)])[yearid])            
            series_label = master_config[series].get("dataset_label")         
            source = master_config[series].get("source")        
            link = master_config[series].get("link") 
            bar_graph_title = series_label+" in "+year  
            df = d.get_series_and_year(pop, year, series, False)   #select the series and year from pop data, and sort it descending                 
            
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
    


    #Line graph modal
    @dash_app.callback(
        [
        Output("dbc-modal-line", "is_open"),
        Output('line-graph', 'figure'),
        Output("line-graph-modal-title", "children"),
        Output("line-graph-modal-footer", "children"),
        Output("line-graph-modal-footer-link", "href"),
        Output('my-loader-line', "children"), #used to trigger loader. Use null string "" as output
        Output('line-graph-dropdown-countries', 'options'),
        Output('line-graph-dropdown-dataset', 'options'),
        Output('my-series-line', 'data'),
        Output("my-url-line-callback","data"),
        Output('my-loader-line-refresh','children'),     
        ],
        [
        Input("my-url-line-trigger", "data"), 
        Input("line-button", "n_clicks"), 
        Input("modal-line-close", "n_clicks"),
        Input("line-graph-dropdown-countries", "value"),
        Input('line-graph-dropdown-dataset', 'value'),
        ],
        [
        State("dbc-modal-line", "is_open"),
        State("my-series", "data"), #super useful. Use state of selections as global vars via state.
        State("year-slider", "value"),  
        State("year-slider", "marks"),
        State("my-url-series", 'data'),
        State('url','href'),  
        State("my-url-view", 'data'),
        State("my-url-year", 'data'),
                    
        ],
        prevent_initial_call=True
    )
    #@cache.memoize(timeout=CACHE_TIMEOUT)
    def callback_toggle_modal_line(line_trigger, n1, n2, dd_country_choices, dd_dataset_choice, is_open, series, yearid, yeardict, url_series, href, url_view, url_year):
        
        #first check triggers and context 
        ctx = dash.callback_context 
        trigger = ctx.triggered[0]["prop_id"].split(".")[0] #this is the series selection (component id from navbar top), except if the year slider is the trigger!!
        #logger.info("linegraph callback. \nTrigger is %r,\nopen state is %r, n1 %r, n2 %r, \ndropdown country %r\ndropdown dataset %r", trigger, is_open, n1, n2, dd_country_choices, dd_dataset_choice) 
        
        if trigger == 'modal-line-close': return not is_open, {}, None,None,None,None, [],[], None,None,None
        
        # special api check 
        if trigger == 'my-url-line-trigger':     
            if url_view == '' or line_trigger != 'line': 
                #print("breaking out of line callback!")
                raise PreventUpdate()
                
            else: series=api_dict_label_to_raw[url_series]
        
        #Check if a dataset choice is the trigger (simpler than bar logic as no years to worry about)
        elif dd_dataset_choice!='' and dd_dataset_choice!=None: series = dd_dataset_choice      
        
        #Gather variables we need    
        series_label = master_config[series].get("dataset_label")         
        source = master_config[series].get("source")        
        link = master_config[series].get("link") 
        graph_title = series_label
            
        # select the series from pop data (all years)
        df = pop[(pop["dataset_raw"] == series)].sort_values(by="country", ascending=True)
            
        # cast numeric values to floats
        df["value"] = df["value"].astype(float)
        df["year"] = df["year"].astype(int)
        
        # Build dropdown list for countries
        ddc = np.sort(pd.unique(df["country"]).astype(str)) #numpy array    
        dd_country_list=[]    
        #dd_country_list.append({'label': 'ALL COUNTRIES' , 'value': 'ALL COUNTRIES'})
        for i in range(0,len(ddc)):
            dd_country_list.append({'label': ddc[i], 'value': ddc[i]})
            
        # Build dropdown list for datasets  (continuous and ratio only)      
                
        # get list of dicts for continuous and ratio, then combine them
        list_continuous = d.get_list_of_dataset_labels_and_raw(master_config,'continuous')
        list_ratio = d.get_list_of_dataset_labels_and_raw(master_config,'ratio')
        list_combined = list_continuous + list_ratio #won't be sorted
        
        # sort this list by label by converting to df and back to list
        list_combined = pd.DataFrame(list_combined).sort_values(by="dataset_label").to_dict('records') 
        
        #assemble into list of dicts for dropdown
        dd_dataset_list=[] 
        for i in range(0,len(list_combined)):        
            dd_dataset_list.append({'label': list_combined[i].get("dataset_label"), 'value': list_combined[i].get("dataset_raw")}) 
        
        
        # build url    
        blah = href.split('/') 
        root = blah[0]+'//'+blah[2]+'/'
        url = root + api_dict_raw_to_label[series] + '/' + 'x/line'          
            
        # keep modal open in these conditions
        if trigger == 'line-graph-dropdown-countries' or trigger == 'line-graph-dropdown-dataset': is_open = not is_open
        
        return not is_open, create_chart_line(df, series, dd_country_choices), graph_title, source, link, "", dd_country_list, dd_dataset_list, series, url, ''


    #Bubble graph modal
    @dash_app.callback(
        [
        Output("dbc-modal-bubble", "is_open"),
        Output('bubble-graph', 'figure'),
        Output("bubble-graph-modal-title", "children"),
        #Output("bubble-graph-modal-footer", "children"),
        #Output("bubble-graph-modal-footer-link", "href"),
        Output('my-loader-bubble', "children"), #used to trigger loader. Use null string "" as output
        Output('bubble-graph-dropdownX', 'options'),
        Output('bubble-graph-dropdownY', 'options'),
        Output('bubble-graph-dropdownZ', 'options'),
        Output('bubble-graph-dropdownyear', 'options'),
        Output('my-xseries-bubble', 'data'),
        Output('my-yseries-bubble', 'data'),
        Output('my-zseries-bubble', 'data'),
        Output('my-year-bubble', 'data'),
        Output('my-loader-bubble-refresh','children'),
        
        ],
        [
        Input("bubble-button", "n_clicks"), 
        Input("modal-bubble-close", "n_clicks"),
        Input("chklist-bubble-log", "value"),
        Input("bubble-graph-dropdownX", "value"),
        Input("bubble-graph-dropdownY", "value"),
        Input("bubble-graph-dropdownZ", "value"),
        Input("bubble-graph-dropdownyear", "value"),     
        ],
        [
        State("dbc-modal-bubble", "is_open"),
        #State("my-series", "children"), #super useful. Use state of selections as global vars via state.
        #State("year-slider", "value"),  
        #State("year-slider", "marks"), 
        State("chklist-bubble-log", "value"),
            
        ],
        prevent_initial_call=True
    )
    def callback_toggle_modal_bubble(n1, n2, n3, dropdown_choicesX, dropdown_choicesY, dropdown_choicesZ, dropdown_choicesyear, is_open, chklist_log_state): #series, yearid, yeardict
        
        #first check triggers and context 
        ctx = dash.callback_context 
        trigger = ctx.triggered[0]["prop_id"].split(".")[0] #this is the series selection (component id from navbar top), except if the year slider is the trigger!!    
        
        # break out on close button
        if trigger == 'modal-bubble-close': return not is_open, {}, None,None, [],[],[],[],None,None,None,None,None
        
        #initial logic fixes (helper can reset these to '' instead of None, which fucks up logic below)
        if dropdown_choicesX == '': dropdown_choicesX = None
        if dropdown_choicesY == '': dropdown_choicesY = None 
        if dropdown_choicesZ == '': dropdown_choicesZ = None 
        
        #Gather variables we need     
        graph_title = "Bubble Chart - Compare three datasets"
        
        #log checkbox logic
        xlog=False
        ylog=False
        zlog=False
        
        if len(chklist_log_state)!=0:              
            if 'x' in chklist_log_state:
                xlog=True
            if 'y' in chklist_log_state:
                ylog=True
            if 'z' in chklist_log_state:
                zlog=True        
        
        # build drop downs
        
        # return all continuous datasets as list of dicts        
        #dd = dataset_lookup[(dataset_lookup['var_type']!='discrete')].sort_values(by="dataset_label")
        dd = d.get_list_of_dataset_labels_and_raw(master_config,'all')
        
        # Note in future may want to pull out discrete. Cutting corners for now.
        
        # assemble the dropdown list using raw and label
        dropdownX=[]        
        for i in range(0,len(dd)): dropdownX.append({'label': dd[i].get("dataset_label"), 'value': dd[i].get("dataset_raw")})
        
        #duplicate this dropdown in separate memory for the other two dropdowns
        dropdownY = copy.deepcopy(dropdownX)
        dropdownZ = copy.deepcopy(dropdownX)
        
        #now strip out any datsets that have already been selected to remove duplicate selections
        if dropdown_choicesX != None:        
            #first y
            for i in range(0,len(dropdownY)):
                if dropdownY[i]['value']==dropdown_choicesX:                
                    del dropdownY[i]
                    break #to avoid key error
            #then z
            for i in range(0,len(dropdownZ)):
                if dropdownZ[i]['value']==dropdown_choicesX:
                    del dropdownZ[i]
                    break    
        
        if dropdown_choicesY != None:        
            #first x
            for i in range(0,len(dropdownX)):
                if dropdownX[i]['value']==dropdown_choicesY:                
                    del dropdownX[i]
                    break #to avoid key error
            #then z
            for i in range(0,len(dropdownZ)):
                if dropdownZ[i]['value']==dropdown_choicesY:
                    del dropdownZ[i]
                    break
                
        if dropdown_choicesZ != None:        
            #first x
            for i in range(0,len(dropdownX)):
                if dropdownX[i]['value']==dropdown_choicesZ:                
                    del dropdownX[i]
                    break #to avoid key error
            #then Y
            for i in range(0,len(dropdownY)):
                if dropdownY[i]['value']==dropdown_choicesZ:
                    del dropdownY[i]
                    break
        
        #Update the years list dynamically based on the datasets selected
        dropdownyear = []     
        
        #if no datasets are selected show no years
        if dropdown_choicesX == None and dropdown_choicesY == None and dropdown_choicesZ == None:        
            dropdownyear.clear()
            
        # x only
        elif dropdown_choicesX != None and dropdown_choicesY == None and dropdown_choicesZ == None:   
            dfx = np.sort(pd.unique(pd.DataFrame(pop[(pop['dataset_raw']==dropdown_choicesX)], columns=['year'])['year'].astype(int)))
            years = dfx
            for i in range(0,len(years)):
                dropdownyear.append({'label': years[i], 'value': years[i]}) 
        
        # x y only
        elif dropdown_choicesX != None and dropdown_choicesY != None and dropdown_choicesZ == None:
            dfx = np.sort(pd.unique(pd.DataFrame(pop[(pop['dataset_raw']==dropdown_choicesX)], columns=['year'])['year'].astype(int)))
            dfy = np.sort(pd.unique(pd.DataFrame(pop[(pop['dataset_raw']==dropdown_choicesY)], columns=['year'])['year'].astype(int)))
            years = reduce(np.intersect1d,(dfx,dfy))
            for i in range(0,len(years)):
                dropdownyear.append({'label': years[i], 'value': years[i]})  
        
        # x z only
        elif dropdown_choicesX != None and dropdown_choicesY == None and dropdown_choicesZ != None:
            dfx = np.sort(pd.unique(pd.DataFrame(pop[(pop['dataset_raw']==dropdown_choicesX)], columns=['year'])['year'].astype(int)))        
            dfz = np.sort(pd.unique(pd.DataFrame(pop[(pop['dataset_raw']==dropdown_choicesZ)], columns=['year'])['year'].astype(int)))
            years = reduce(np.intersect1d,(dfx,dfz))      
            for i in range(0,len(years)):
                dropdownyear.append({'label': years[i], 'value': years[i]})  
        
        # y only
        elif dropdown_choicesX == None and dropdown_choicesY != None and dropdown_choicesZ == None:    
            dfy = np.sort(pd.unique(pd.DataFrame(pop[(pop['dataset_raw']==dropdown_choicesY)], columns=['year'])['year'].astype(int)))
            years = dfy
            for i in range(0,len(years)):
                dropdownyear.append({'label': years[i], 'value': years[i]})
        
        # y z only
        elif dropdown_choicesX == None and dropdown_choicesY != None and dropdown_choicesZ != None:         
            dfy = np.sort(pd.unique(pd.DataFrame(pop[(pop['Series']==dropdown_choicesY)], columns=['year'])['year'].astype(int)))
            dfz = np.sort(pd.unique(pd.DataFrame(pop[(pop['Series']==dropdown_choicesZ)], columns=['year'])['year'].astype(int)))       
            years = reduce(np.intersect1d,(dfy,dfz))        
            for i in range(0,len(years)):
                dropdownyear.append({'label': years[i], 'value': years[i]})
        
        # z only
        elif dropdown_choicesX == None and dropdown_choicesY == None and dropdown_choicesZ != None:
            dfz = np.sort(pd.unique(pd.DataFrame(pop[(pop['Series']==dropdown_choicesZ)], columns=['year'])['year'].astype(int)))
            years = dfz
            for i in range(0,len(years)):
                dropdownyear.append({'label': years[i], 'value': years[i]})
        
        # x y z
        else:
            #query master dataset based on the 3 choices and produce a unique list of years for each (i.e. the years data is available for each set)
            print("Dropdown choices are: ",dropdown_choicesX, dropdown_choicesY, dropdown_choicesZ)
            
            dfx = np.sort(pd.unique(pd.DataFrame(pop[(pop['dataset_raw']==dropdown_choicesX)], columns=['year'])['year'].astype(int)))
            dfy = np.sort(pd.unique(pd.DataFrame(pop[(pop['dataset_raw']==dropdown_choicesY)], columns=['year'])['year'].astype(int)))
            dfz = np.sort(pd.unique(pd.DataFrame(pop[(pop['dataset_raw']==dropdown_choicesZ)], columns=['year'])['year'].astype(int)))
            
            print("Length of year arrays dfx, dfy, dfz :",len(dfx), len(dfy), len(dfz))
            
            #now find interections across the 3 arrays, for common years in which we have data for all sets
            years = reduce(np.intersect1d,(dfx,dfy,dfz))            

            #build the year dropdown
            for i in range(0,len(years)):
                dropdownyear.append({'label': years[i], 'value': years[i]})      
        
        #funky year logic
        if dropdown_choicesX != None or dropdown_choicesY != None or dropdown_choicesZ != None:
            #logger.info("Testing....\n\navailable years %r\nselected year %r", years, dropdown_choicesyear)
            
            #if no available years do something
            if len(years) == 0:
                print("no available years")
                dropdownyear.clear()
                #dropdownyear.append({'label': 'No available years', 'value': 'No available years'}) 
            
            #set to most recent year if null (this happens once I think due to helper callback)
            elif dropdown_choicesyear == '' or dropdown_choicesyear == None:
                dropdown_choicesyear = years[-1]
                
            #check if has come back as dictionary from helper and retrieve value(countriesy but can tweak)
            elif type(dropdown_choicesyear) is dict:
                dropdown_choicesyear = dropdown_choicesyear['value']
                if dropdown_choicesyear in years:
                    print("selected year is in available years")
                else:
                    print("selected year not in available, so setting to most recent from available")            
                    dropdown_choicesyear = years[-1]
            
            #can we autoselect the most recent year?
        
        # keep modal open in this condition
        if trigger == "chklist-bubble-log" or trigger == "bubble-graph-dropdownX" or trigger == "bubble-graph-dropdownY" or trigger == "bubble-graph-dropdownZ" or trigger == "bubble-graph-dropdownyear": is_open = not is_open
        
        return not is_open, create_chart_bubble(dropdown_choicesX, dropdown_choicesY, dropdown_choicesZ, dropdown_choicesyear, xlog, ylog, zlog), graph_title, "", dropdownX, dropdownY, dropdownZ, dropdownyear,dropdown_choicesX, dropdown_choicesY, dropdown_choicesZ, dropdown_choicesyear, ''
        
    

    #Sunburst graph modal
    @dash_app.callback(
        [
        Output("dbc-modal-sunburst", "is_open"),     
        Output("sunburst-graph-modal-title", "children"),
        Output("sunburst-graph-modal-footer", "children"),
        Output("sunburst-graph-modal-footer-link", "href"),
        Output('sunburst-graph', 'figure'),
        Output('my-loader-sunburst', "children"), #used to trigger loader. Use null string "" as output
        Output('sunburst-dropdown-pizza','options'),
        Output('sunburst-dropdown-toppings', 'options'),
        Output('my-pizza-sunburst','data'),
        Output('my-toppings-sunburst','data'),       
        Output('my-year-sunburst','data'),
        Output('my-loader-sunburst-refresh','children'),
        ],
        [
        Input("sunburst-button", "n_clicks"), 
        Input("modal-sunburst-close", "n_clicks"),
        Input('sunburst-dropdown-pizza','value'),
        Input('sunburst-dropdown-toppings','value'),
        ],
        [
        State("dbc-modal-bar", "is_open"),
        State("my-series", "data"), #super useful. Use state of selections as global vars via state.
        State("year-slider", "value"),  
        State("year-slider", "marks"),
        State("my-settings_colorbar_store", 'data'),
        State("my-settings_colorbar_reverse_store", 'data'), 
        State('my-pizza-sunburst','data'),
        State('my-toppings-sunburst','data'),
        State('my-year-sunburst','data'),
        State('sunburst-dropdown-pizza','value'),
        State('sunburst-dropdown-toppings','value'),
            
        ],
        prevent_initial_call=True
    )
    def callback_toggle_modal_sunburst(n1, n2, ddv_pizza, ddv_toppings, is_open, series, yearid, yeardict, colorbar_style, colorbar_reverse, store_pizza, store_toppings, store_year, state_pizza, state_toppings):
                
        #first check triggers and context 
        ctx = dash.callback_context 
        trigger = ctx.triggered[0]["prop_id"].split(".")[0] 
        #logger.info("Sunburst view callback. Trigger is %r, colorbar_style %r, colorbar_reverse % r", trigger, colorbar_style, colorbar_reverse)  
            
        # break out early on close
        if trigger == "modal-sunburst-close": return is_open, None, None, None, {}, "", [],[],None,None,None,None
        
        # build pizza drop down (list of dicts)
        dd = d.get_list_of_dataset_labels_and_raw(master_config,'quantitative')
        dropdownPizza=[]
        for i in range(0,len(dd)): dropdownPizza.append({'label': dd[i].get("dataset_label"), 'value': dd[i].get("dataset_raw")})
                
        # build toppings drop down (list of dicts)
        dd = d.get_list_of_dataset_labels_and_raw(master_config,'continuous')
        dropdownToppings=[]
        for i in range(0,len(dd)): dropdownToppings.append({'label': dd[i].get("dataset_label"), 'value': dd[i].get("dataset_raw")})
                
        #If no dcc store states returned for colorbar, set to defaults
        if colorbar_style == None: colorbar_style = INIT_COLOR_PALETTE        
        if colorbar_reverse == None: colorbar_reverse = INIT_COLOR_PALETTE_REVERSE
            
        #Fashion sunburst colour input as a string in the form "blue" or "blue_r" for reverse
        if colorbar_reverse == False: colorbar_sb = geomap_colorscale[int(colorbar_style)]
        else: colorbar_sb = geomap_colorscale[int(colorbar_style)]+"_r"      

        # tweak this to autoselect a quantitative series
        if trigger == "sunburst-button":
                
            # set setires to whatever the value of the pizza drop down is
            series = state_pizza
            color = state_toppings
            
            # if no second series
            if color == None:
                # check availble yrs and set to most recent, plus set the store year value
                availyrs = np.sort(pd.unique(pd.DataFrame(pop[(pop['Series']==series)], columns=['year'])['year'].astype(int)))
                #logger.info("Sunny busty Button push, avail yrs for this dataset are %r", availyrs)
                year = str(availyrs[-1])
                store_year = year
            
            else:  
                #find intersect years 
                x = series
                y = color                 
                dfx = np.sort(pd.unique(pd.DataFrame(pop[(pop['dataset_raw']==x)], columns=['year'])['year'].astype(int)))
                dfy = np.sort(pd.unique(pd.DataFrame(pop[(pop['dataset_raw']==y)], columns=['year'])['year'].astype(int)))
                years = reduce(np.intersect1d,(dfx,dfy))
                #logger.info("Intersect availble years with %r and %r is %r",x,y,years)            
                year = str(years[-1])
                store_year = year        
            
            # update variables to display
            series_label = master_config[series].get("dataset_label") +" vs "+master_config[color].get("dataset_label")                               
            source = master_config[series].get("source")        
            link = master_config[series].get("link") 
            sunburst_title = series_label+" ["+year+"]"        
          
            #logger.info("attempting to return\nyear %r\nseries_label %r\ntitle %r\nsource %r\nlink %r\nseries %r\npizza store %r\ntopping store %r",year, series_label, sunburst_title, source, link, series, store_pizza, store_toppings)
                    
            store_pizza = series
            store_toppings = color              
        
            return not is_open, sunburst_title, source, link, create_chart_sunburst(series, color, year, colorbar_sb), "", dropdownPizza, dropdownToppings, store_pizza, store_toppings, store_year,''
        
        elif trigger == 'sunburst-dropdown-pizza':              
            
            # set series to drop down value
            series = ddv_pizza
                    
            # if no second dataset, set year to most recent for this particular set
            if store_toppings == None:
                color = None
                #logger.info("No second datset found, setting to most recent year")
                year = str(np.sort(pd.unique(pd.DataFrame(pop[(pop['dataset_raw']==series)], columns=['year'])['year'].astype(int)))[-1])        
            
            else:        
                
                color = ddv_toppings
                
                #find intersect years 
                x = series
                y = color
                dfx = np.sort(pd.unique(pd.DataFrame(pop[(pop['dataset_raw']==x)], columns=['year'])['year'].astype(int)))
                dfy = np.sort(pd.unique(pd.DataFrame(pop[(pop['dataset_raw']==y)], columns=['year'])['year'].astype(int)))
                years = reduce(np.intersect1d,(dfx,dfy))
                #logger.info("Intersect availble years with %r and %r is %r",x,y,years)
                
                year = str(years[-1])     
                
            # Set variables we need            
            series_label = master_config[series].get("dataset_label") +" vs "+master_config[color].get("dataset_label") 
            sunburst_title = series_label+" ["+year+"]"        
            source=master_config[series].get("source")
            link=master_config[series].get("link") 
            store_pizza = series                
            store_toppings = color
            store_year = year
            
            #logger.info("attempting to return\nyear %r\nseries_label %r\ntitle %r\nsource %r\nlink %r\nseries %r\nddv %r\npizza store %r\ntoppings store %r",year, series_label, sunburst_title, source, link, series, ddv_pizza, store_pizza, store_toppings)
            
            return not is_open, sunburst_title, source, link, create_chart_sunburst(series, color, year, colorbar_sb), "", dropdownPizza, dropdownToppings,store_pizza, store_toppings, store_year,''
        
        elif trigger == 'sunburst-dropdown-toppings':
            
            series = store_pizza        
            color = ddv_toppings
            
            #find intersect years with whatever store_pizza and it have a baby with
            x = series
            y = ddv_toppings
            
            dfx = np.sort(pd.unique(pd.DataFrame(pop[(pop['dataset_raw']==x)], columns=['year'])['year'].astype(int)))
            dfy = np.sort(pd.unique(pd.DataFrame(pop[(pop['dataset_raw']==y)], columns=['year'])['year'].astype(int)))
            years = reduce(np.intersect1d,(dfx,dfy))
            #logger.info("Intersect availble years with %r and %r is %r",x,y,years)
            
            year = str(years[-1])        
                    
            # Gather variables we need            
            series_label = master_config[series].get("dataset_label")+" vs "+master_config[color].get("dataset_label")
            sunburst_title = series_label+" ["+year+"]"  
            source=master_config[series].get("source")
            link=master_config[series].get("link") 
            
            # set the stores
            store_pizza = series
            store_toppings = ddv_toppings                       
            store_year = year
            
            #logger.info("attempting to return\nyear %r\nseries_label %r\ntitle %r\nsource %r\nlink %r\nseries %r\nddv %r\npizza store %r\ntoppings store %r",year, series_label, sunburst_title, source, link, series, ddv_pizza, store_pizza, store_toppings)
            
            return not is_open, sunburst_title, source, link, create_chart_sunburst(series, color, year, colorbar_sb), "", dropdownPizza, dropdownToppings,store_pizza, store_toppings, store_year,''
        
        

    #Globe view modal callback
    @dash_app.callback([
        Output("dbc-modal-globe", "is_open"),
        Output("globe-body","children"),
        Output('my-loader-globe', "children"), #used to trigger loader. Use null string "" as output  
        Output("globe-modal-title", "children"),
        Output('globe-modal-footer', 'children'),
        Output('globe-modal-footer-link', 'children'),
        Output('my-loader-globe-refresh','children'),
        Output("my-url-globe-callback","data"),
        ],
        [
        Input("my-url-globe-trigger", "data"), 
        Input("globe-button", "n_clicks"), 
        Input("modal-globe-close", "n_clicks"),
        Input("modal-globe-jelly", "n_clicks"),
        Input("modal-globe-ne50m", "n_clicks"),
        ],
        [
        State("dbc-modal-globe", "is_open"),
        State("my-series", "data"), 
        State("year-slider", "value"),  
        State("year-slider", "marks"),
        State('my-settings_json_store', 'data'),
        State("geomap_figure", "figure"),
        State("my-settings_colorbar_reverse_store", 'data'),
        State("my-url-series", 'data'),
        State('url','href'),  
        State("my-url-view", 'data'),
        State("my-url-year", 'data'),
        ], 
        prevent_initial_call=True,
    )
    #@cache.memoize(timeout=CACHE_TIMEOUT)
    def callback_toggle_modal_globe(globe_trigger, n1, n2, n3, n4, is_open, series, yearid, yeardict, settings_json, map_data, colorbar_reverse, url_series, href, url_view, url_year):
        
        #first check triggers and context 
        ctx = dash.callback_context 
        trigger = ctx.triggered[0]["prop_id"].split(".")[0] #this is the series selection (component id from navbar top), except if the year slider is the trigger!!
        #logger.info("Globe view callback. Trigger is %r", trigger)
        
        # break out quickly on close
        if trigger == 'modal-globe-close': return not is_open, {}, None,None,None,None,None,None
        
        if trigger == 'my-url-globe-trigger':
            if globe_trigger != 'globe':
                #print("Breaking out of Globe callback!")
                raise PreventUpdate()
            else:
                # get year and override series
                year = url_year
                series = api_dict_label_to_raw[url_series]            
                
        else: year = str(d.get_years(pop.loc[(pop['dataset_raw'] == series)])[yearid])
        
        # set variables      
        series_label = master_config[series].get("dataset_label")
        source = master_config[series].get("source")
        link = master_config[series].get("link")
        var_type = master_config[series].get("var_type")
        title = series_label+" ["+str(year)+"]"  
        jellybean = False
        high_res = False    
        
        #Store continuous colorscale from map data and reverse if necessary    
        try:
            continuous_colorscale = map_data['data'][0]['colorscale'] #a list of colours e.g. [1.1111, #hexcolour] (does not reverse)
        except KeyError as error:
            print("Breaking out of globe callback. Map not ready")
            raise PreventUpdate()
        
        #Check if needs to be reversed from DCC store
        if colorbar_reverse == None: colorbar_reverse = INIT_COLOR_PALETTE_REVERSE
            
        #If not default, then reverse the colorscale (only thet second element of each element)
        if colorbar_reverse == False:
            #deep copy the array (prevents problems with assigning data)
            csr = copy.deepcopy(continuous_colorscale)        
            #reverse the colorscale
            csr = csr[::-1]      
            for i in range(0,len(csr)): continuous_colorscale[i][1] = csr[i][1]  
        
        if trigger == 'modal-globe-jelly':  jellybean = True        
        if trigger == 'modal-globe-ne50m':  high_res = True
                    
        # build url     
        blah = href.split('/') 
        root = blah[0]+'//'+blah[2]+'/'
        url = root + api_dict_raw_to_label[series] + '/'+str(year)+'/globe'
                
        #subset df
        df = pop[(pop["year"] == int(year)) & (pop["dataset_raw"] == series)].copy()  
        
        #update json for the two main resolution scenarios
        if not high_res:
            gj_land = d.update_3d_geo_data_JSON(df, geojson_globe_land_ne110m, continuous_colorscale, jellybean, var_type, discrete_colorscale) 
            gj_ocean = d.update_3d_geo_data_JSON(df, geojson_globe_ocean_ne110m, continuous_colorscale, jellybean, var_type, discrete_colorscale)
        
        else:
            gj_land = d.update_3d_geo_data_JSON(df, geojson_globe_land_ne50m, continuous_colorscale, jellybean, var_type, discrete_colorscale) 
            gj_ocean = d.update_3d_geo_data_JSON(df, geojson_globe_ocean_ne50m, continuous_colorscale, jellybean, var_type, discrete_colorscale)
        
        #create globe
        globe = create_chart_globe(gj_land, gj_ocean) 
        
        # keep modal open in these conditions
        if trigger == 'modal-globe-jelly' or trigger == 'modal-globe-ne50m': is_open = not is_open
                
        return not is_open, globe, "", title, source, link, "", url
        



    #Area51 view modal callback
    @dash_app.callback(
        [
        Output("dbc-modal-geobar", "is_open"),
        Output("geobar-test","children"),
        Output("geobar-modal-title", "children"),
        Output('my-loader-geobar', "children"), #used to trigger loader. Use null string "" as output
        Output('geobar-modal-footer', 'children'),        
        Output('geobar-modal-footer-link', 'children'),    
        Output("my-url-jigsaw-callback","data"),
        Output('my-loader-geobar-refresh','children'),
        ],
        [
        Input("my-url-jigsaw-trigger", "data"), 
        Input("geobar-button", "n_clicks"), 
        Input("modal-geobar-close", "n_clicks"),
        Input("modal-geobar-jelly", "n_clicks"),    
        ],
        [
        State("dbc-modal-geobar", "is_open"),
        State("my-series", "data"), #super useful. Use state of selections as global vars via state.
        State("year-slider", "value"),  
        State("year-slider", "marks"),
        State('my-settings_json_store', 'data'),
        State("geomap_figure", "figure"),
        State("my-settings_colorbar_reverse_store", 'data'),
        State('url','href'),  
        State("my-url-series", 'data'),
        State("my-url-view", 'data'),
        State("my-url-year", 'data'),        
        ], 
        prevent_initial_call=True,
    )
    def callback_toggle_modal_jigsaw(jigsaw_trigger, n1, n2, n3, is_open, series, yearid, yeardict, settings_json, map_data, colorbar_reverse,href, url_series, url_view, url_year):
        
        #first check triggers and context 
        ctx = dash.callback_context 
        trigger = ctx.triggered[0]["prop_id"].split(".")[0]
        
        # break out early on close
        if trigger == 'modal-geobar-close': return not is_open, {}, None,None,None,None,None,None
    
        
        if trigger == 'my-url-jigsaw-trigger':
            if jigsaw_trigger != 'jigsaw':
                #print("Breaking out of Jigsaw callback!")
                raise PreventUpdate()
            else:
                # get year and override series
                year = url_year
                series = api_dict_label_to_raw[url_series]  
        
        else: year = str(d.get_years(pop.loc[(pop['dataset_raw'] == series)])[yearid])
        
        #Gather variables we need    
        series_label = master_config[series].get("dataset_label")
        source = master_config[series].get("source")
        link = master_config[series].get("link")
        title = series_label+" ["+str(year)+"]"    
        jellybean = False         
            
        #determine colorscale and whether it is reverse/normal
        colorscale = map_data['data'][0]['colorscale'] #an list of colours e.g. [1.1111, #hexcolour] (does not reverse)
        
        #default
        if colorbar_reverse == None:  colorbar_reverse = INIT_COLOR_PALETTE_REVERSE        
        
        #Logic to reverse colorscale. It seems counterintuitive. Don't ask, this is fucky logic but it works. It's because I can't control underlying map color array
        #it could be to do is all my dev was done on the initial color setting being false, which means I built the logic on the color array I return from map around that, which was originally already reversed.
        if colorbar_reverse == False:
            #print("REVERSING COLORSCALE!!")
            #deep copy the array (prevents problems with assigning data)
            csr = copy.deepcopy(colorscale)        
            #reverse the colorscale
            csr = csr[::-1]      
            for i in range(0,len(csr)):
                colorscale[i][1] = csr[i][1] 
        
        #make a deep copy of the json data 
        if settings_json is None: gj = copy.deepcopy(geojson_LOWRES)
            
        else:
            #logger.info("Area51 callback: dcc store for geojson found, loading")        
            if int(settings_json) == 0: gj = copy.deepcopy(geojson_LOWRES)           
            elif int(settings_json)==1: gj = copy.deepcopy(geojson_MEDRES)          
            elif int(settings_json)==2: gj = copy.deepcopy(geojson_HIRES)
        
        if trigger == 'modal-geobar-jelly': jellybean = True           
        
        # build url    
        blah = href.split('/') 
        root = blah[0]+'//'+blah[2]+'/'
        url = root + api_dict_raw_to_label[series] + '/'+str(year)+'/jigsaw'        

        # build figure  
        geobar = create_chart_geobar(series, year, colorscale, gj, jellybean)        
        
        # keep modal open in these conditions
        if trigger == 'modal-geobar-jelly': is_open = not is_open 
            
        return not is_open, geobar, title, "", source, link, url,'' 
        




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


    #Settings modal callback (settings button push)
    @dash_app.callback(
        Output("dbc-modal-settings", "is_open"),
        [
        Input("settings-button", "n_clicks"), 
        Input("modal-settings-apply", "n_clicks"),
        Input("modal-settings-close", "n_clicks"),
        ],
        [
        State("dbc-modal-settings", "is_open")    
        ], 
        prevent_initial_call=True,
    )
    def callback_toggle_modal_settings(n1, n2, n3, is_open):
        if n1 or n2 or n3:
            logger.info("Modal Settings triggered")
            return not is_open    
        return is_open


    
    #downloadland modal callback
    @dash_app.callback(
        [
        Output("dbc-modal-download-land", "is_open"),
        Output('downloads-countries-selector', 'options'),
        Output('downloads-series-selector','options'),
        Output('downloads-year-selector','options'),        
        ],     
        [
        Input("btn-popover-map-download-land", "n_clicks"),
        Input("btn-popover-bar-download-land", "n_clicks"),
        Input("btn-popover-line-download-land", "n_clicks"),
        Input("btn-popover-bubble-download-land", "n_clicks"),
        Input("btn-popover-sunburst-download-land", "n_clicks"),
        Input("modal-downloads-close", "n_clicks")
        ],
        [
        State("dbc-modal-download-land", "is_open")
        ], 
        prevent_initial_call=True,
    )
    def callback_toggle_modal_downloads(n1, n2, n3, n4, n5, n6, is_open):
            
        #first check triggers and context 
        ctx = dash.callback_context 
        trigger = ctx.triggered[0]["prop_id"].split(".")[0]
        #print('dl modal trigger is ',trigger)

        # break out if close button pushed
        if trigger == 'modal-downloads-close': return not is_open, [],[],[]

        # build dropdown list of unique countries  
        
        # Find the unique countries for this dataset (all years) and sort 
        dd = np.sort(pd.unique(pop["country"])) #numpy array     
        
        #refresh list of country labels and vals for the dropdown
        dropdown_countries=[]
        for i in range(0,len(dd)):
            dropdown_countries.append({'label': dd[i], 'value': dd[i]})              

        # build dropdown list of unique series
        
        # Find the unique series for this dataset (all years) and sort 
        dd = np.sort(pd.unique(pop["dataset_raw"])) 
        
        #drop first 10 rows as they are horrible
        dd = dd[17:]

        #refresh list of series labels for the dropdown
        dropdown_series=[]
        for i in range(0,len(dd)):
            dropdown_series.append({'label': dd[i], 'value': dd[i]})

        # build dropdown list of unique years
        
        # Find the unique series for this dataset (all years) and sort 
        dd = np.sort(pd.unique(pop["year"])) 

        #refresh list of year labels for the dropdown
        dropdown_years=[]
        for i in range(0,len(dd)):
            dropdown_years.append({'label': dd[i], 'value': dd[i]})

        if n1 or n2 or n3 or n4 or n5 or n6 : return [not is_open], dropdown_countries, dropdown_series, dropdown_years
        
  

    # Display experimental modal 
    @dash_app.callback(
        Output("dbc-modal-experiments", "is_open"),
        Output('xp-modal-title', 'children'),
        Output('xp-modal-body', 'children'),
        Output('my-loader-xp', "children"), #used to trigger loader. Use null string "" as output
        Input("my-experimental-trigger", "data"), #trigger for experimental modal  
        State("dbc-modal-experiments", "is_open"),
        State("my-series-label", 'data'), 
        prevent_initial_call=True
        )
    def callback_toggle_modal_experiments(trigger, is_open, series):

        if trigger == "Creme freesh": return [not is_open], series, create_chart_globe_powerstations_xp1(), ''
        
        return is_open, series, None, ''


    # clear the search box after any search or nav menu selection
    @dash_app.callback(
        Output("nav-search-menu", 'value'),
        Input("my-series",'data'),
        #State(),
        prevent_initial_call=True
        )
    def callback_clear_search_menu_helper(data):        
        return "hi"



    #Helper chain callback to clear dataset dropdown for bar graph
    @dash_app.callback(
        [Output('bar-graph-dropdown-dataset', 'value'),
        Output('bar-graph-dropdown-year', 'value'),
        ],
        [Input("bar-button", "n_clicks"),
        Input("bar-graph-dropdown-dataset", "options"),     
        ],
        [State('bar-graph-dropdown-dataset', 'value'),
        State('bar-graph-dropdown-year', 'value'),
        ],
        prevent_initial_call=True
    )
    def callback_toggle_modal_bar_clear_dropdown_helper(n, options, val, valyr):
        # The purpose of this callback is to clear or set the bar graph modal dataset drop down upon click.
        
        ctx = dash.callback_context 
        trigger = ctx.triggered[0]["prop_id"].split(".")[0]
        
        #logger.info("bar dropdown helper\ntrigger is %r\nval is %r\noptions: %r\n",trigger, val, options)
            
        #if first run from main map, clear the dropdowns
        if trigger == 'bar-button':
            return "",""
        
        else:
            #must be change to dataset. Check if it is clear
            if val == None:
                #print("dataset clear. ok to clear stuff")
                return "",""
            else:
                #print("dataset not clear, setting val to what it was selected as")
                return val, valyr #may need to set year here too
                    


    #Helper chain callback to clear dataset dropdown for line graph
    @dash_app.callback(
        [Output('line-graph-dropdown-dataset', 'value'), ],
        [Input("line-button", "n_clicks"), ],
        [State('line-graph-dropdown-dataset', 'value'), ],
        prevent_initial_call=True
    )
    def callback_toggle_modal_line_clear_dropdown_helper(n,val):
        #logger.info("\n\nHI val is %r\n\n",val)
        return [""]


    #Line graph modal helper
    @dash_app.callback(
        [
        Output("line-graph-dropdown-countries", "value"), 
        #Output('line-graph','style'),
        ],
        [    
        Input("linegraph-allcountries-button", "n_clicks"), 
        Input("linegraph-nocountries-button", "n_clicks"),  
        ],
        [     
        State('line-graph-dropdown-countries', 'options'),           
        ],
        prevent_initial_call=True
    )
    def callback_toggle_modal_line_allcountries_helper(n1,n2, countries_options):
        ctx = dash.callback_context 
        trigger = ctx.triggered[0]["prop_id"].split(".")[0] 
        
        if trigger == 'linegraph-allcountries-button':
            style={"backgroundColor": "#1a2d46", 'color': '#ffffff', 'height': 1000}
            countries=[]
            for i in range(0,len(countries_options)):
                countries.append(countries_options[i]['label'])            
            return [countries] #, style
        
        elif trigger == 'linegraph-nocountries-button':
            style={"backgroundColor": "#1a2d46", 'color': '#ffffff', 'height': INIT_BAR_H}
            return [''] #, style


    #Helper chain callback to preselect year for bubble graph
    @dash_app.callback(
        [Output('bubble-graph-dropdownyear', 'value'), ],
        [Input('bubble-graph-dropdownyear', 'options'), ],
        [State('bubble-graph-dropdownyear', 'value'), ],
        prevent_initial_call=True
    )
    def callback_toggle_modal_bubble_preset_year_helper(options, val):
        #logger.info("\n\nyear helper val is %r\nval length %r\nstate val %r",options, len(options), val)
        
        #check if state val dict, and convert if so
        if type(val) is dict:
            print("helper: converting state val from dict")
            val = val['value']
        
        
        #if list is empty (default None) we need to return "" as we cannot return None
        if len(options) == 0:
            print("bubble helper:return empty")
            return [""]
        
        #if we have a value selected by the user
        elif val != None and val != '':        
            #loop through options list and return the one corresponding to the selection (i.e. reselect the same value)
            for i in range(0,len(options)):
                #logger.info("checking %r against %r",options[i]['value'], val)
                if options[i]['value'] == val:
                    #logger.info("bubble helper: returning %r",[options[i]])
                    return [options[i]]
            
            #if not found it means the current val of the drop down does not match available years (i.e. dataset change made list smaller)
            return [options[-1]]
            
        #otherwise autoselect the most recent year available in the list (as there is no selection)    
        else:
            #logger.info("bubble helper: returning most recent: %r",options[-1])
            return [options[-1]]



    @dash_app.callback(
        [Output("bubble-graph-dropdownX", "value"),
        Output("bubble-graph-dropdownY", "value"),
        Output("bubble-graph-dropdownZ", "value"),
        Output("chklist-bubble-log", "value"),
        ],
        Input("modal-bubble-examplebtn", "n_clicks"),
        Input('modal-bubble-resetbtn','n_clicks'),
        prevent_initial_call=True
    )
    def callback_toggle_modal_bubble_example_helper(n1,n2):    
        #this call back simply sets the dropdown values to presets for an example
        ctx = dash.callback_context 
        trigger = ctx.triggered[0]["prop_id"].split(".")[0]
        
        if trigger == 'modal-bubble-examplebtn':    
            return 'GDP/capita (US$, inflation-adjusted)', 'Life expectancy at birth, data from IHME', 'Population, total', 'x' #must be dataset_raw (not labels)
        elif trigger == 'modal-bubble-resetbtn':
            return "","","",""
        


    @dash_app.callback(
        [
        Output('sunburst-dropdown-pizza','value'),
        Output('sunburst-dropdown-toppings','value'),
        ],
        Input("modal-sunburst-examplebtn", "n_clicks"),
        #Input('modal-bubble-resetbtn','n_clicks'),
        prevent_initial_call=True
    )
    def callback_toggle_modal_sunburst_example_helper(n1):    
        #this call back simply sets the dropdown values to presets for an example
        #ctx = dash.callback_context 
        #trigger = ctx.triggered[0]["prop_id"].split(".")[0]
        
        return 'Population, total', 'Life expectancy at birth, data from IHME'
    

    #Setup Caching (use memcachier on heroku. Got it working but no noticable benefit, plus in production it will likely cost big $$)
    #https://devcenter.heroku.com/articles/flask-memcache

    '''
    cache = Cache()
    CACHE_TIMEOUT = 3600 #1hr in seconds
    cache_servers = os.environ.get('MEMCACHIER_SERVERS')
    logger.info("Cache servers: %r", cache_servers)
    if cache_servers != None:
        logger.info("Memcachier servers located, initialising cache settings")
        cache_user = os.environ.get('MEMCACHIER_USERNAME') or ''
        cache_pass = os.environ.get('MEMCACHIER_PASSWORD') or ''
        cache.init_app(app.server,
            config={'CACHE_TYPE': 'saslmemcached',
                    'CACHE_MEMCACHED_SERVERS': cache_servers.split(','),
                    'CACHE_MEMCACHED_USERNAME': cache_user,
                    'CACHE_MEMCACHED_PASSWORD': cache_pass,
                    'CACHE_OPTIONS': { 'behaviors': {
                        # Faster IO
                        'tcp_nodelay': True,
                        # Keep connection alive
                        'tcp_keepalive': True,
                        # Timeout for set/get requests
                        'connect_timeout': 2000, # ms
                        'send_timeout': 750 * 1000, # us
                        'receive_timeout': 750 * 1000, # us
                        '_poll_timeout': 2000, # ms
                        # Better failover
                        'ketama': True,
                        'remove_failed': 1,
                        'retry_timeout': 2,
                        'dead_timeout': 30}}})

    else:
        logger.info("Caching on local filesystem")
        cache = Cache(app.server, config={
        'CACHE_TYPE': 'filesystem',
        'CACHE_DIR': 'cache-directory'
        })  
        
    '''

    return






















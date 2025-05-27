
#use debug flag to determine whether to pull data from cloud or repo
# invoke with
# python3.12 -d blah.py

#successfully used brotli to compress master file hard from 97MB to 54MB. Nice.
#going forward this means could periodically download titanium container and put into repo.

#can't download folders directly from storage explorer (maybe on the proper app version??) but not
# in browser version. Maybe make script that does this so it can be done easily in future?

# script: pull titanium subfolders to new folder location called snapshot in /data/data_snapshot

# 1. Get snapshot of processed data into repo [DONE]
# 2 Test debug mode can succesfully pull from different sources [DONE]
# See if can do this via docker (i.e. can I run docker image in debug mode from cmd line? for other users) [DONE]
# 3 Begin the process of refactoring and rebuilding. First update to latest dash version etc. 


import sys
sys.path.append('/usr/src/app/data') #working dir for built container (see /Dockerfile)
sys.path.append('/home/dan/atlas/data') #testing on local machine (no docker)
import logging
from . global_constants import *
from . import data  # run-time helpers
from src.data_pipeline.data_paths import * 
import dash_bootstrap_components as dbc
from dash import dash, html, dcc
from . import dash_html #index page
import plotly.express as px
import plotly.graph_objs as go

# Get debug flag 
#debug_mode = sys.flags.debug # determines if cloud or local data ingested
debug_mode = 1

# setup logger to console
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("atlas")


# load app data object into memory
dobj = data.load(debug_mode)
print('Data successfully loaded.')


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
    create_dash_layout(dash_app) # INTERNAL ERROR IS PROBABLY BECAUSE THERE IS NO LAYOUT

    # Initialize callbacks after our app is loaded
    #init_callbacks(dash_app)

    return dash_app.server


def create_dash_layout(app):

    #CONSTRUCT DASH LAYOUT
    
    # Favicon and title
    app._favicon = ("favicon.ico") #must be in /assets/favicon.ico 
    app.title = "WORLD ATLAS 2.0" #browser tab
    
    # index.html template page structure
    app.index_string = dash_html.index_string      
    
    # Header
    header = create_dash_layout_header()
    
    # Navigation menu    
    #navbar = create_dash_layout_navbar()    
    
    # Body (i.e. the map centrepiece,)
    body = create_dash_layout_body()     
       
    # Build low navigation menu                      
    #footer = create_dash_layout_nav_footer()  
    footer = html.Div([html.Br(), html.Br(), dcc.Markdown(""" ### Built with ![Image](heart.png) in Python using [Dash](https://plotly.com/dash/)""")])
    
    # dcc stores for settings
    #dcc_stores = create_dash_layout_dcc_stores()        
        
    #hidden div triggers (for chaining callbacks)
    #hidden_div_triggers = create_dash_hidden_div_triggers()
    
    #enable special clientside callbacks
    #js_callback_clientside_blur(app)
    #js_callback_clientside_share(app)
    #js_callback_clientside_viewport(app) 

    # enable pathname API queries
    #api = dcc.Location(id='url', refresh=False) 
    
    # Assemble dash layout 
    #app.layout = html.Div([navbar, header, body, nav_footer, dcc_stores, hidden_div_triggers, api]) 
    app.layout = html.Div([header, body, footer])     
    
    
    return app



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
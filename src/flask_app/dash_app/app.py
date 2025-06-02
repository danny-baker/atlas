
# run app
# uv run atlas.py

# script: pull titanium subfolders to new folder location called snapshot in /data/data_snapshot

# 1. Get snapshot of processed data into repo [DONE]
# 2 Test debug mode can succesfully pull from different sources [DONE]
# See if can do this via docker (i.e. can I run docker image in debug mode from cmd line? for other users) [DONE]

# Get overhead menu working.It's close. Do a dummy one and work out what style is needed so they float. It's like eachone added is an inlineblock so it takes a new row rather than flex. PRetty sure it's just css style.

# Get footer running ok
# Port rest of app_old.py across
# Get a map displaying data (see what free tilemaps are now available. Xp here.)
# Refactor and make nice.
# Build note...when call uv build, want to build into a container, not a package. See if that's possible.



import sys
sys.path.append('/usr/src/app/data') #working dir for built container (see /Dockerfile)
sys.path.append('/home/dan/atlas/data') #testing on local machine (no docker)
import logging, os
from . global_constants import *
from . import data  # run-time helpers
from src.data_pipeline.data_paths import * 
import dash_bootstrap_components as dbc
from dash import dash, html, dcc
import plotly.express as px
import plotly.graph_objs as go
from . import layout_html, layout_footer, layout_body, layout_header, layout_navmenu
import pandas as pd

# Get debug flag 
#debug_mode = sys.flags.debug # determines if cloud or local data ingested
debug_mode = 1

# setup logger to console
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(LOGGER)

# load all run-time data
dobj = data.load(debug_mode)
print(dobj.dataset_count, dobj.observation_count)

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

    create_dash_layout(dash_app) 

    #init_callbacks(dash_app)

    return dash_app.server


def create_dash_layout(app):

    #CONSTRUCT DASH LAYOUT

    app._favicon = FAVICON
    app.title = TAB_TITLE 
    app.index_string = layout_html.index_string     

    navmenu = layout_navmenu.build(dobj)   
  
    header = layout_header.build()
    
    body = layout_body.build() 
       
    footer = layout_footer.build()
    
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
    app.layout = html.Div([navmenu, header, body, footer])     
    
    
    return app









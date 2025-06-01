
# run app
# uv run atlas.py

# script: pull titanium subfolders to new folder location called snapshot in /data/data_snapshot

# 1. Get snapshot of processed data into repo [DONE]
# 2 Test debug mode can succesfully pull from different sources [DONE]
# See if can do this via docker (i.e. can I run docker image in debug mode from cmd line? for other users) [DONE]

#2.5 Get footer running ok

# 3 Get overhead menu working
# 4 Get a map displaying data (see what free tilemaps are now available. Xp here.)
# 5 Port rest of app_old.py across
# 6 Refactor and make nice.

# Each major component make as a separate file. Way cleaner. Refactor the current ones before moving on baby.
# This file should be silky clean and happy.
# layout_navbar
# layout_footer
# layout_body
# callback logic might live here, but definitely not layout bullshit. It's too messy.

# Continue work L151 layout_footer.py.... adding in each modal as sep files.

import sys
sys.path.append('/usr/src/app/data') #working dir for built container (see /Dockerfile)
sys.path.append('/home/dan/atlas/data') #testing on local machine (no docker)
import logging
from . global_constants import *
from . import data  # run-time helpers
from src.data_pipeline.data_paths import * 
import dash_bootstrap_components as dbc
from dash import dash, html, dcc
import plotly.express as px
import plotly.graph_objs as go
from . import layout_html, layout_footer, layout_body, layout_header


# Get debug flag 
#debug_mode = sys.flags.debug # determines if cloud or local data ingested
debug_mode = 1

# setup logger to console
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(LOGGER)

# load all run-time data
dobj = data.load(debug_mode)

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

    #navbar = create_dash_layout_navbar()    
  
    header = layout_header.build_header()
    
    body = layout_body.build_body() 
       
    footer = layout_footer.build_footer()
    
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









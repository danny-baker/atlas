# RUN
# uv run atlas

# TASKS
# Get overhead menu working. [DONE]
# Create callbacks file. [DONE]
# All prop ids are global (good) [DONE]
# Get main callback running (bring in states, they should all be defined now.) Basic run [DONE]
# Can select dataset and map displays [DONE]
# Get footer running ok [DONE]
# about modal [DONE]
# user guide modal [DONE]
# Get timeslider working [DONE]
# Bar chart [DONE]

# Line chart ... basic working. Needs hovertip cleanups and some testing.

# Bubble chart?
# Geobar
# Globe
# Settings
# URL path working
# Finishing. CSS clean up (formatting and finishing touches. E.g. modal left align for footer. Make yr slider sexy etc)
# Port rest of app_old.py across. i.e. delete app_old.py

# Build note...when call uv build, want to build into a container, not a package. See if that's possible.



import sys
sys.path.append('/usr/src/app/data') #working dir for built container (see /Dockerfile)
sys.path.append('/home/dan/atlas/data') #testing on local machine (no docker)
import logging, os
from . global_constants import *
from . layout_navmenu import *
from . callbacks import *
from . import data  # run-time helpers
from data_pipeline.data_paths import * 
import dash_bootstrap_components as dbc
from dash import Dash, html, Input, Output, ctx, callback, dcc
import plotly.express as px
import plotly.graph_objs as go
from . import layout_html, layout_footer, layout_body, layout_header, layout_navmenu, layout_dcc_stores, layout_hidden_divs, callbacks
import pandas as pd

# Get debug flag 
#debug_mode = sys.flags.debug # determines if cloud or local data ingested
debug_mode = 1

# setup logger to console
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(LOGGER)

# load all run-time data
dobj = data.load(debug_mode)
print(f"dobj: dataset count: {dobj.dataset_count}, observations: {dobj.observation_count}")

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

    init_callbacks(dash_app, dobj)

    #testing
    #all_ids = get_component_ids(dash_app.layout)
    #print(all_ids)
    #if "random-button" in all_ids:
        #print("Random button is FOUND!!!")

    #Testing
    #print('url dict example below')
    #print(dobj.api_dict_label_to_raw)

    return dash_app.server


def get_component_ids(layout):
    #Helper to return all component ids in the dash layout (for testing)
    ids = []
    if hasattr(layout, "id") and layout.id:
        ids.append(layout.id)
    if hasattr(layout, "children"):
        if isinstance(layout.children, list):
            for child in layout.children:
                ids.extend(get_component_ids(child))
        else:
            ids.extend(get_component_ids(layout.children))
    return ids



def create_dash_layout(app):

    app._favicon = FAVICON
    app.title = TAB_TITLE 
    app.index_string = layout_html.index_string     

    navmenu = layout_navmenu.build(dobj)   
  
    header = layout_header.build()
    
    body = layout_body.build() 
       
    footer = layout_footer.build()
    
    dcc_stores = layout_dcc_stores.build()        
           
    hidden_div_triggers = layout_hidden_divs.build() # for chaining callbacks
    
    url = dcc.Location(id='url', refresh=False) # enable pathname API queries    
  
    app.layout = html.Div([navmenu, header, body, footer, dcc_stores, hidden_div_triggers, url])    

    #enable special clientside callbacks
    js_callback_clientside_blur(app)
    #js_callback_clientside_share(app)
    #callbacks.js_callback_clientside_viewport(app)      
    

    return app


        










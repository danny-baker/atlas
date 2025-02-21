
#use debug flag to determine whether to pull data from cloud or repo
# invoke with
# python3.12 -d blah.py

#successfully used brotli to compress master file hard from 97MB to 54MB. Nice.
#going forward this means could periodically download titanium container and put into repo.

#can't download folders directly from storage explorer (maybe on the proper app version??) but not
# in browser version. Maybe make script that does this so it can be done easily in future?

# script: pull titanium subfolders to new folder location called snapshot in /data/data_snapshot

# 1. Get snapshot of processed data into repo (DONE)
# 2 Test debug mode can succesfully pull from different sources
# See if can do this via docker (i.e. can I run docker image in debug mode from cmd line? for other users)
# 3 Begin the process of refactoring and rebuilding. First update to latest dash version etc. 


import sys
sys.path.append('/usr/src/app/data') #working dir for built container (see /Dockerfile)
sys.path.append('/home/dan/atlas/data') #testing on local machine (no docker)
import logging
#from global_constants import *
from . import global_constants
from . import data  # run-time helpers
from data_paths import * 
import dash
import dash_bootstrap_components as dbc
from dash import html
from . import dash_html #index page

# Get debug flag 
debug_mode = sys.flags.debug # determines if cloud or local data ingested
debug_mode = 1

# setup logger to console
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("atlas")


# load app data into memory
pop = data.load(debug_mode)

print('Data successfully loaded....blahpidy')

t = pop.globe_land_hires
m = pop.globe_land_lowres
d = pop.stats
xp = pop.EXP_POWER_PLANTS_DF
config_key_dsraw = pop.config_key_dsraw
config_key_dsid = pop.config_key_dsid
config_key_navcat = pop.config_key_navcat

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
    
    #create_dash_layout(dash_app) # INTERNAL ERROR IS PROBABLY BECAUSE THERE IS NO LAYOUT

    # Initialize callbacks after our app is loaded
    #init_callbacks(dash_app)

    return dash_app.server
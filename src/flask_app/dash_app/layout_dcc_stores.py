from dash import html, dcc
from . global_constants import *
import logging

#Obtain the root logger
logger = logging.getLogger(LOGGER)

def build():  
    
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

        dcc.Store(id="flag-bar", storage_type='memory'), 
        dcc.Store(id="fire-bar", storage_type='memory'), 

        dcc.Store(id="flag-line",storage_type='memory'), 
        dcc.Store(id="fire-line",storage_type='memory'), 

        ]) 
    return dcc_stores
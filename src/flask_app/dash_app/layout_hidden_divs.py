from dash import html
from . global_constants import *
import logging

#Obtain the root logger
logger = logging.getLogger(LOGGER)

def build():  
    
    triggers = html.Div([
        #html.Div("Test div", id="timeslider-hidden-div", style={"display":"none"}), #CRITICAL. Hidden div for triggering main callback from secondary time-slider callback.
        html.Div("Test div", id="settings-hidden-div", style={"display":"none"}), #CRITICAL. Hidden div for triggering main callback from settings modal updates
        html.Div("Test div", id="blur-hidden-div", style={"display":"none"}),
        html.Div("Test div", id="blur-hidden-div-menu", style={"display":"none"}),
        html.Div("Test div", id="js-social-share-refresh", style={"display":"none"}),
        html.Div("Test div", id="js-social-share-dummy", style={"display":"none"}),        
        html.Div("Test div", id="js-detected-viewport-dummy", style={"display":"none"}),

        ],style={"display":"none"})
    
    return triggers

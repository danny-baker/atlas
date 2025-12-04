from dash import html
from . global_constants import *
import logging

#Obtain the root logger
logger = logging.getLogger(LOGGER)

def build():  
    
    triggers = html.Div([        
        html.Div("Test div", id="settings-hidden-div", style={"display":"none"}), #CRITICAL. Hidden div for triggering main callback from settings modal updates (could probably be dcc store)
        html.Div("Test div", id="blur-hidden-div", style={"display":"none"}),
        html.Div("Test div", id="blur-hidden-div-menu", style={"display":"none"}),        

        ],style={"display":"none"})
    
    return triggers

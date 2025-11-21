from dash import dash, html, dcc
import dash_bootstrap_components as dbc
from . global_constants import *


def build():
            
    #title of app in page
    title = html.Div([
        html.Span(PAGE_TITLE, style={"marginBottom": 0,
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
                children=html.Span("\u00A0No data selected\u00A0", id="my-loader-main", style={"marginBottom": 0, "marginTop": 10, "marginLeft": 0, 'textAlign': 'center', 'fontSize': INIT_SELECTION_H, 'fontFamily': 'Helvetica', 'fontWeight': '', 'backgroundColor': INIT_TITLE_BG_COL, 'opacity': INIT_TITLE_OPACITY  },), #style of span
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
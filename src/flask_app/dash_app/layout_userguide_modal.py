from dash import dash, html, dcc
import dash_bootstrap_components as dbc
from . global_constants import *

def build():
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
            dialog_style={"max-width": "none", "width": INIT_UGUIDE_MODAL_W}  
        )
    return m
from dash import dash, html, dcc
import dash_bootstrap_components as dbc
from . global_constants import *
from . import layout_modal


def build():    
       
    m = dbc.Modal(
            [
                dbc.ModalHeader(html.Div("This site is a front-end to thousands of datasets.", style={"fontFamily":INIT_MODAL_HEADER_FONT_GENERAL, "fontSize": INIT_MODAL_HEADER_FONT_SIZE, "fontWeight": INIT_MODAL_HEADER_FONT_WEIGHT })),
                dbc.ModalBody(layout_modal.about_modal_body),
                dbc.ModalFooter([
                    dcc.Markdown(""" Built with ![Image](/static/img/heart1.png) in Python using [Dash](https://plotly.com/dash/)."""),
                    dbc.Button("Close", id="modal-about-close", className="ml-auto",size=INIT_BUTTON_SIZE)
                    ]
                ),
                #html.Div([html.Audio(id='audio', src='/static/img/encarta_intro.mp3', autoPlay=True, loop=False )]) #,controls=True
                
                
            ],
            id="dbc-modal-about",
            centered=True,
            size="xl",
            style={"max-width": "none", "width": INIT_ABOUT_MODAL_W}  #70%
        )
    return m
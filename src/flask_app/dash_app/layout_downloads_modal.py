# This is experimental and currently not used as it loaded the server (takes a full worker for a while to run)
# probably need another approach.

from dash import dash, html, dcc
import dash_bootstrap_components as dbc
from . global_constants import *


def build():
    m = dbc.Modal(
            [
                dcc.Download(id='download_object_downloads_modal'), 
                
                #dbc.ModalHeader(html.Div( /static/img/rainbow2.png) Download Land ![Image](/static/img/rainbow1.png) """), style={"fontFamily":INIT_MODAL_HEADER_FONT_GENERAL, "fontSize": INIT_MODAL_HEADER_FONT_SIZE, "fontWeight": INIT_MODAL_HEADER_FONT_WEIGHT }),
                dbc.ModalHeader(
                    html.Div([
                        html.Img(src='/static/img/rainbow2.png', width=50),
                        html.Div("Download Land", style={"fontFamily":INIT_MODAL_HEADER_FONT_GENERAL, "fontSize": INIT_MODAL_HEADER_FONT_SIZE, "fontWeight": INIT_MODAL_HEADER_FONT_WEIGHT, 'padding-left':20, 'padding-right':20 }),
                        html.Img(src='/static/img/rainbow1.png', width=50),  
                    ],style={'display':'flex', 'align-items': 'center', 'justify-content': 'center', 'background-color':'transparent'}),
                style={'background-color':'transparent', 'align-items':'center', 'justify-content': 'center'}
                    
                ),
                
                dbc.ModalBody([                    

                    dcc.Markdown(""" 
                        Welcome to a magical place where dreams come true. 
                        Here you can export larger chunks of data beyond what the other download buttons can do.
                        For example, you might want all available data just for two regions of the world, or all available data in a given year.
                        Please be aware the tools below are live-querying the main dataset and preparing a zipped comma-separated-value (CSV) file.                      To minimise file size and query load, I've stripped out source information. 
                        Please also note you are getting the raw series names as they originally came, and not my curated re-labelled series names.
                        This area is really intended for advanced users who are comfortable working with datasets larger than 100,000 rows.
                        
                        
                        #### How do you like your data sliced?
                    """),

                    dbc.Row([
                        dbc.Card(
                        [                            
                            dbc.CardHeader(html.H5("Series")),
                            dbc.CardBody([  
                                html.Div("Download all available data (i.e. all regions, all years) for the selected series."),
                                html.Br(),
                                dcc.Dropdown(
                                    options=[],
                                    id="downloads-series-selector",
                                    multi=True,
                                    placeholder='Select series',
                                ),
                                html.Br(),
                                dbc.Button("Download ZIP", size=INIT_BUTTON_SIZE, outline=True, active = True, color="success", id='btn-downloads-series'),                                
                            ]),
                        ],
                        style={"width": '100%', "marginBottom": 0, "marginTop": '1vw', "marginLeft": 0, "marginRight": '1vw'},
                        ),
                    ], style={"marginBottom": 0, "marginTop": 0, "marginLeft": 0, "marginRight": 0, }), #end row
                    
                    dbc.Row([
                     
                        dbc.Card(
                        [                            
                            dbc.CardHeader(html.H5("country/Region")),
                            dbc.CardBody([  
                                html.Div("Download all available data (i.e. all data series) for the selected countries."),
                                html.Br(),
                                dcc.Dropdown(
                                    options=[],
                                    id="downloads-countries-selector",
                                    multi=True,
                                    placeholder='Select countries',
                                ),
                                html.Br(),
                                dbc.Button("Download ZIP", size=INIT_BUTTON_SIZE, outline=True, active = True, color="success", id='btn-downloads-countries'),
                            ]),
                        ],
                        style={"width": INIT_SETTINGS_DL_CARD_WIDTH, "marginBottom": 0, "marginTop": '1vw', "marginLeft": 0, "marginRight": '1vw' },
                        ),                       
                        
                        
                        dbc.Card(
                        [
                            dbc.CardHeader(html.H5("year")),
                            dbc.CardBody([ 
                                html.Div("Download all available data (i.e. all data series, all regions) for the selected year(s)."),
                                html.Br(),
                                dcc.Dropdown(
                                    options=[],
                                    id="downloads-year-selector",
                                    multi=True,
                                    placeholder='Select years',
                                ),
                                html.Br(),
                                dbc.Button("Download ZIP", size=INIT_BUTTON_SIZE, outline=True, active = True, color="success", id='btn-downloads-years'),
                            ]),
                        ],
                        style={"width": INIT_SETTINGS_DL_CARD_WIDTH, "marginBottom": 0, "marginTop": '1vw', "marginLeft": 0, "marginRight": '1vw'},
                        ),

                        dbc.Card(
                        [                            
                            dbc.CardHeader(html.H5("Everything")),
                            dbc.CardBody([ 
                                html.Div("Download the entire dataset (2500+ series) as a zipped CSV. Advanced users only."),
                                html.Br(),
                                html.Div("Allow up to 1 min to process. TEMPORARILY DISABLED"),
                                html.Br(),
                                dbc.Button("Download ZIP (136MB)", size=INIT_BUTTON_SIZE, outline=True, active = True, color="success", id='btn-downloads-all-data', style={'padding-top':5}, disabled=True),
                            ]),
                        ],
                        style={"width": INIT_SETTINGS_DL_CARD_WIDTH,"marginBottom": 0, "marginTop": '1vw', "marginLeft": 0, "marginRight": '1vw' },
                        ),
                        
                        
                    ], style={"marginBottom": 0, "marginTop": 0, "marginLeft": 0, "marginRight": 0, }), #end row 

                    dcc.Loading(                            
                        type=INIT_LOADER_TYPE,
                        color=INIT_LOADER_CHART_COLOR, 
                        children=html.Span(id="my-spinner-dl-series"),
                        style={"zIndex":1, 'display': 'flex', 'vertical-align': 'center' , 'align-items': 'center', 'justify-content': 'center'},
                    ),

                                  
                dbc.Tooltip(
                        "Temporarily disabled to preserve server availability. Solution coming soon.",
                        target='btn-downloads-all-data',
                        placement='top',                        
                    ), 

                dbc.Tooltip(
                        "Click this button and wait patiently for download to start. Expect ~5s processing time per country selected.",
                        target='btn-downloads-countries',
                        placement='top',                        
                    ), 

                dbc.Tooltip(
                        "Click this button and wait patiently for download to start. Expect ~5s processing time per series selected.",
                        target='btn-downloads-series',
                        placement='top',                        
                    ), 
                
                dbc.Tooltip(
                        "Click this button and wait patiently for download to start. Expect ~5s processing time per year selected.",
                        target='btn-downloads-years',
                        placement='top',                        
                    ),

                





                ]),                  
                dbc.ModalFooter([
                    dbc.Button("Close", id="modal-downloads-close", className="ml-auto"),
                    ]), 
            ],
            id="dbc-modal-download-land",
            centered=True,
            size="xl",            
            style={"max-width": "none", "width": INIT_DL_MODAL_W, 'max-height': "100vh"} 
        )
    return m
from dash import dash, html, dcc
import dash_bootstrap_components as dbc
from . global_constants import *
from . import layout_hovertip



def build():
    m = dbc.Modal(
            [                            
                dbc.ModalHeader(html.H1(id="line-graph-modal-title",style={"fontFamily":INIT_MODAL_HEADER_FONT_GENERAL, "fontSize": INIT_MODAL_HEADER_FONT_SIZE, "fontWeight": INIT_MODAL_HEADER_FONT_WEIGHT }),),                           
                
                dbc.ModalBody(html.Div([                    
                    dbc.Row([                    
                        
                        dbc.Col([                    
                            html.H5("Select countries"),                            
                            dcc.Dropdown(
                                options=[],
                                value=['United States of America', 'China', 'India', 'United Kingdom'],
                                id="line-graph-dropdown-countries",
                                multi=True,
                                placeholder='Select countries',
                                #style={'max-height': '100px'},
                            ),                             
                            
                            dbc.Button("Select all countries",  outline=True, color="secondary", id="linegraph-allcountries-button", style={"marginLeft": 0, 'marginTop':10, "marginBottom": 0, 'display': 'inline-block', 'opacity':INIT_BUTTON_OPACITY}, size=INIT_BUTTON_SIZE),
                            dbc.Button("Remove all countries",  outline=True, color="secondary", id="linegraph-nocountries-button", style={"marginLeft": 10, 'marginTop':10, "marginBottom": 0, 'display': 'inline-block', 'opacity':INIT_BUTTON_OPACITY}, size=INIT_BUTTON_SIZE),
                            
                             dbc.Tooltip(
                                "Only for the brave!",
                                target='linegraph-allcountries-button',
                                placement='bottom',                
                                ),
                                                        
                        ]),
                        dbc.Col([                        
                            html.H5("Change datasets"),
                            dcc.Dropdown(
                                options=[],
                                id="line-graph-dropdown-dataset",
                                multi=False,
                                placeholder='Select dataset or type to search'
                            ),
                        ]),                        
                    ]),                    
                    
                    # loader for component refreshes
                    dcc.Loading(
                        #id="my-loader-geobar",
                        type=INIT_LOADER_TYPE,
                        color=INIT_LOADER_CHART_COMPONENT_COLOR, #hex colour close match to nav bar ##515A5A
                        children=html.Span(id="my-loader-line-refresh"),
                        style={"zIndex":1, 'display': 'flex', 'vertical-align': 'center' , 'align-items': 'center', 'justify-content': 'center', 'paddingTop':100 },
                    ),
                    
                    dcc.Graph(id='line-graph',
                              animate=False,
                              style={"backgroundColor": "#1a2d46", 'color': '#ffffff', 'height': INIT_LINE_H},
                              config={'displayModeBar': False },),])),                           
                
                dbc.ModalFooter([
                    
                    html.Div([   
                        html.Span("Data source: "),
                        html.Span(id='line-graph-modal-footer'),
                        html.Div(dcc.Link(href='', target="_blank", id="line-graph-modal-footer-link")),
                    ], className="me-auto", style={'fontSize':INIT_MODAL_FOOTER_FONT_SIZE}), 
                    
                    html.Div([
                        dbc.Button("About", id='modal-line-guide-popover-target', color='info', className="me-2", size=INIT_BUTTON_SIZE),
                        dbc.Button("Instructions", id='modal-line-instructions-popover-target', color='warning', className="me-2", size=INIT_BUTTON_SIZE),
                        dbc.Button("Download", id='modal-line-download', color='success', className="me-2", size=INIT_BUTTON_SIZE),
                        dcc.Download(id='download_dataset_line'),
                        dbc.Button("Close", id="modal-line-close", className="me-2", size=INIT_BUTTON_SIZE)
                        
                    ]),
                    
                                        
                    dbc.Popover(
                        [
                            dbc.PopoverHeader("Instructions", style={'fontWeight':'bold'}),
                            dbc.PopoverBody(layout_hovertip.linegraph_instructions)
                        ],                        
                        target="modal-line-instructions-popover-target",
                        trigger="hover",
                        placement="top",
                        hide_arrow=False,                        
                    ),
                    
                    dbc.Popover(
                        [
                            dbc.PopoverHeader("About", style={'fontWeight':'bold'}),
                            dbc.PopoverBody(layout_hovertip.linegraph_about),
                        ],
                        target="modal-line-guide-popover-target",
                        trigger="hover",
                        placement="top",
                        hide_arrow=False,  
                    ),
                    
                    dbc.Popover(
                          [
                          dbc.PopoverHeader("Download", style={'fontWeight':'bold'}),
                          dbc.PopoverBody([          
                              html.Div('Raw data'),
                              dbc.Button(".xlsx", outline=True, color="secondary", className="me-1", id="btn-popover-line-download-xls", style={}, size=INIT_BUTTON_SIZE),
                              dbc.Button(".csv", outline=True, color="secondary", className="me-1", id="btn-popover-line-download-csv", style={}, size=INIT_BUTTON_SIZE),
                              dbc.Button(".json", outline=True, color="secondary", className="me-1", id="btn-popover-line-download-json", style={}, size=INIT_BUTTON_SIZE),
                              html.Div('Chart', style={'marginTop':5}),
                              dbc.Button(".pdf", outline=True, color="secondary", className="me-1", id="btn-popover-line-download-pdf", style={}, size=INIT_BUTTON_SIZE),
                              dbc.Button(".jpg", outline=True, color="secondary", className="me-1", id="btn-popover-line-download-jpg", style={}, size=INIT_BUTTON_SIZE),
                              dbc.Button(".png", outline=True, color="secondary", className="me-1", id="btn-popover-line-download-png", style={}, size=INIT_BUTTON_SIZE),
                              dbc.Button(".svg", outline=True, color="secondary", className="me-1", id="btn-popover-line-download-svg", style={}, size=INIT_BUTTON_SIZE),
                              #html.Div('Advanced', style={'marginTop':5,'display':'none'}),
                              #dbc.Button("Downloads Area", outline=True, color="secondary", className="me-1", id="btn-popover-line-download-land", style={'display':'none'}, size=INIT_BUTTON_SIZE),
                              ]),
                          ],
                          id="download-popover-line",                                        
                          target="modal-line-download",                          
                          trigger="legacy",
                          placement="top",
                          hide_arrow=False,
                          
                    ), 
                    
                ]), 
                
            ],
            id="dbc-modal-line",
            centered=True,
            size="xl",
            dialog_style={"max-width": "none", "width": INIT_LINE_MODAL_W} 
        )
    return m
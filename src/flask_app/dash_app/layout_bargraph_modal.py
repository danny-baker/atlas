from dash import dash, html, dcc
import dash_bootstrap_components as dbc
from . global_constants import *
from . import layout_hovertip


def build():
    
    m =  dbc.Modal(
                [                            
                    dbc.ModalHeader(html.Div(id="bar-graph-modal-title",style={"fontFamily":INIT_MODAL_HEADER_FONT_GENERAL, "fontSize": INIT_MODAL_HEADER_FONT_SIZE, "fontWeight": INIT_MODAL_HEADER_FONT_WEIGHT }), ),                           
                    
                    dbc.ModalBody(html.Div([                        
                        
                        # the dropdown components
                        dbc.Row([                        
                            dbc.Col([                        
                                html.H5("Highlight specific countries"),
                                dcc.Dropdown(
                                    options=[],
                                    id="bar-graph-dropdown-countrieselector",
                                    multi=True,
                                    placeholder='Select countries or type to search',
                                ),
                            ]),                            
                            dbc.Col([
                                html.H5("Change datasets"),
                                dcc.Dropdown(
                                    options=[],
                                    id="bar-graph-dropdown-dataset",
                                    multi=False,
                                    placeholder='Select dataset or type to search',
                                ),
                            ]),
                            dbc.Col([
                                html.H5("Change year"),
                                dcc.Dropdown(
                                    options=[],
                                    id="bar-graph-dropdown-year",
                                    multi=False,
                                    placeholder='Select year',
                                    clearable=False,
                                ),
                            ],width=2),
                        ], style={'marginBottom':10}), #end row
                            
                        # loader for component refreshes
                        dcc.Loading(
                            #id="my-loader-geobar",
                            type=INIT_LOADER_TYPE,
                            color=INIT_LOADER_CHART_COMPONENT_COLOR,              #INIT_LOADER_COLOR, #hex colour close match to nav bar ##515A5A
                            children=html.Span(id="my-loader-bar-refresh"),
                            style={"zIndex":1, 'display': 'flex', 'vertical-align': 'center' , 'align-items': 'center', 'justify-content': 'center', 'paddingTop':50 },
                        ),
                        
                        # the main bargraph
                        dcc.Graph(id='bar-graph',
                                  #animate=True,
                                  #animation_options={ 'frame': { 'redraw': True, }, 'transition': { 'duration': 500, 'ease': 'cubic-in-out', }, },
                                  style={"backgroundColor": "#1a2d46", 'color': '#ffffff', 'height': INIT_BAR_H},
                                  config={'displayModeBar': False },),
                    ])),  
          
                    
                    dbc.ModalFooter([                       
                        
                        
                        html.Div([                            
                            html.Div("Data source: "),
                            html.Div(id='bar-graph-modal-footer'), 
                            html.Div(dcc.Link(href='', target="_blank", id="bar-graph-modal-footer-link", )), 
                        ], className="me-auto", style={"fontSize": INIT_MODAL_FOOTER_FONT_SIZE, "background-color": "none" } ),
                       
                            
                        html.Div([       
                            dbc.Button("About", id='modal-bar-guide-popover-target', color='info', className="me-2", outline=False, size=INIT_BUTTON_SIZE),
                            dbc.Button("Instructions", id='modal-bar-instruction-popover-target', color='warning', className="me-2", outline=False, size=INIT_BUTTON_SIZE),
                            dbc.Button("Download", id='modal-bar-download', color='success', className="me-2", outline=False, size=INIT_BUTTON_SIZE),
                            dcc.Download(id='download_dataset_bar'),                           
                            dbc.Button("Close", id="modal-bar-close", className="me-2",size=INIT_BUTTON_SIZE),
                        ], style={"background-color": "none"}),                        
                        
                        
                        dbc.Popover(
                            [
                                dbc.PopoverHeader("Instructions", style={'fontWeight':'bold'}),
                                dbc.PopoverBody(layout_hovertip.bargraph_instructions),
                            ],                            
                            target="modal-bar-instruction-popover-target",
                            trigger="hover",
                            placement="top",
                            hide_arrow=False,                            
                        ),
                        
                        dbc.Popover(
                            [
                                dbc.PopoverHeader("About", style={'fontWeight':'bold'}),
                                dbc.PopoverBody(layout_hovertip.bargraph_about)                                    
                            ],                            
                            target="modal-bar-guide-popover-target",
                            trigger="hover",
                            placement="top",
                            hide_arrow=False,                            
                        ),
                        
                        dbc.Popover(
                          [
                          dbc.PopoverHeader("Download", style={'fontWeight':'bold'}),
                          dbc.PopoverBody([
                              html.Div('Raw data'),
                              dbc.Button(".xlsx", outline=True, color="secondary", className="me-1", id="btn-popover-bar-download-xls", style={}, size=INIT_BUTTON_SIZE),
                              dbc.Button(".csv", outline=True, color="secondary", className="me-1", id="btn-popover-bar-download-csv", style={}, size=INIT_BUTTON_SIZE),
                              dbc.Button(".json", outline=True, color="secondary", className="me-1", id="btn-popover-bar-download-json", style={}, size=INIT_BUTTON_SIZE),
                              html.Div('Chart', style={'marginTop':5}),
                              dbc.Button(".pdf", outline=True, color="secondary", className="me-1", id="btn-popover-bar-download-pdf", style={}, size=INIT_BUTTON_SIZE),
                              dbc.Button(".jpg", outline=True, color="secondary", className="me-1", id="btn-popover-bar-download-jpg", style={}, size=INIT_BUTTON_SIZE),
                              dbc.Button(".png", outline=True, color="secondary", className="me-1", id="btn-popover-bar-download-png", style={}, size=INIT_BUTTON_SIZE),
                              dbc.Button(".svg", outline=True, color="secondary", className="me-1", id="btn-popover-bar-download-svg", style={}, size=INIT_BUTTON_SIZE),
                              html.Div('Advanced', style={'marginTop':5,'display':'none'}),
                              dbc.Button("Downloads Area", outline=True, color="secondary", className="me-1", id="btn-popover-bar-download-land", style={'display':'none'}, size=INIT_BUTTON_SIZE),  
                              ]),
                          ],
                          id="download-popover-bar",                                        
                          target="modal-bar-download",
                          #style={'maxHeight': '300px', 'overflowY': 'auto'},
                          trigger="legacy",
                          placement="top",
                          hide_arrow=False,
                          
                          ), 
                        
                        
                        
                        
                    ], style={"background-color": "none"}),
                ],
                id="dbc-modal-bar",
                centered=True,
                size="xl",
                dialog_style={"max-width": "none", "width": INIT_BAR_MODAL_W, 'max-height': "100vh"} 
            )
    
    return m
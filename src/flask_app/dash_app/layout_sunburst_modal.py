from dash import dash, html, dcc
import dash_bootstrap_components as dbc
from . global_constants import *
from . import layout_hovertip


def build():
    m = dbc.Modal(
            [
                dbc.ModalHeader(html.H1(id="sunburst-graph-modal-title",style={"fontFamily":INIT_MODAL_HEADER_FONT_GENERAL, "fontSize": INIT_SUNBURST_MODAL_HEADER_FONT_SIZE, "fontWeight": INIT_MODAL_HEADER_FONT_WEIGHT }),),
                dbc.ModalBody(html.Div([
                    
                    dbc.Row([                        
                        dbc.Col([
                            #Dropdown quantitative data
                            html.H5("Quantitative data (pizza slices)"),                            
                            dcc.Dropdown(
                                options=[],
                                value='Population, total',
                                id="sunburst-dropdown-pizza",
                                multi=False,
                                placeholder='Select dataset',
                                clearable=False,
                            ),
                        ]),                                               
                        dbc.Col([
                            #Dropdown color axis
                            html.H5("Color data (pizza toppings)"),
                            dcc.Dropdown(
                                options=[],
                                value='Life expectancy at birth, data from IHME',
                                id="sunburst-dropdown-toppings",
                                multi=False,
                                placeholder='Select dataset',
                                clearable=False,
                            ),
                        ]),
                        dbc.Col([
                            #Dropdown years
                            #html.H5("Available years"),
                            dcc.Dropdown(
                                options=[],
                                id="sunburst-dropdown-years",
                                multi=False,
                                placeholder='Select...',
                                clearable=False,
                                style={'display':'none'}
                            ),
                        ], width=2),
                    ]),              
                    
                    dcc.Graph(id='sunburst-graph', animate=False, style={"backgroundColor": "#1a2d46", 'color': '#ffffff',  'height':INIT_SUNBURST_H}, config={'displayModeBar': False },),  
                    
                    # loader for component refreshes
                    dcc.Loading(                        
                        type=INIT_LOADER_TYPE,
                        color=INIT_LOADER_CHART_COMPONENT_COLOR, #hex colour close match to nav bar ##515A5A
                        children=html.Span(id="my-loader-sunburst-refresh"),
                        style={"zIndex":1, 'display': 'flex', 'vertical-align': 'center' , 'align-items': 'center', 'justify-content': 'center', 'paddingTop':0 },
                    ),    
                    
                ])),
                
                
                dbc.ModalFooter([
                    
                    html.Div([                    
                        html.Span("Data source: "),
                        html.Span(id='sunburst-graph-modal-footer'),    
                        html.Div(dcc.Link(href='', target="_blank", id="sunburst-graph-modal-footer-link")),
                    ], style={"fontSize": 12, 'display':'inline-block'} ),
                        
                    html.Div([
                        dbc.Button("About", id='modal-sunburst-guide-popover-target', color='info', className="mr-1", size=INIT_BUTTON_SIZE),
                        dbc.Button("Instructions", id='modal-sunburst-instructions-popover-target', color='warning', className="mr-1", size=INIT_BUTTON_SIZE),
                        dbc.Button("Show Example", id='modal-sunburst-examplebtn', color='light', className="mr-1", size=INIT_BUTTON_SIZE),
                        dbc.Button("Download", id='modal-sunburst-download', color='success', className="mr-1", size=INIT_BUTTON_SIZE),
                        dcc.Download(id='download_dataset_sunburst_csv'),
                        dbc.Button("Close", id="modal-sunburst-close", className="mr-1", size=INIT_BUTTON_SIZE), 
                        
                    ], className="ml-auto"),
                    
                    dbc.Popover(
                        [
                            dbc.PopoverHeader("About", style={'fontWeight':'bold'}),
                            dbc.PopoverBody(layout_hovertip.sunburst_about),
                        ],
                        #id="modal-sunburst-guide-popover",
                        #is_open=False,
                        target="modal-sunburst-guide-popover-target",
                        trigger="hover",
                        placement="top",
                        hide_arrow=False,
                        #style={"zIndex":1}
                    ),
                    
                    dbc.Popover(
                        [
                            dbc.PopoverHeader("Instructions", style={'fontWeight':'bold'}),
                            dbc.PopoverBody(layout_hovertip.sunburst_instructions),
                        ],
                        #id="modal-sunburst-instructions-popover",
                        #is_open=False,
                        target="modal-sunburst-instructions-popover-target",
                        trigger="hover",
                        placement="top",
                        hide_arrow=False,
                        #style={"zIndex":1}
                    ),
                    
                    dbc.Popover(
                          [
                          dbc.PopoverHeader("Download format:", style={'fontWeight':'bold'}),
                          dbc.PopoverBody([
                              html.Div('Raw data'),
                              dbc.Button(".xlsx", outline=True, color="secondary", className="mr-1", id="btn-popover-sunburst-download-xls", style={}, size=INIT_BUTTON_SIZE),
                              dbc.Button(".csv", outline=True, color="secondary", className="mr-1", id="btn-popover-sunburst-download-csv", style={}, size=INIT_BUTTON_SIZE),
                              dbc.Button(".json", outline=True, color="secondary", className="mr-1", id="btn-popover-sunburst-download-json", style={}, size=INIT_BUTTON_SIZE),
                              html.Div('Chart', style={'marginTop':5}),
                              dbc.Button(".pdf", outline=True, color="secondary", className="mr-1", id="btn-popover-sunburst-download-pdf", style={}, size=INIT_BUTTON_SIZE),
                              dbc.Button(".png", outline=True, color="secondary", className="mr-1", id="btn-popover-sunburst-download-png", style={}, size=INIT_BUTTON_SIZE),
                              dbc.Button(".svg", outline=True, color="secondary", className="mr-1", id="btn-popover-sunburst-download-svg", style={}, size=INIT_BUTTON_SIZE),
                              dbc.Button(".jpg", outline=True, color="secondary", className="mr-1", id="btn-popover-sunburst-download-jpg", style={}, size=INIT_BUTTON_SIZE),
                              html.Div('Advanced', style={'marginTop':5,'display':'none'}),
                              dbc.Button("Downloads Area", outline=True, color="secondary", className="mr-1", id="btn-popover-sunburst-download-land", style={'display':'none'}, size=INIT_BUTTON_SIZE), 
                              
                              ]),
                          ],
                          id="download-popover-sunburst",                                        
                          target="modal-sunburst-download",
                          #style={'maxHeight': '300px', 'overflowY': 'auto'},
                          trigger="legacy",
                          placement="top",
                          hide_arrow=False,
                          
                    ), 
                    
                    
                ]),
            ],
            id="dbc-modal-sunburst",
            centered=True,
            size="xl",
            style={"max-width": "none", "width": INIT_SUNBURST_MODAL_W}  #70%
        )
    return m
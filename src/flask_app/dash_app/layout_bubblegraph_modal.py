from dash import dash, html, dcc
import dash_bootstrap_components as dbc
from . global_constants import *
from . import layout_hovertip


def build():
    m = dbc.Modal(
            [                            
                dbc.ModalHeader(html.H1(id="bubble-graph-modal-title",style={"fontFamily":INIT_MODAL_HEADER_FONT_GENERAL, "fontSize": INIT_MODAL_HEADER_FONT_SIZE, "fontWeight": INIT_MODAL_HEADER_FONT_WEIGHT }),),                           
                
                dbc.ModalBody(html.Div([                    
                    dbc.Row([                        
                        dbc.Col([
                            #Dropdown x axis
                            html.H5("Vertical axis"),
                            dcc.Dropdown(
                                options=[],
                                value='GDP/capita (US$, inflation-adjusted)',
                                id="bubble-graph-dropdownX",
                                multi=False,
                                placeholder='Select dataset'
                            ),
                        ]),                                               
                        dbc.Col([
                            #Dropdown y axis
                            html.H5("Horizontal axis"),
                            dcc.Dropdown(
                                options=[],
                                value='Life expectancy at birth, data from IHME',
                                id="bubble-graph-dropdownY",
                                multi=False,
                                placeholder='Select dataset'
                            ),
                        ]),
                    ]),
                    
                    dbc.Row([                        
                        dbc.Col([                    
                            #Dropdown z axis
                            html.H5("Bubble size"),
                            dcc.Dropdown(
                                options=[],
                                value='Population, total',
                                id="bubble-graph-dropdownZ",
                                multi=False,
                                placeholder='Select dataset'
                            ),
                        ]),
                        dbc.Col([
                            
                            dbc.Row([
                                
                                dbc.Col([
                                    #Dropdown year axis
                                    html.H5("Available years"),
                                    dcc.Dropdown(
                                        options=[],
                                        id="bubble-graph-dropdownyear",
                                        multi=False,
                                        clearable=False,
                                    ),
                                ], width=6),
                                
                                dbc.Col([
                                
                                    html.H5("Logarithmic scale"),
                                    dcc.Checklist(
                                        options=[
                                            {'label': 'X axis', 'value': 'x'},
                                            {'label': 'Y axis', 'value': 'y'}, 
                                            {'label': 'Bubbles', 'value': 'z'}, 
                                        ],
                                        value=['x'],
                                        labelStyle={'display':'inline-block',"margin-left": "15px"},
                                        inputStyle={"margin-right": "10px"},
                                        style={'marginTop': 0},
                                        id='chklist-bubble-log',
                                    ),
                                ]),
                            ]),
                            
                        ]),
                    ], style={"marginTop": 10}),
                    
                    # loader for component refreshes
                    dcc.Loading(                        
                        type=INIT_LOADER_TYPE,
                        color=INIT_LOADER_CHART_COMPONENT_COLOR, #hex colour close match to nav bar ##515A5A
                        children=html.Span(id="my-loader-bubble-refresh"),
                        style={"zIndex":1, 'display': 'flex', 'vertical-align': 'center' , 'align-items': 'center', 'justify-content': 'center', 'paddingTop':50 },
                    ),
                    
                    dcc.Graph(id='bubble-graph',
                              #animate=False,
                              #animation_options={ 'frame': { 'redraw': True, }, 'transition': { 'duration': 500, 'ease': 'cubic-in-out', }, }, #working 95%, just doesn't resize the chart!! Need a way to mimic the double click javascript event to resize
                              #https://github.com/plotly/dash-core-components/blob/40a0d87479064e0f56286adac1c0493cf903d2b7/src/components/Graph.react.js#L71
                              #https://plotly.com/python/animations/
                              style={"backgroundColor": "#1a2d46", 'color': '#ffffff', 'height': INIT_BUBBLE_H },
                              config={'displayModeBar': False, 'responsive': True, 'autosizable': True },
                              ),
                ])),                           
                
                dbc.ModalFooter([
                    
                    #dbc.Row([                    
                    
                        #dbc.Col([    
                        html.Div([
                            #html.Span("Data source: "),
                            #html.Span(id='bubble-graph-modal-footer'),    
                            #html.Div(dcc.Link(href='', target="_blank", id="bubble-graph-modal-footer-link")),
                            html.Img(src='/static/img/bubblebobble1.png'), 
                            #dcc.Markdown(""" ![Image](bubblebobble1.png) """),
                            #'display': 'flex', 'vertical-align': 'top' , 'align-items': 'center', 'justify-content': 'center'
                            #dcc.Markdown(""" Built with ![Image](heart1.png) in Python using [Dash](https://plotly.com/dash/)."""),
                        ]),
                        #],width=3, style={'justify-content':'center', 'display':'flex','align-items': 'center'}),
                        
                        #dbc.Col([
                        html.Div([                            
                            dbc.Button("About", id='modal-bubble-guide-popover-target', color='info', className="mr-1", size=INIT_BUTTON_SIZE),
                            dbc.Button("Instructions", id='modal-bubble-instructions-popover-target', color='warning', className="mr-1", size=INIT_BUTTON_SIZE),
                            dbc.Button("Show Example", id='modal-bubble-examplebtn', color='light', className="mr-1", size=INIT_BUTTON_SIZE),
                            dbc.Button("Clear Chart", id='modal-bubble-resetbtn', color='light', className="mr-1", size=INIT_BUTTON_SIZE),
                            dbc.Button("Download", id='modal-bubble-download', color='success', className="mr-1", size=INIT_BUTTON_SIZE),
                            dcc.Download(id='download_dataset_bubble'),
                            dbc.Button("Close", id="modal-bubble-close", className="mr-1", size=INIT_BUTTON_SIZE),
                        ], className="ml-auto"),
                        #])
                    #]),
                    
                    dbc.Popover(
                        [
                            dbc.PopoverHeader("About", style={'fontWeight':'bold'}),
                            dbc.PopoverBody(layout_hovertip.bubblegraph_about),
                        ],
                        #id="modal-bubble-guide-popover",
                        #is_open=False,
                        target="modal-bubble-guide-popover-target",
                        trigger="hover",
                        placement="top",
                        hide_arrow=False,
                        #style={"zIndex":1}
                    ),
                    
                    dbc.Popover(
                        [
                            dbc.PopoverHeader("Instructions", style={'fontWeight':'bold'}),
                            dbc.PopoverBody(layout_hovertip.bubblegraph_instructions),
                        ],
                        #id="modal-bubble-instructions-popover",
                        #is_open=False,
                        target="modal-bubble-instructions-popover-target",
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
                              dbc.Button(".xlsx", outline=True, color="secondary", className="mr-1", id="btn-popover-bubble-download-xls", style={}, size=INIT_BUTTON_SIZE),
                              dbc.Button(".csv", outline=True, color="secondary", className="mr-1", id="btn-popover-bubble-download-csv", style={}, size=INIT_BUTTON_SIZE),
                              dbc.Button(".json", outline=True, color="secondary", className="mr-1", id="btn-popover-bubble-download-json", style={}, size=INIT_BUTTON_SIZE),
                              html.Div('Chart', style={'marginTop':5}),
                              dbc.Button(".pdf", outline=True, color="secondary", className="mr-1", id="btn-popover-bubble-download-pdf", style={}, size=INIT_BUTTON_SIZE),
                              dbc.Button(".png", outline=True, color="secondary", className="mr-1", id="btn-popover-bubble-download-png", style={}, size=INIT_BUTTON_SIZE),
                              dbc.Button(".svg", outline=True, color="secondary", className="mr-1", id="btn-popover-bubble-download-svg", style={}, size=INIT_BUTTON_SIZE),
                              dbc.Button(".jpg", outline=True, color="secondary", className="mr-1", id="btn-popover-bubble-download-jpg", style={}, size=INIT_BUTTON_SIZE),
                              html.Div('Advanced', style={'marginTop':5,'display':'none'}),
                              dbc.Button("Downloads Area", outline=True, color="secondary", className="mr-1", id="btn-popover-bubble-download-land", style={'display':'none'}, size=INIT_BUTTON_SIZE), 
                              ]),
                          ],
                          id="download-popover-bubble",                                        
                          target="modal-bubble-download",
                          #style={'maxHeight': '300px', 'overflowY': 'auto'},
                          trigger="legacy",
                          placement="top",
                          hide_arrow=False,
                          
                    ), 
                    
                ])
                
                
                
                
            ],
            id="dbc-modal-bubble",
            centered=True,
            size="xl",
            style={"max-width": "none", "width": INIT_BAR_BUBBLE_W} 
        )
    return m
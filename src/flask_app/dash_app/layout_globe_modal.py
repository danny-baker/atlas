from dash import dash, html, dcc
import dash_bootstrap_components as dbc
from . global_constants import *
from . import layout_hovertip


def build():
    m = dbc.Modal(
                [
                    dbc.ModalHeader(html.Div(html.H1(id="globe-modal-title",style={"fontFamily":INIT_MODAL_HEADER_FONT_GENERAL, "fontSize": INIT_MODAL_HEADER_FONT_SIZE, "fontWeight": INIT_MODAL_HEADER_FONT_WEIGHT })),),
                    
                    dbc.ModalBody([
                        html.Div(id='globe-body', style={'height': INIT_GLOBE_H, },),
                        
                        # loader for globe refreshes
                        dcc.Loading(
                            #id="my-loader-geobar",
                            type=INIT_LOADER_TYPE,
                            color=INIT_LOADER_CHART_COMPONENT_COLOR, #hex colour close match to nav bar ##515A5A
                            children=html.Span(id="my-loader-globe-refresh"),
                            style={"zIndex":1, 'display': 'flex', 'vertical-align': 'center' , 'align-items': 'center', 'justify-content': 'center', },
                        ),
                    
                        
                        ]), #'height': "50pc", 'width': '100%', # 'display': 'flex', 'align-items': 'center', 'justify-content': 'center'
                    
                    dbc.ModalFooter([                           
                            
                            #dbc.Row([
                                
                            #    dbc.Col([
                            
                                    html.Div([
                                        html.Span("Data source: "),
                                        html.Span(id='globe-modal-footer'), 
                                        html.Div(dcc.Link(href='', target="_blank", id="globe-modal-footer-link", style={'display':'inline-block'})),
                                    ], style={"fontSize": INIT_MODAL_FOOTER_FONT_SIZE, } ),
                                    
                             #   ]),
                             #   dbc.Col([
                            
                                    html.Div([
                                        dbc.Button("About", id='modal-globe-guide-popover-target', color='info', className="mr-1", outline=False, size=INIT_BUTTON_SIZE),
                                        dbc.Button("Instructions", id='modal-globe-instructions-popover-target', color='warning', className="mr-1", outline=False, size=INIT_BUTTON_SIZE), 
                                        dbc.Button("High Resolution", color="primary", id="modal-globe-ne50m", className="mr-1", size=INIT_BUTTON_SIZE ),
                                        dbc.Button("Jellybean Mode", color="success", id="modal-globe-jelly", className="mr-1", size=INIT_BUTTON_SIZE),
                                        dbc.Button("Close", id="modal-globe-close", className="mr-1", size=INIT_BUTTON_SIZE ),
                                    ], className="ml-auto", style={'display':'inline-block'}) ,
                              #  ]),
                            #]),
                                
                            
                            dbc.Popover(
                            [
                                dbc.PopoverHeader("Instructions", style={'fontWeight':'bold'}),
                                dbc.PopoverBody(layout_hovertip.globe_instructions),
                            ],
                            #id="modal-globe-instructions-popover",
                            #is_open=False,
                            target="modal-globe-instructions-popover-target",
                            trigger="hover",
                            placement="top",
                            hide_arrow=False,
                            style={"zIndex":1}
                            ),
                            
                            dbc.Popover(
                                [
                                    dbc.PopoverHeader("About", style={'fontWeight':'bold'}),
                                    dbc.PopoverBody(layout_hovertip.globe_about),                                    
                                ],
                                #id="modal-globe-guide-popover",
                                #is_open=False,
                                target="modal-globe-guide-popover-target",
                                trigger="hover",
                                placement="top",
                                hide_arrow=False,
                                style={"zIndex":1}
                            ),
                        
                        ],),
                    
                    #tool tip high resolution
                    dbc.Tooltip(
                                "Allow up to 30 seconds to load",
                                target='modal-globe-ne50m',
                                placement='top',
                                style={},
                        
                    ),
                ],
                id="dbc-modal-globe",
                centered=True,
                size="xl",
                style={"max-width": "none", "width": INIT_GLOBE_MODAL_W} #85%
            )
    return m
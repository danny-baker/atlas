from dash import dash, html, dcc
import dash_bootstrap_components as dbc
from . global_constants import *
from . import layout_hovertip

def build():
    m = dbc.Modal(
            [
                dbc.ModalHeader(html.Div([
                    html.H1(id="geobar-modal-title",style={"fontFamily":INIT_MODAL_HEADER_FONT_GENERAL, "fontSize": INIT_MODAL_HEADER_FONT_SIZE, "fontWeight": INIT_MODAL_HEADER_FONT_WEIGHT }),
                    
                ]),),
                
                dbc.ModalBody([                  
                    html.Div(id='geobar-test', style={'height': INIT_JIGSAW_H, 'display': 'flex', 'align-items': 'center', 'justify-content': 'center'},),  
                    
                     # loader for component refreshes
                    dcc.Loading(                        
                        type=INIT_LOADER_TYPE,
                        color=INIT_LOADER_CHART_COMPONENT_COLOR, #hex colour close match to nav bar ##515A5A
                        children=html.Span(id="my-loader-geobar-refresh"),
                        style={"zIndex":1, 'display': 'flex', 'vertical-align': 'center' , 'align-items': 'center', 'justify-content': 'center', },
                    ),
                
                ]), #, 'width': INIT_JIGSAW_W
                
                dbc.ModalFooter([
                            
                            html.Div([
                                html.Span("Data source: "),
                                html.Span(id='geobar-modal-footer'), 
                                html.Div(dcc.Link(href='', target="_blank", id="geobar-modal-footer-link",)),
                            ], style={"fontSize": INIT_MODAL_FOOTER_FONT_SIZE, 'display':'inline-block'} ),
                      
                            html.Div([
                                dbc.Button("About", id='modal-geobar-guide-popover-target', color='info', className="mr-1", outline=False, size=INIT_BUTTON_SIZE),
                                dbc.Button("Instructions", id='modal-geobar-instructions-popover-target', color='warning', className="mr-1", outline=False, size=INIT_BUTTON_SIZE),                            
                                dbc.Button("Jellybean Mode", color="success", id="modal-geobar-jelly", className="mr-1",size=INIT_BUTTON_SIZE),
                                dbc.Button("Close", id="modal-geobar-close", className="mr-1",size=INIT_BUTTON_SIZE),
                            ], className="ml-auto" ), 
                            
                
                            dbc.Popover(
                                [
                                dbc.PopoverHeader("Instructions", style={'fontWeight':'bold'}),
                                dbc.PopoverBody(layout_hovertip.jigsaw_instructions),
                                ],
                                #id="modal-geobar-instructions-popover",
                                #is_open=False,
                                target="modal-geobar-instructions-popover-target",
                                trigger="hover",
                                placement="top",
                                hide_arrow=False,
                                #style={"zIndex":1}
                            ),
                            
                            dbc.Popover(
                                [
                                dbc.PopoverHeader("About", style={'fontWeight':'bold'}),
                                dbc.PopoverBody(layout_hovertip.jigsaw_about),
                                #dbc.PopoverBody(dcc.Markdown(""" Built with ![Image](media/heart1.png) in Python using [Dash](https://plotly.com/dash/)."""), style={'display':'inline-block'}),
                                ],
                                #id="modal-geobar-guide-popover",
                                #is_open=False,
                                target="modal-geobar-guide-popover-target",
                                trigger="hover",
                                placement="top",
                                hide_arrow=False,
                                #style={"zIndex":1}
                            ),
                        ]),
                
                
            ],
            id="dbc-modal-geobar",
            centered=True,
            size="xl",
            style={"max-width": "none", "width": INIT_JIGSAW_MODAL_W} #85%
        )
    return m
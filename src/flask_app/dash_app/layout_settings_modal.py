from dash import dash, html, dcc
import dash_bootstrap_components as dbc
from . global_constants import *



settings_colour_scheme = html.Div([

    dcc.Markdown(""" 
    This controls how each region on the main map is coloured. 
    The main map is a choropleth, which is a type of map where regions are coloured based on the distibution of values in a data series. 
    You can change the colour scheme any time and there are 184 combinations!
    The default colour scheme for the site is `Inferno` in `Reverse`. To change the colour scheme select a combination and click the "APPLY SETTINGS" button. 
    Note that some charts and visualisations are also coloured based on the selected colour scheme.  
    """),
])


def build():
    
    #First build the modal body as it is complex (modal itself built at end function)
    settings_modal_body = html.Div([
        
        
        dbc.Row([
                
                #Border resolution    
                html.Div([
                #dbc.Container([    
        
                    #RESOLUTION
                    dcc.Markdown(""" #### Border Resolution """, style={"marginTop":'1vw'}),
                    dcc.Markdown(""" The number of individual points used to draw a line around a region."""),
             
                    dbc.Row([
                     
                        dbc.Card(
                        [
                            dbc.CardImg(src="/static/img/border1.PNG", top=True),
                            dbc.CardBody(dbc.Button("LOW DETAIL", size=INIT_BUTTON_SIZE, outline=True, active = True, color="success", id='settingsbtn-resolution-low'),),
                        ],
                        style={"width": INIT_SETTINGS_BORDER_CARD_WIDTH, 'align-items': 'center', 'justify-content': 'center',"marginBottom": 0, "marginTop": '1vw', "marginLeft": 0, "marginRight": '1vw' },
                        ),
                        
                        dbc.Card(
                        [
                            dbc.CardImg(src="/static/img/border2.PNG", top=True),
                            dbc.CardBody(dbc.Button("MEDIUM DETAIL", size=INIT_BUTTON_SIZE, outline=True, active = False, color="warning", id='settingsbtn-resolution-med'),),
                        ],
                        style={"width": INIT_SETTINGS_BORDER_CARD_WIDTH, 'align-items': 'center', 'justify-content': 'center', "marginBottom": 0, "marginTop": '1vw', "marginLeft": 0, "marginRight": '1vw'},
                        ),
                        
                        dbc.Card(
                        [
                            dbc.CardImg(src="/static/img/border3.PNG", top=True),
                            dbc.CardBody(dbc.Button("INSANE DETAIL", size=INIT_BUTTON_SIZE, outline=True, active = False, color="danger", id='settingsbtn-resolution-high')),
                        ],
                        style={"width": INIT_SETTINGS_BORDER_CARD_WIDTH, 'align-items': 'center', 'justify-content': 'center', "marginBottom": 0, "marginTop": '1vw', "marginLeft": 0, "marginRight": '1vw'},
                        ),
                        
                    ], style={"marginBottom": 0, "marginTop": 0, "marginLeft": 0, "marginRight": 0, }) #end row
                
                ]), #end div , style={'margin-left': '1vw'}
                
                #Map style
                #dbc.Container([
                html.Div([    
                    #MAP STYLE
                    dcc.Markdown(""" #### Map Style  """, style={"marginTop":'1vw'}),
                    dcc.Markdown(""" Choose from the free tile-based map styles courtesy of [MapBox](https://www.mapbox.com/) """),                
                    
                    #Map style
                    dbc.Row([   
               
                 
                        dbc.Card(
                        [
                            dbc.CardImg(src="/static/img/osmp.PNG", top=True, ), #style={'height':'58%'}
                            dbc.CardBody(dbc.Button("opn-street-map", size=INIT_BUTTON_SIZE, outline=True, active = False, color="secondary", id='settingsbtn-mapstyle-openstreetmap'),),
                        ],
                        style={"width": INIT_SETTINGS_MAP_CARD_WIDTH, 'align-items': 'center', 'justify-content': 'center', "marginBottom": 0, "marginTop": '1vw', "marginLeft": '1vw', "marginRight": 0},
                        ),
                        
                        dbc.Card(
                        [
                            dbc.CardImg(src="/static/img/cart.PNG", top=True, ), #style={'height':'58%'}
                            dbc.CardBody(dbc.Button("carto-positron", size=INIT_BUTTON_SIZE, outline=True, active = True, color="secondary",id='settingsbtn-mapstyle-carto-positron'),),
                        ],
                        style={"width": INIT_SETTINGS_MAP_CARD_WIDTH, 'align-items': 'center', 'justify-content': 'center', "marginBottom": 0, "marginTop": '1vw', "marginLeft": '1vw', "marginRight": 0},
                        ),
                        
                        dbc.Card(
                        [
                            dbc.CardImg(src="/static/img/dark.PNG", top=True, ), #style={'height':'58%'}
                            dbc.CardBody(dbc.Button("carto-dark",size=INIT_BUTTON_SIZE, outline=True, active = False, color="secondary",id='settingsbtn-mapstyle-darkmatter'),),
                        ],
                        style={"width": INIT_SETTINGS_MAP_CARD_WIDTH, 'align-items': 'center', 'justify-content': 'center', "marginBottom": 0, "marginTop": '1vw', "marginLeft": '1vw', "marginRight": 0},
                        ),
                        
                        dbc.Card(
                        [
                            dbc.CardImg(src="/static/img/terrain.PNG",  top=True), #style={'height':'58%'}
                            dbc.CardBody(dbc.Button("terrain", size=INIT_BUTTON_SIZE,outline=True, active = False, color="secondary",id='settingsbtn-mapstyle-stamen-terrain'),),
                        ],
                        style={"width": INIT_SETTINGS_MAP_CARD_WIDTH, 'align-items': 'center', 'justify-content': 'center', "marginBottom": 0, "marginTop": '1vw', "marginLeft": '1vw', "marginRight": 0},
                        ),
                        
                        dbc.Card(
                        [
                            dbc.CardImg(src="/static/img/charlie3.png", top=True,), #style={'height':'57%'}
                            dbc.CardBody(dbc.Button("charlie",size=INIT_BUTTON_SIZE, outline=True, active = False, color="secondary",id='settingsbtn-mapstyle-stamen-toner'),),
                        ],
                        style={"width": INIT_SETTINGS_MAP_CARD_WIDTH, 'align-items': 'center', 'justify-content': 'center', "marginBottom": 0, "marginTop": '1vw', "marginLeft": '1vw', "marginRight": 0},
                        ),
                        
                        dbc.Card(
                        [
                            dbc.CardImg(src="/static/img/watercolour.PNG", top=True), # style={'height':'58%'}
                            dbc.CardBody(dbc.Button("watercolor", size=INIT_BUTTON_SIZE, outline=True, active = False, color="secondary",id='settingsbtn-mapstyle-stamen-watercolor'), ),
                        ],
                        style={"width": INIT_SETTINGS_MAP_CARD_WIDTH, 'align-items': 'center', 'justify-content': 'center', "marginBottom": 0, "marginTop": '1vw', "marginLeft": '1vw', "marginRight": 0},
                        ),
                    ]), #end row
               
                    
                ] ), #end div , style={'margin-left': '1vw'}
          ], style={'margin-left': '1vw'}),    # end main row
        
        
        #tool tips
        dbc.Tooltip(
                "High resolution borders will take much longer to load each dataset (~30 seconds).",
                target='settingsbtn-resolution-high',
                placement='bottom',
                style={},
        ),
        
        dbc.Tooltip(
                "Default resolution. Fastest performance.",
                target='settingsbtn-resolution-low',
                placement='bottom',
                style={},
        ),
                
        html.Div(html.Br()),    
        
        #COLOURSCALE BUTTON GROUP
        
        html.Div([    
        
                #COLOUR SCHEME
                dcc.Markdown(""" #### Colour Scheme  """),
                settings_colour_scheme,
                                
                #Create colorscale buttons recursively by calling a special function
                html.Div(children=[create_dash_layout_settings_modal_colorscale_button(i) for i in range(0,93)]),
                
                #Create reverse toggle button for reversing colorscale
                html.Div([                   
                        html.H6("Reverse Color Scale",style={"marginLeft": 0, "marginBottom": 0, "marginTop":10, 'marginRight':10, 'display':'inline-block'}),
                        dbc.ButtonGroup([  
                            dbc.Button("OFF", color="danger", outline=True, id='settingsbtn-normal-colorscale',style={"marginLeft": 1, "marginBottom": 0, "marginTop":5}, size=INIT_BUTTON_SIZE),
                            dbc.Button("ON", color="success", outline=True, id='settingsbtn-reverse-colorscale',style={"marginLeft": 0, "marginBottom": 0, "marginTop":5}, size=INIT_BUTTON_SIZE),
                            
                            ],style={'display':'inline-block'})                           
                        ])
               
        ], style={'margin-left': '1vw'}),    # end main row) 
    ])
    
    
    #Build the actual modal
    m = dbc.Modal(
        [
            dbc.ModalHeader(html.Div("Settings", style={"fontFamily":INIT_MODAL_HEADER_FONT_GENERAL, "fontSize": INIT_MODAL_HEADER_FONT_SIZE, "fontWeight": INIT_MODAL_HEADER_FONT_WEIGHT })),
            dbc.ModalBody(settings_modal_body),
            dbc.ModalFooter([ 
                dbc.Button("Close", id="modal-settings-close", className="",size=INIT_BUTTON_SIZE),
                dbc.Button("Apply settings", id="modal-settings-apply", className="", color="dark", size=INIT_BUTTON_SIZE)                               
                ]
            ),  
            
        ],
        id="dbc-modal-settings",
        centered=True,
        size="xl",
        style={"max-width": "none", "width": INIT_SETTINGS_MODAL_W}
    )
    return m


#construct colorscale button
def create_dash_layout_settings_modal_colorscale_button(i):
    
    #hide the first 'auto' option as this messes with the ability to get the colorwheel
    if i == 0:
        return dbc.Button(children=geomap_colorscale[i], color="light", className="mr-1", id=geomap_colorscale[i], style={'display': 'none'})
    
    else:
        return dbc.Button(children=geomap_colorscale[i], color="light", className="mr-1", id=geomap_colorscale[i], size=INIT_BUTTON_SIZE, style={'marginBottom':3})



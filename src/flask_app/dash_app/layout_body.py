from dash import dash, html, dcc
from . global_constants import *
import logging
import plotly.express as px
import plotly.graph_objs as go
from . global_constants import *

#Obtain the root logger
logger = logging.getLogger(LOGGER)

def build():
    
    body = html.Div(
        children=[
            
            # loader for geobar
            dcc.Loading(
                #id="my-loader-geobar",
                type=INIT_LOADER_TYPE,
                color=INIT_LOADER_CHART_COLOR, #hex colour close match to nav bar ##515A5A
                children=html.Span(id="my-loader-geobar"),
                style={"zIndex":1, 'display': 'flex', 'vertical-align': 'center' , 'align-items': 'center', 'justify-content': 'center', "marginTop": '50vh'},
                ),
            
            # loader for bubble graph
            dcc.Loading(                
                type=INIT_LOADER_TYPE,
                color=INIT_LOADER_CHART_COLOR, #hex colour close match to nav bar
                children=html.Span(id="my-loader-bubble"),
                style={"zIndex":1, 'display': 'flex', 'vertical-align': 'center' , 'align-items': 'center', 'justify-content': 'center', "marginTop": '50vh'},
                ),
            
            # loader for line graph
            dcc.Loading(                
                type=INIT_LOADER_TYPE,
                color=INIT_LOADER_CHART_COLOR, #hex colour close match to nav bar
                children=html.Span(id="my-loader-line"),
                style={"zIndex":1, 'display': 'flex', 'vertical-align': 'center' , 'align-items': 'center', 'justify-content': 'center', "marginTop": '50vh'},
            ),
            
            # loader for sunburst
            dcc.Loading(                
                type=INIT_LOADER_TYPE,
                color=INIT_LOADER_CHART_COLOR, #hex colour close match to nav bar
                children=html.Span(id="my-loader-sunburst"),
                style={"zIndex":1, 'display': 'flex', 'vertical-align': 'center' , 'align-items': 'center', 'justify-content': 'center', "marginTop": '50vh'},
                ),
            
            # loader for the globe          
            dcc.Loading(                
                type=INIT_LOADER_TYPE,
                color=INIT_LOADER_CHART_COLOR, #hex colour close match to nav bar
                children=html.Span(id="my-loader-globe"),
                style={"zIndex":1, 'display': 'flex', 'vertical-align': 'center' , 'align-items': 'center', 'justify-content': 'center', "marginTop": '50vh'},
                ),
            
            # loader for bar graph
            dcc.Loading(                
                type=INIT_LOADER_TYPE,
                color=INIT_LOADER_CHART_COLOR, #hex colour close match to nav bar
                children=html.Span(id="my-loader-bar"),
                style={"zIndex":1, 'display': 'flex', 'vertical-align': 'center' , 'align-items': 'center', 'justify-content': 'center', "marginTop": '50vh'},
            ),

            # loader for bar graph
            dcc.Loading(                
                type=INIT_LOADER_TYPE,
                color=INIT_LOADER_CHART_COLOR, #hex colour close match to nav bar
                children=html.Span(id="my-loader-xp"),
                style={"zIndex":1, 'display': 'flex', 'vertical-align': 'center' , 'align-items': 'center', 'justify-content': 'center', "marginTop": '50vh'},
            ),

            
            # THE MAIN GRAPH CENTERPIECE
            dcc.Graph(
                style={"height": INIT_MAP_H, "width": INIT_MAP_W, 'z-index':'2' }, 
                id="geomap_figure",
                figure = create_map_geomap_empty(),
                config={'displayModeBar': False, 'scrollZoom': True },              
            )
        ],)
    return body


def create_map_geomap_empty():
    #No method overloading in python, so have an empty map load for initial.
    logger.info("Creating geomap empty...")
    
    fig = go.Figure(
        go.Choroplethmapbox(        
        )
    )
    
    #zoom 1.6637151294876888 and centre {'lon': 27.607108241243623, 'lat': 3.4455217746834705}
    fig.update_layout(
        mapbox_style=mapbox_style[1], #default
        mapbox_zoom=INIT_ZOOM,
        mapbox_center={"lat": INIT_LATITUDE, "lon": INIT_LONGITUDE},   
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
    )
    return fig

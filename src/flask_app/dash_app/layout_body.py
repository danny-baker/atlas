from dash import dash, html, dcc
from . global_constants import *
import logging
import plotly.express as px
import plotly.graph_objs as go
from . global_constants import *
from . import charts

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
                figure = charts.create_map_geomap_empty(),
                config={'displayModeBar': False, 'scrollZoom': True },              
            )
        ],)
    return body


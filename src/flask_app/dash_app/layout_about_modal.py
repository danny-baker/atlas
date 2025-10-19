from dash import dash, html, dcc
import dash_bootstrap_components as dbc
from . global_constants import *



about_modal_body = html.Div([  
    
    dcc.Markdown(""" 
    
    **Inspired by Microsoft's Encarta from the 1990's, The Atlas mission is simple: "make important data super-accessible to everyone."**
       
    With over 15 million data points spanning 100 categories, find a dataset that interests you and explore it using a suite of interactive maps and charts. 
    All data is fully sourced and available for download. It's designed to be easy to use and fun to learn. Hit the USER GUIDE button in the bottom left of the main screen for a 2 minute fly over of the site features.
        
    Read the full background and write-up published on Towards Datascience (medium.com) [here](https://towardsdatascience.com/ive-built-a-public-world-atlas-with-2-500-datasets-to-explore-8b9ae799e345). The entire project is open-source on Github [here](https://github.com/danny-baker/atlas).
    """),
                    
    html.Div(html.Br()),
    html.Span(html.Img(src='/static/img/scrn2_sm.png', style={'width':'22%', 'marginRight':'1vw'})),        
    html.Span(html.Img(src='/static/img/scrn6_sm.png', style={'width':'22%', 'marginRight':'1vw'})),
    html.Span(html.Img(src='/static/img/scrn3_sm.png', style={'width':'22%', 'marginRight':'1vw'})),        
    html.Span(html.Img(src='/static/img/scrn10_sm.png', style={'width':'22%', 'marginRight':'1vw'})),        
    html.Div(html.Br()),
    
            
    dcc.Markdown("""  
    
    Once you discover something interesting, you can share the map or chart directly with anyone via the full URL path in the browser! 
    
    Examples: 
    * [A map showing access to electricity across the world in 2022](https://worldatlas.org/Access-to-electricity-(percent-of-population)/2022/map)
    * [How access to clean water and sanitation has changed over the last 30 years](https://worldatlas.org/Access-to-basic-sanitation--overall-access-(percent-of-population)/x/line)    
    * [All countries ranked by their access to the internet in 2021](https://worldatlas.org/Individuals-using-the-Internet-(percent-of-population)/2021/bar)
    * [A 3d globe showing which side of the road each country drives on](https://worldatlas.org/Which-side-of-the-road-do-they-drive-/2020/globe)

    Please note this site is 100% self-funded and experimental, so there are still a few bugs. And it's best experienced on a desktop or laptop in Chrome or Firefox. 
    I'd love your feedback and ideas for the site via the [2 minute anonymous survey](https://forms.gle/CMA8CZCggfZZ4kEZA). You can also reach me direct via dan@worldatlas.org
    
    """),
        
])


def build():    
       
    m = dbc.Modal(
            [
                dbc.ModalHeader(html.Div("This site is a front-end to thousands of datasets.", style={"fontFamily":INIT_MODAL_HEADER_FONT_GENERAL, "fontSize": INIT_MODAL_HEADER_FONT_SIZE, "fontWeight": INIT_MODAL_HEADER_FONT_WEIGHT })),
                dbc.ModalBody(about_modal_body),
                dbc.ModalFooter([
                    dcc.Markdown(""" Built with ![Image](/static/img/heart1.png) in Python using [Dash](https://plotly.com/dash/)."""),
                    dbc.Button("Close", id="modal-about-close", className="ml-auto",size=INIT_BUTTON_SIZE)
                    ]
                ),
                #html.Div([html.Audio(id='audio', src='/static/img/encarta_intro.mp3', autoPlay=True, loop=False )]) #,controls=True
                
                
            ],
            id="dbc-modal-about",
            centered=True,
            size="xl",
            dialog_style={"max-width": "none", "width": INIT_ABOUT_MODAL_W}  #70%
        )
    return m
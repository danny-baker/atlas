import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc


settings_colour_scheme = html.Div([

    dcc.Markdown(""" 
    This controls how each region on the main map is coloured. 
    The main map is a choropleth, which is a type of map where regions are coloured based on the distibution of values in a data series. 
    You can change the colour scheme any time and there are 184 combinations!
    The default colour scheme for the site is `Inferno` in `Reverse`. To change the colour scheme select a combination and click the "APPLY SETTINGS" button. 
    Note that some charts and visualisations are also coloured based on the selected colour scheme.  
    """),
])


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
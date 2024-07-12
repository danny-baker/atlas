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
    
    #### I've built a World Atlas as a website, with over 2,500 datasets for you to explore. 
       
    This site is a front-end to thousands of datasets. It allows you to *see* the data as it should be seen: through colours and shapes.
    With over 12 million data points spanning 100 categories, find a dataset that interests you and explore it using a suite of interactive maps and charts. 
    All data is fully sourced and available for download. It's designed to be easy to use and fun to learn.
    Features include a world map and 3d globe, alongside realtime analytical tools such as bar charts, line charts, and scatter plots.
    Inspired by Microsoft's Encarta from the 1990's, The Atlas mission is simple: "make important data super-accessible to everyone."
    Read the full write-up [here](https://towardsdatascience.com/ive-built-a-public-world-atlas-with-2-500-datasets-to-explore-8b9ae799e345).
    """),

    html.Div([
        html.Div('Learn how to use the site with a 2 minute video flyover in the ',style={'font-weight': 'bold'} ),
        html.Button("user guide", id="button-userguide-about", style={'border':'none', 'font-size': '15px', 'font-weight': 'bold', 'color': 'lightseagreen', 'text-align': 'center', 'background-color': 'transparent', 'padding': '0px 3px', 'text-decoration':'none', } ),
    ],style={'display':'flex', 'vertical-align': 'middle', 'background-color': 'transparent' }),
                    
    html.Div(html.Br()),
    html.Span(html.Img(src='/static/img/scrn2_sm.png', style={'width':'22%', 'marginRight':'1vw'})),        
    html.Span(html.Img(src='/static/img/scrn6_sm.png', style={'width':'22%', 'marginRight':'1vw'})),
    html.Span(html.Img(src='/static/img/scrn3_sm.png', style={'width':'22%', 'marginRight':'1vw'})),        
    html.Span(html.Img(src='/static/img/scrn10_sm.png', style={'width':'22%', 'marginRight':'1vw'})),        
    html.Div(html.Br()),
    
            
    dcc.Markdown("""  
    
    Once you discover something interesting, you can share the map or chart directly with anyone via the full URL path in the browser! 
    
    Examples: 
    * [A map showing access to electricity across the world in 2018](https://worldatlas.org/Access-to-electricity-(percent-of-population)/2018/bar)
    * [How access to clean water and sanitation has changed over the last 30 years](https://worldatlas.org/At-least-basic-sanitation--overall-access-(percent)/x/line)    
    * [All countries ranked by their access to the internet in 2017](https://worldatlas.org/Technology---Percentage-of-individuals-using-the-internet-(percent)/2017/bar)
    * [A 3d globe showing which side of the road each country drives on](https://worldatlas.org/Which-side-of-the-road-do-they-drive/2020/globe)

    Please note this site is 100% self-funded and experimental, so there are still a few bugs. 
    The site is best experienced on a desktop or laptop in Chrome or Firefox. I'm working to make it more friendly to small screen sizes (phones).
    I'd love to hear what you think of the site, what features you would like to see, and how it could be improved.
    
    #### Please send feedback to dan@worldatlas.org

    """),
        
])
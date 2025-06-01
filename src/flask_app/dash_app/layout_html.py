# This is the base template used by the dash page
index_string = '''

    <!DOCTYPE html>
    <html>
        <head>
            {%metas%}
             
            <!-- Primary Meta Tags -->
            <title>{%title%}</title> 
            <title>WORLD ATLAS 2.0</title>
            <meta name="title" content="WORLD ATLAS 2.0 - Explore 2,500 datasets">
            <meta name="description" content="With over 15 million data points spanning 100 categories, find a dataset that interests you and analyse it using a suite of interactive charts. All data is fully sourced and available for download. It's designed to be easy to use and fun to learn. ">

            <!-- Open Graph / Facebook -->
            <meta property="og:type" content="website">
            <meta property="og:url" content="https://worldatlas.org/">
            <meta property="og:title" content="WORLD ATLAS 2.0 - Explore 2,500 datasets">
            <meta property="og:description" content="This is OG description meta content.">
            <meta property="og:image" content="https://worldatlas.org/static/img/screenshot_meta.png">

            <!-- Twitter -->
            <meta property="twitter:card" content="summary_large_image">
            <meta property="twitter:url" content="https://worldatlas.org/">
            <meta property="twitter:title" content="WORLD ATLAS 2.0 - Explore 2,500 datasets">
            <meta property="twitter:description" content="This is twitter description meta content. ">
            <meta property="twitter:image" content="https://worldatlas.org/static/img/screenshot_meta.png">
             
            {%favicon%}
            {%css%}     

            <!-- Global site tag (gtag.js) - Google Analytics -->
            <script async src="https://www.googletagmanager.com/gtag/js?id=SECRET_GA4_TAG"></script>
            <script>
            window.dataLayer = window.dataLayer || [];
            function gtag(){dataLayer.push(arguments);}
            gtag('js', new Date());
            gtag('config', 'SECRET_GA4_TAG');
            </script>            
            
        </head>

        <style>
            * {
            box-sizing: border-box;
            }

            /* Column css bullshit */
            .column {
            float: left;            
            padding: 10px;            
            }

            .left {
            width: 85%
            }

            .right {
            width: 15%
            }


            body {
            /*overflow-y: hidden; /* Hide vertical scrollbar */
            overflow-x: hidden; /* Hide horizontal scrollbar */
            }

            
        </style>
        
        <body>        
            {%app_entry%}
            <footer>
                {%config%}
                {%scripts%}
                {%renderer%}           
            </footer>  

            <div class="row">

                
                <div class="column left" style="background-color:transparent;padding-left:25px;">
                     <!--<p>This project is now open-source on Github! Check it out <a href="https://github.com/danny-baker/atlas">here</a>.</p>-->
                     WELCOME_MSG_TOKEN_HTML

                    
                </div>
                
                    
                <div class="column right" style="text-align:right;padding-right:25px;background-color:transparent;">
                    <a style="font-size: 2vmin"  href="https://www.buymeacoffee.com/danbaker" target="_blank">Buy me a coffee :) </a>
                </div>
                

            </div>
            
            </body>
    </html>
    '''
    

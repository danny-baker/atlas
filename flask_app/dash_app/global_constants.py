# Global configuration constants for main app

#DECLARE GLOBAL APPLICATION DATA

mapbox_style = ["open-street-map", "carto-positron", "carto-darkmatter", "stamen-terrain", "stamen-toner", "stamen-watercolor"]

geomap_colorscale = ["auto", 'aggrnyl', 'agsunset', 'algae', 'amp', 'armyrose', 'balance',
             'blackbody', 'bluered', 'blues', 'blugrn', 'bluyl', 'brbg',
             'brwnyl', 'bugn', 'bupu', 'burg', 'burgyl', 'cividis', 'curl',
             'darkmint', 'deep', 'delta', 'dense', 'earth', 'edge', 'electric',
             'emrld', 'fall', 'geyser', 'gnbu', 'gray', 'greens', 'greys',
             'haline', 'hot', 'hsv', 'ice', 'icefire', 'inferno', 'jet',
             'magenta', 'magma', 'matter', 'mint', 'mrybm', 'mygbm', 'oranges',
             'orrd', 'oryel', 'peach', 'phase', 'picnic', 'pinkyl', 'piyg',
             'plasma', 'plotly3', 'portland', 'prgn', 'pubu', 'pubugn', 'puor',
             'purd', 'purp', 'purples', 'purpor', 'rainbow', 'rdbu', 'rdgy',
             'rdpu', 'rdylbu', 'rdylgn', 'redor', 'reds', 'solar', 'spectral',
             'speed', 'sunset', 'sunsetdark', 'teal', 'tealgrn', 'tealrose',
             'tempo', 'temps', 'thermal', 'tropic', 'turbid', 'twilight',
             'viridis', 'ylgn', 'ylgnbu', 'ylorbr', 'ylorrd']

#build discrete colourscale (16 available)
discrete_colorscale = [
    ((0.0, '#792069'), (1.0, '#792069')), #purple
    ((0.0, '#FFBB33'), (1.0, '#FFBB33')), #orangy
    ((0.0, '#00cc96'), (1.0, '#00cc96')), #green (0,204,150)       
    ((0.0, '#EF553B'), (1.0, '#EF553B')), #red (239,85,59)    
    ((0.0, '#636efa'), (1.0, '#636efa')), #blue (99,110,25)         
    ((0.0, '#7F8C8D'), (1.0, '#7F8C8D')), #grey
    ((0.0, '#0dc9b6'), (1.0, '#0dc9b6')), #cyan
    ((0.0, '#eac1c1'), (1.0, '#eac1c1')), #yuk pink
    ((0.0, '#fff8b7'), (1.0, '#fff8b7')), #cream
    ((0.0, '#264f7d'), (1.0, '#264f7d')), #navy blue
    ((0.0, '#95b619'), (1.0, '#95b619')), #yellowy
    ((0.0, '#99b8cc'), (1.0, '#99b8cc')), #bluey
    ((0.0, '#853d55'), (1.0, '#853d55')), #beige
    ((0.0, '#542709'), (1.0, '#542709')), #poo brown
    ((0.0, '#4db0bd'), (1.0, '#4db0bd')), #turcoise
    ((0.0, '#13ad20'), (1.0, '#13ad20')), #green as fuck
]

#Initialise default settings
INIT_BORDER_RES = 0
INIT_COLOR_PALETTE = 39 #fall 28 
INIT_COLOR_PALETTE_REVERSE = True
INIT_MAP_STYLE = 1
INIT_TITLE_TEXT = "WORLD  ATLAS  2.0"
INIT_TITLE_H = "6vmin" # "7vh"
INIT_TITLE_DIV_H = "7vmin"
INIT_TITLE_PAD_TOP = "1vmin"
INIT_TITLE_COL = "white"                                 # title colour
INIT_TITLE_BG_COL = "grey"                               # title background
INIT_TITLE_OPACITY = 0.8                                 # title opacity
INIT_BUTTON_OPACITY = 0.9                                # button opacity
INIT_BTN_OUTLINE = False
INIT_year_SLIDER_FONTSIZE = "1.5vmin"
INIT_year_TITLE_FONTSIZE = "2vmin" #2vmin
INIT_year_SLIDER_FONTCOLOR = 'grey'
INIT_SELECTION_H = "2.3vmin"  #was 2.3
INIT_NAVBAR_H = "7vmin"                                # NAVBAR HEIGHT
INIT_NAVBAR_W = "100vw" 
INIT_NAVBAR_FONT_H = "1.6vmin"                         #was 1.35vmin making larger for chrome tradeoff
INIT_NAVBAR_SEARCH_WIDTH ='30vw'
INIT_NAVBAR_SEARCH_FONT = "1.5vmin" 
INIT_RANDOM_BTN_TEXT = "PRESS ME"
INIT_RANDOM_BTN_FONT = "1.35vmin"
INIT_MAP_H = "88vh"                                   # MAP HEIGHT was 92.75. was 88 for firefox. Dropping for chrome windows. Was 87.
INIT_MAP_W = "100vw"
INIT_BAR_H = "55vmin"
INIT_LINE_H = "50vmin"
INIT_BUBBLE_H = "50vmin"
INIT_SUNBURST_H = "60vh"
INIT_JIGSAW_H = "65vh"
#INIT_JIGSAW_W = "50vw"
INIT_GLOBE_H = "72vh"
INIT_EXPERIMENT_H = '90vh'
#INIT_BUTTON_FONT_H = "1.1vmin"
INIT_BUTTON_SIZE = 'sm'
INIT_DROPDOWNITEM_LPAD = 0
INIT_DROPDOWNITEM_RPAD = "0.65vw"
INIT_SETTINGS_BORDER_CARD_WIDTH = "19vh" #settings modal was 17vh
INIT_SETTINGS_MAP_CARD_WIDTH = "18vh" #settings modal
INIT_SETTINGS_DL_CARD_WIDTH = '31.5%'
INIT_UGUIDE_MODAL_W = "70%"
INIT_SETTINGS_MODAL_W = "70%"
INIT_GLOBE_MODAL_W = "70%"
INIT_BAR_MODAL_W = "90%"
INIT_DL_MODAL_W = "70%"
INIT_LINE_MODAL_W = "70%"
INIT_BAR_BUBBLE_W = "70%"
INIT_SUNBURST_MODAL_W = "70%"
INIT_JIGSAW_MODAL_W = "70%"
INIT_ABOUT_MODAL_W = "60%"
INIT_AREA51_NAVBAR_W = '35vw'
INIT_NAVFOOTER_W = '97vw' #100% causes scroll bar to appear 97.5vw good for firefox. But dropping to test.
INIT_NAVFOOTER_OFFSET = "5.5vmin" #This is optimised for wide aspect. it pushes nav footer too high on narrow portrait screens. Try to detect?
INIT_NAVFOOTER_BTN_FONT = "1.35vmin" 
INIT_NAVFOOTER_COMPONENT_MINWIDTH = 400
INIT_SOURCE_POPOVER_FONT = "1.5vmin" #does not appear to be working. Could be a bug with the popover style
INIT_SOURCE_FONT = "1.5vmin"
INIT_LATITUDE = 24.32570626067931 
INIT_LONGITUDE = 6.365789817509949
INIT_ZOOM = 1.6637151294876884
#Fonts
#Title font "allstar, ca, bal, bank, capt1, capt2, commodore, const, game, lady, miss, prometheus, mario, aad, amnestia, betel, bord, emy, reduza, maizen
#like: miss, madio, amnestia, betel
#refined/timeless: const
#futuristic scifi: betel, lady
#old school fantasy: amnestia
#8 bit retro stylised: miss, mario, commodore
INIT_FONT_MASTER = ""
INIT_TITLE_FONT = INIT_FONT_MASTER 
INIT_MODAL_HEADER_FONT_GENERAL = INIT_FONT_MASTER #the default font for heading
INIT_MODAL_HEADER_FONT_UGUIDE = INIT_FONT_MASTER
INIT_MODAL_HEADER_FONT_SETTINGS = INIT_FONT_MASTER
INIT_MODAL_HEADER_FONT_ABOUT = INIT_FONT_MASTER
INIT_MODAL_HEADER_FONT_SIZE = "4vmin"
INIT_MODAL_HEADER_FONT_WEIGHT = "bold"
INIT_MODAL_FOOTER_FONT_SIZE = 12
INIT_SUNBURST_MODAL_HEADER_FONT_SIZE = '3vmin'
INIT_LOADER_DATASET_COLOR = "#3E3F3A"
INIT_LOADER_CHART_COLOR = "#3E3F3A"
INIT_LOADER_CHART_COMPONENT_COLOR = "#3E3F3A"
INIT_LOADER_TYPE = 'dot'
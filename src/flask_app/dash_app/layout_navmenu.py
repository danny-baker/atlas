from dash import dash, html, dcc
import dash_bootstrap_components as dbc
from . global_constants import *
import logging
import pandas as pd
from . import data


#Obtain the root logger
logger = logging.getLogger(LOGGER)


def build(dobj):
    
    #construct the navbar by calling a function that recursively builds out components based on dataset_lkup
    navbar = html.Div(        
        
        children=create_dash_layout_navbar_menu(dobj),              
        className="ml-auto", #Format the row. This ensurs spill over buttons are also centre aligned        
               
        style={"height": INIT_NAVBAR_H,
               "width": INIT_NAVBAR_W,
               #"zIndex":2,
               "backgroundColor": '#3E3F3A',
               'display': 'flex',
               'vertical-align': 'top',
               'align-items': 'center',
               'justify-content': 'center',               
               #"marginBottom": 0,
               #"marginTop": 0,
               #"marginLeft": '1vw',
               #"marginRight": '1vw',               
               #"margin-left": "auto",
               #"margin-right": "auto",               
               #'backgroundColor':'yellow',               
               #"position": "absolute",
               #"z-index": "2",
               #"top": INIT_NAVBAR_POSITION, 
               #"left": "5vw",
               
               
               }, 
        
    )    

    return navbar


def create_dash_layout_navbar_items(nav_cat, dobj):
    
    #build dropdown menu items for all instances of the nav_cat from master config
    #This is pretty inefficient but the logic is super hard, so I haven't wanted to fuck with it
    #dataframes are built from the robust dictionary in master config, and so changes to master config csv should not be breaking
        
    #blank list for returning
    items = []       
    
    # build df from master config using all datasets ids
    config_list = []
    for key in dobj.config_key_dsid:
        config_list.append(dobj.config_key_dsid[key]) #should be whole dict
    
    # convert list to df
    df_test= pd.DataFrame(config_list)
    
    # subset and reorganise cols to match structure needed for this patch 0 dataset id 1 dataset raw 2 dataset label
    df_test = df_test[['dataset_id', 'dataset_raw', 'dataset_label', 'nav_cat', 'nav_cat_nest']]
    
    # cast dataset id col to string (needed for callback creation)
    df_test['dataset_id'] = df_test['dataset_id'].astype(str)        
    
    # subset dataframe
    df = df_test[df_test['nav_cat']==nav_cat]
            
    #extract list of unique nesting cats
    nests = pd.unique(df['nav_cat_nest'])
    
    logger.info("Creating %r nav items for category: %r",len(df), nav_cat)  
    
    # case all root nesting, simply add items
    if len(nests) == 1 and nests[0] == 'root':          
    
        #for each occurance in the category, add a dropdownmenu item and id based (ultimately) on master config
        for i in range(0,len(df)):    
                items.append(
                    dbc.DropdownMenuItem(
                        children=df.iloc[i,2], #dataset_label
                        id=df.iloc[i,0], #dataset_id        
                        #style={'marginTop':0, 'marginBottom':0},
                        ))
                
    # add nesting
    else:
        #print("not all roots")        
        
        #loop through categories and nest if needed
        for i in range(0,len(nests)):            
            if nests[i] == 'root':
                #subsample this nav_cat just to root items and add items menu
                r = df[df['nav_cat_nest']=='root'] 
                for j in range(0,len(r)):    
                    items.append(
                        dbc.DropdownMenuItem(
                            children=r.iloc[j,2], #dataset_label
                            id=r.iloc[j,0] #dataset_id        
                            ))
               
            #for anything not root, add nests
            else:
                #for each unique nest in this category, add a new submenu and populate
                items.append(
                    dbc.DropdownMenu(
                        label=nests[i],
                        direction='left',
                        toggle_style={'color':'grey', 'backgroundColor':'white', 'border': '0px', 'fontSize': INIT_NAVBAR_FONT_H, "marginBottom": 0, "marginTop": 0, "marginLeft": INIT_DROPDOWNITEM_LPAD, "marginRight": INIT_DROPDOWNITEM_RPAD,}, 
                        children=create_dash_layout_navbar_items_nests(nests[i], df),  
                    )
                )          
    
    return items


def create_dash_layout_navbar_items_nests(nest, df):
    #df is just for one particular nav_cat. Loop through and add any items to list
    items = []
    r = df[df['nav_cat_nest']==nest] 
    for j in range(0,len(r)):    
        items.append(
            dbc.DropdownMenuItem(                
                children=r.iloc[j,2], #dataset_label
                id=r.iloc[j,0] #dataset_id        
                ))    
    
    return items


def create_dash_layout_navbar_menu(dobj):    
    
    #construct the entire navbar menu recursively based on master config. Can return a list of dropdown menus, each with children (items) built recursively aswell
    logger.info("Building nav menu...")
       
    menu_list=[]

    # Add tool tip
    menu_list.append( dbc.Tooltip(
                "Randomly select a dataset!",
                target='random-button',
                placement='bottom',                
                ),)
    
    #Grab all navigation categories
    nav_cats = dobj.config_key_navcat    
    logger.info("Adding %r dataset categories...", len(nav_cats))
    
    #loop through unique nav_cats    
    for i in nav_cats:    
        logger.info("adding %r",nav_cats[i].get("nav_cat"))
        
        #logic for hiding unused categories
        if nav_cats[i].get("nav_cat") == "unused":
            display="none"
        else:
            display="block"        
        
        #extract colour for menuitem                    
        colour = nav_cats[i].get("colour")
        
        #add items to this menu list
        menu_list.append(
            dbc.DropdownMenu(
                children=create_dash_layout_navbar_items(nav_cats[i].get("nav_cat"), dobj),                
                size="sm",
                label=nav_cats[i].get("nav_cat"), 
                toggle_style={"display":display, "color": colour, 'backgroundColor':'#3E3F3A', 'border': '0px', 'fontSize': INIT_NAVBAR_FONT_H, "marginBottom": 0, "marginTop": 0, "marginLeft": INIT_DROPDOWNITEM_LPAD, "marginRight": INIT_DROPDOWNITEM_RPAD,},               
            ))
            
    
        
        
    menu_list.append(dbc.Button(INIT_RANDOM_BTN_TEXT,  outline=INIT_BTN_OUTLINE, color="danger", id="random-button", size=INIT_BUTTON_SIZE,
                                style={'display': 'inline-block', 'opacity':INIT_BUTTON_OPACITY, 'fontSize': INIT_RANDOM_BTN_FONT, "marginBottom": 0, "marginTop": 0, "marginLeft": INIT_DROPDOWNITEM_LPAD, "marginRight": INIT_DROPDOWNITEM_RPAD,},
                                ),)
    
    # add search DCC dropdown to list
    
    # get list of all datasets in config (list of dicts)
    dd_list = data.get_list_of_dataset_labels_and_raw(dobj.config_key_dsraw,"all")
    
    # sort list by dataset raw by converting to df and back
    dd_list = pd.DataFrame(dd_list).sort_values(by="dataset_label").to_dict('records') 
    
    # construct drop down list
    search_menu_list = []
    for i in range(0,len(dd_list)):        
        search_menu_list.append({'label': dd_list[i].get("dataset_label"), 'value': dd_list[i].get("dataset_raw")})
    
    menu_list.append(
        dcc.Dropdown(
                options=search_menu_list,
                id="nav-search-menu",
                multi=False,
                placeholder=f'Search {dobj.dataset_count:>3,} datasets and {dobj.observation_count:>3,} data points',
                clearable=True,
                style={'width':INIT_NAVBAR_SEARCH_WIDTH, "fontSize": INIT_NAVBAR_SEARCH_FONT},
                className='ml-auto',
                
            ),
        ),
    
    
   
    return menu_list
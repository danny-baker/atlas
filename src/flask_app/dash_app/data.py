# This file contains all helper functions required by main app at run-time

import json
import pandas as pd
import numpy as np
import matplotlib as mpl #colour
import copy
import sys
import time
from PIL import ImageColor
import os
from datetime import datetime, timedelta
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions, BlobClient, ContainerClient
from dotenv import load_dotenv
from dataclasses import dataclass

# add atlas/data folder to path (so we can access paths in /data/data_paths.py)
sys.path.append('/usr/src/app/data') #working dir for built container (see /Dockerfile)
sys.path.append('/home/dan/atlas/data') #testing on local machine (no docker)
from data_pipeline.data_paths import * 

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)



"""        
def check_year(pop, series, year):
           
    # get unique years from series
    #print("Testing. check_year function. Pop series year ",pop,series,year)
    df = pop.loc[(pop['dataset_raw'] == series)]
    
    # convert to list
    years = pd.DataFrame(pd.unique(df["year"]), columns=["value"])['value'].tolist()
           
    # return bool if year found
    return int(year) in years
    

def get_years(df):
    # strip out years from dataset and return as dictionary (for control input)
    df = df.sort_values('year')
    years = pd.DataFrame(pd.unique(df["year"]), columns=["value"])
    years = years["value"].to_dict()
    #print(years)
    return years



def get_year_slider_index(pop, series, year):
    
    #obtain relevant years for this series
    yr_slider = get_years(pop.loc[(pop['dataset_raw'] == series)])
        
    if len(yr_slider) > 0:
        for index in range(len(yr_slider)):  
            if yr_slider[index] == year: return index
            
    #otherwise return most recent    
    return len(yr_slider)-1


def get_year_slider_marks(series, pop, INIT_year_SLIDER_FONTSIZE, INIT_year_SLIDER_FONTCOLOR, year_slider_selected):    
    
    #obtain relevant years for this series and update slider
    year_slider_marks = get_years(pop.loc[(pop['dataset_raw'] == series)])
    
    # add styling to year slider        
    year_slider_marks2 = {
                    i: {
                        "label": year_slider_marks[i],
                        "style": {"fontSize": INIT_year_SLIDER_FONTSIZE, 'color':INIT_year_SLIDER_FONTCOLOR, 'fontWeight': 'normal'},
                    }
                    for i in range(0, len(year_slider_marks))
                }   
    
    year_slider_marks=year_slider_marks2     
     
    # shorten year labels if needed
    
    #10-20 = '91 style
    #if len(year_slider_marks) > 10 and len(year_slider_marks) <= 20:
    #    for i in range(0,len(year_slider_marks)):
    #        year_slider_marks[i]['label'] = "'"+str(year_slider_marks[i]['label'])[2:]
    #        #year_slider_marks[i]['style']['fontSize']=12
    
    
    #10-20 = '91 style
    if len(year_slider_marks) > 10 and len(year_slider_marks) <= 20:
        counter = 0
        for i in range(0,len(year_slider_marks)):   
            if i == 0 or i == len(year_slider_marks)-1:              
                continue    
            if counter != 1:
                year_slider_marks[i]['label'] = ""               
                counter = counter + 1
            else:                
                counter = 0
    
    
    
    #20-50 = every 5 yrs
    elif len(year_slider_marks) > 20 and len(year_slider_marks) <= 50:                    
        counter = 0
        for i in range(0,len(year_slider_marks)):   
            if i == 0 or i == len(year_slider_marks)-1:              
                continue    
            if counter != 4:
                year_slider_marks[i]['label'] = ""               
                counter = counter + 1
            else:                
                counter = 0
                
    #50-100 = every 10 yrs
    elif len(year_slider_marks) > 50 and len(year_slider_marks) <= 100:                      
        counter = 0
        for i in range(0,len(year_slider_marks)):  
            if i == 0 or i == len(year_slider_marks)-1:              
                continue   
            if counter != 9:
                year_slider_marks[i]['label'] = ""               
                counter = counter + 1
            else:                
                counter = 0
                
    #100-200 = every 20 yrs
    elif len(year_slider_marks) > 100 and len(year_slider_marks) <= 200:                      
        counter = 0
        for i in range(0,len(year_slider_marks)): 
            if i == 0 or i == len(year_slider_marks)-1:              
                continue 
            if counter != 19:
                year_slider_marks[i]['label'] = ""               
                counter = counter + 1
            else:                
                counter = 0
    
    #200+ = every 50 yrs
    elif len(year_slider_marks) > 200:                      
        counter = 0
        for i in range(0,len(year_slider_marks)):  
            if i == 0 or i == len(year_slider_marks)-1:              
                continue   
            if counter != 49:
                year_slider_marks[i]['label'] = ""               
                counter = counter + 1
            else:                
                counter = 0
    
    
    
    return year_slider_marks
"""


def get_series_and_year(df, year, series, ascending):
    #print("Get series. year %r, series %r, ascending %r", year, series, ascending)
    
    #Subset main dataframe for this series and year as a shallow copy (so we can cast value to Float)
    d = copy.copy(df[(df["year"] == int(year)) & (df["dataset_raw"] == series)]) #This could be a memory leak, or at least seems inefficient.
    
    d['value'] = d['value'].astype(float) 
    
    # dropping ALL duplicate values (THIS SHOULDNT BE NEEDED BUT SOME DATASETS MAY BE A LITTLE CORRUPTED. E.g 'Annual mean levels of fine particulate matter in cities, urban population (micrograms per cubic meter)'
    d = d.drop_duplicates(subset ="m49_un_a3")

    d = d.sort_values('value', ascending=ascending)
    return d

def get_series(df, series, ascending):
    #print("Get series. Series %r, ascending %r", series, ascending)
    d = copy.copy(df[(df["dataset_raw"] == series)])
    d['year'] = d['year'].astype(int)
    d['value'] = d['value'].astype(float)
    d = d.sort_values('value', ascending=ascending)
    return d

def update_3d_geo_data_JSON(df, geojson, colorscale, jellybean, var_type, discrete_colorscale):
    # This is used for the globe to help it mimic the main map colours etc.
    #update a copy of the geojson data to include series specific data from the passed in dataframe (subset) including label names, and colours
        
    #FIRST DO THE COLOUR INTERPOLATION
    
    #fix for removing note and source columns
    df['fix1'] = "dummmy"
    df['fix2'] = "dummy"
    
    #For continuous data we'll do linear color interpolation based on the extracted colorscale from the main map
    if var_type == "continuous" or var_type == "ratio" or var_type == "quantitative":
    
        #cast values to float
        df['value'] = df['value'].astype(float)  
        
        #drop values below zero (they cannot be displayed on current choropleth style)
        df = df[df.value > 0]  
        
        #transform the data values to log10 (zeros introduced where log not computed)
        df['value_log10'] = np.log10(df['value'], out=np.zeros_like(df['value']), where=(df['value']!=0))        
        
        #now drop any rows with zero vals (or it will be affected by subsequent colour interpolation logic)
        df = df[df.value_log10 != 0]       
        
        #translate data range to positive
        mn = np.min(df["value_log10"])
        mx = np.max(df["value_log10"])
        if mn < 0.0:            
            #print("Color correction, translating log vals")
            df['value_log10'] = df['value_log10'] + abs(mn)
        
        #now calculate the 0-1 ratio (normalise)
        df['f-log'] = df['value_log10'] / np.max(df["value_log10"]) #i.e. what proportion is it of the max   
        
        #get colorscale array from mapdata (this is variable length and can switch to RGB from Hex)
        #colorscale = map_data['data'][0]['colorscale'] #an list of colours e.g. [1.1111, #hexcolour]   
        
        if colorscale[0][1][0] != "#":
            #i.e. we have an RGB color array (happens after settings are changed), so convert to hex
            #print("RGB color array found in map data. Converting to hex")
            for i in range(0,len(colorscale)):              
                red = extractRed(colorscale[i][1])
                green = extractGreen(colorscale[i][1])
                blue = extractBlue(colorscale[i][1])
                hx = '#{:02x}{:02x}{:02x}'.format(red, green , blue)
                #print(red, green, blue, hx)
                colorscale[i][1] = hx #replace rgb string with hex string
        
        #print(df['f-log'])
        #print(colorscale)
        
        #based on the value for each row, obtain the two colours and mixing to interpolate between them!
        df['c1'] = df.apply(lambda row : extractColorPositions(colorscale, row['f-log'])[0], axis =1).astype(str)
        df['c2'] = df.apply(lambda row : extractColorPositions(colorscale, row['f-log'])[1], axis =1).astype(str)
        df['mix'] = df.apply(lambda row : extractColorPositions(colorscale, row['f-log'])[2], axis =1).astype(float)
        
        #get hex val by linear interpolation between c1, c2, mix for each row, and also convert this into the component RGB vals (for deck.gl)
        df['hex'] = df.apply(lambda row : colorFader(row['c1'], row['c2'], row['mix']), axis =1) #linear interpolation between two hex colours
        
        df['r'] = df.apply(lambda row : ImageColor.getcolor(row['hex'], "RGB")[0], axis =1).astype(str) #return the red (index 0 of tuple) from the RGB tuble returned by getcolor 
        df['g'] = df.apply(lambda row : ImageColor.getcolor(row['hex'], "RGB")[1], axis =1).astype(str) #return the greeen (index 0 of tuple) from the RGB tuble returned by getcolor 
        df['b'] = df.apply(lambda row : ImageColor.getcolor(row['hex'], "RGB")[2], axis =1).astype(str) #return the blue (index 0 of tuple) from the RGB tuble returned by getcolor 
          
        #print(df.columns)
        #print(colorscale)
    
    #For discrete data, set colour scales based on global lookup
    elif var_type == "discrete":                
        
        #mimic the same df structure as the continuous dataset, so the logic further below works (creating dummy columns)
        df['value_log10'] = "dummy"
        df['f-log'] = "dummy"
        df['c1'] = "dummy"
        df['c2'] = "dummy"
        df['mix'] = "dummy"
        df['hex'] = "dummy"  
        
        #obtain array of discrete categories
        discrete_cats = pd.unique(df['value'])
       
        #loop through unique discrete categories and set the hex value based on discrete colour scale lookup
        for i in range(0,len(discrete_cats)):                    
            df.loc[df['value']==discrete_cats[i], 'hex'] = discrete_colorscale[i][0][1]
        
        #Convert the hex value to separate R/G/B values as cols, as this data is needed by pdeck to render the globe        
        df['r'] = df.apply(lambda row : ImageColor.getcolor(row['hex'], "RGB")[0], axis =1).astype(str) #return the red (index 0 of tuple) from the RGB tuble returned by getcolor 
        df['g'] = df.apply(lambda row : ImageColor.getcolor(row['hex'], "RGB")[1], axis =1).astype(str) #return the greeen (index 0 of tuple) from the RGB tuble returned by getcolor 
        df['b'] = df.apply(lambda row : ImageColor.getcolor(row['hex'], "RGB")[2], axis =1).astype(str) #return the blue (index 0 of tuple) from the RGB tuble returned by getcolor 
    
    
    #NOW ADD COLOUR AND SERIES SPECIFIC DATA TO GEOJSON
    
    #deep copy globe geojson
    gj = copy.deepcopy(geojson)
   
    #loop through all 1300 geojson features and set the value based on current series
    for i in range(0, len(gj['features'])):
        try:                               
            
            #At this point, check if country name/val None (i.e. no data in DF), and grab the country name for the properties of the JSON, and set the value to 0            
            #if no data exists for a country in this series, store the country name from json, set val to 0, and set a nice grey colour so it displays on jigsaw
            if gj['features'][i]['properties']['sr_un_a3'] not in df["m49_un_a3"].values:
                #print(gj['features'][i]['properties']['BRK_NAME'])
                #gj['features'][i]['COUNTRY'] = gj['features'][i]['properties']['BRK_NAME'] #grab country name from json              
                gj['features'][i]['value'] = "no data"                    
                
                #Colour ocean blue
                if gj['features'][i]['COUNTRY'] == "Ocean" or gj['features'][i]['COUNTRY'] == "Caspian Sea":
                    gj['features'][i]['properties']['red'] = "134" #ocean blue
                    gj['features'][i]['properties']['green'] = "181"
                    gj['features'][i]['properties']['blue'] = "209"
                
                #Colour all other features missing data as grey
                else:
                    gj['features'][i]['properties']['red'] = "224" #grey
                    gj['features'][i]['properties']['green'] = "224"
                    gj['features'][i]['properties']['blue'] = "224"
                
            else:  
                #set value of current series to this row item in json               
                gj['features'][i]['value'] = df[df["m49_un_a3"]==gj['features'][i]['properties']['sr_un_a3']].iloc[0,4] #set geojson property to the value of the series for that country
                
                #colour the feature for this country based on the interpolated colours
                #print("\n Df cols. Need to know for red green blue bitch", df.columns)
                if jellybean == False:                    
                    gj['features'][i]['properties']['red']= df[df["m49_un_a3"]==gj['features'][i]['properties']['sr_un_a3']].iloc[0,14] #column index for red (these are added in in the code above)
                    gj['features'][i]['properties']['green']= df[df["m49_un_a3"]==gj['features'][i]['properties']['sr_un_a3']].iloc[0,15]
                    gj['features'][i]['properties']['blue']= df[df["m49_un_a3"]==gj['features'][i]['properties']['sr_un_a3']].iloc[0,16]
         
        except IndexError as error:
            print("Globe: Exception thrown attempting to build custom dict from json (expected)")
         
    
    return gj

def colorFader(c1,c2,mix=0): 
    #fade (linear interpolate) from color c1 (at mix=0) to c2 (mix=1)
    #c1 and c2 are hex colours, mix variable is a float point between 0 and 1, and colour will be interpolated and a hex colour will be returned
    c1=np.array(mpl.colors.to_rgb(c1))
    c2=np.array(mpl.colors.to_rgb(c2))
    return mpl.colors.to_hex((1-mix)*c1 + mix*c2)
   
def extractRed(rgb_str):
    #rip out the red    
    r = rgb_str.split(",")
    red = r[0].strip("rgb() ") #select red val from the array, and remove zeros    
    return int(red)


def extractGreen(rgb_str):
    #rip out the green    
    g = rgb_str.split(",")
    green = g[1].strip() #select red val from the array, and remove zeros    
    return int(green)
    
def extractBlue(rgb_str):
    #rip out the blue
    b = rgb_str.split(",")
    blue = b[2].strip("() ") #select red val from the array, and remove zeros    
    return int(blue)

def extractColorPositions(colorscale, val):
    #this function takes the given colour array and a value, and returns the respective c1, c2, mix vars needed for linear colour interpolation

    colorscale_r = copy.deepcopy(colorscale)
    
    #reverse colorscale
    for i in range(0, len(colorscale)):        
        colorscale_r[(len(colorscale)-1)-i][1] = colorscale[i][1]
    
    colorscale = copy.deepcopy(colorscale_r)
    
    #Find the val position in the colour scale, store the two colours and the mix level to interpolate between them based on val
    for i in range(0, len(colorscale)-1):    
        
        if val <= colorscale[i+1][0]:
            c1 = colorscale[i][1]
            c2 = colorscale[i+1][1]
            mix = (val - colorscale[i][0]) / (colorscale[i+1][0] - colorscale[i][0])    
            #print(c1)
            #print(c2)
            #print(mix)
            return c1, c2, mix
    return   





################# New abstraction work ######################









def read_blob(account_name, account_key, container_name, filepath, data_format, return_format):
    # A generic function for reading files from blob
    print("Attempting to read file:",filepath,"from Azure blob container:",container_name)
    
    
    
    if data_format == 'json':
        # presently all json files are returned as json
        constr = 'DefaultEndpointsProtocol=https;AccountName=' + account_name + ';AccountKey=' + account_key + ';EndpointSuffix=core.windows.net'
        blob_service_client = BlobServiceClient.from_connection_string(constr)
        container_client = blob_service_client.get_container_client(container_name)
        blob_client = container_client.get_blob_client(filepath)
        streamdownloader = blob_client.download_blob()
        file = json.loads(streamdownloader.readall())
        return file
    
    elif data_format == 'parquet' and return_format == 'dataframe':
        # read parquet, return dataframe
        #generate a shared access signature for the file
        sas_i = generate_blob_sas(account_name = account_name,
                                     container_name = container_name,
                                     blob_name = filepath,  # statistics/master_stats.parquet
                                     account_key=account_key,
                                     permission=BlobSasPermissions(read=True),
                                     expiry=datetime.utcnow() + timedelta(hours=1))

        #build sas URL using new sas sig
        sas_url = 'https://' + account_name+'.blob.core.windows.net/' + container_name + '/' + filepath + '?' + sas_i            
        df = pd.read_parquet(sas_url)
        return df
    
    elif data_format == 'csv' and return_format == 'dataframe':
        #read csv, return parquet
        
        #generate a shared access signature for the file
        sas_i = generate_blob_sas(account_name = account_name,
                                     container_name = container_name,
                                     blob_name = filepath,  # statistics/master_stats.parquet
                                     account_key=account_key,
                                     permission=BlobSasPermissions(read=True),
                                     expiry=datetime.utcnow() + timedelta(hours=1))

        #build sas URL using new sas sig
        sas_url = 'https://' + account_name+'.blob.core.windows.net/' + container_name + '/' + filepath + '?' + sas_i
        df = pd.read_csv(sas_url)
        return df
 
    else:
        print('ERROR trying to open file on blob')

def build_config_dicts(set_key_list: list, master_config: pd.DataFrame):
    #The successor to read_dataset_metadata using new master_config.csv
    #Returns a dictionary of dictionaries, with a specified parent key (for rapid lookup) 
    
    print('Building configuration dictionaries...')        
    
    # Remove all rows with unprocessed configurations (i.e. pipeline has run but not updated by human yet)
    master_config = master_config[~master_config['dataset_label'].isin(["TODO"])]
    master_config = master_config[~master_config['var_type'].isin(["TODO"])]
    master_config = master_config[~master_config['nav_cat'].isin(["TODO"])]
    master_config = master_config[~master_config['colour'].isin(["TODO"])]
    master_config = master_config[~master_config['nav_cat_nest'].isin(["TODO"])]
    
    # Remove any NaN's in config variables (human error may create these)    
    master_config = master_config.dropna(subset=['dataset_label','var_type','nav_cat','colour','nav_cat_nest']) #specify cols to drop rows with NaN in them        
     
    # convert df to list of dicts as records 
    dict_list = master_config.to_dict('records')
    
    # now build a new dict setting keys based on the passed in list
    
    # key:dataset_raw       {dataset_raw: {dataset_label:, dataset_id:, dataset_html:, var_type:, nav_cat, colour:, nav_cat_nest: }}    
    config_dict1 = {}
    for i in range(len(dict_list)): 
        key = dict_list[i].get(set_key_list[0]) #e.g set dataset_raw as key for parent dictionary
        value = dict_list[i] #value is the whole dictionary  
        config_dict1[key]=value
        
    # key:dataset_id        {dataset_id: {dataset_raw:, dataset_label:, dataset_html:, var_type:, nav_cat, colour:, nav_cat_nest: }}   
    config_dict2 = {}
    for i in range(len(dict_list)):  
        key = dict_list[i].get(set_key_list[1]) #e.g set dataset_id as key for parent dictionary
        value = dict_list[i] #value is the whole dictionary    
        config_dict2[key]=value
        
    # key:nav_cat           {nav_cat: {dataset_raw:, dataset_label:, dataset_id:, var_type:, colour:, nav_cat_nest: }} 
    config_dict3 = {}
    for i in range(len(dict_list)):  
        key = dict_list[i].get(set_key_list[2]) #e.g set nav_cat as key for parent dictionary
        value = dict_list[i] #value is the whole dictionary  
        config_dict3[key]=value

    # key:dataset_html
    config_dict4 = {}
    for i in range(len(dict_list)):  
        key = dict_list[i].get(set_key_list[3]) #e.g set dataset_html as key
        value = dict_list[i] #value is the whole dictionary  
        config_dict4[key]=value

    # key:dataset_label
    config_dict5 = {}
    for i in range(len(dict_list)):  
        key = dict_list[i].get(set_key_list[4]) #e.g set dataset_label as key
        value = dict_list[i] #value is the whole dictionary  
        config_dict5[key]=value
   
    return config_dict1, config_dict2, config_dict3, config_dict4, config_dict5


def add_html_friendly_dataset_labels(df) -> pd.DataFrame:
    
    # Add a new column to the master config dataframe representing the html friendly version of the dataset labels     
    
    # Copy the column we which to modify
    df['dataset_html'] = df['dataset_label'].copy()      

    # make api labels URL path friendly
    df['dataset_html'] = df['dataset_html'].str.replace(' ','-', regex=True)
    df['dataset_html'] = df['dataset_html'].str.replace('%','percent', regex=True)
    df['dataset_html'] = df['dataset_html'].str.replace('?','-', regex=False) 
    df['dataset_html'] = df['dataset_html'].str.replace('+','-', regex=False) 
    df['dataset_html'] = df['dataset_html'].str.replace(',','-', regex=False)
       
    return df


def get_list_of_dataset_labels_and_raw(master_config,var_type):

    # build and return list of dictionaries containing var_type, datset_raw, dataset_label
    # Special condition if var_type specified as "all" at calling, return all.
    # This is used heabily to subset datasets to build lots of the modal drop downs for charts.
    # Is this redundant??? seems like double work. Check. TODO
    
    config_list=[]
    for i in master_config:
        config_list.append({"dataset_raw":master_config[i].get("dataset_raw"),
                            "dataset_label":master_config[i].get("dataset_label"),
                            "dataset_id":master_config[i].get("dataset_id"),
                            "var_type":master_config[i].get("var_type"),
                            "nav_cat":master_config[i].get("nav_cat"),
                            "nav_cat_nest":master_config[i].get("nav_cat_nest")
                            
                            })
    
    # convert this to a df (so can sort and subset)
    df = pd.DataFrame(config_list).sort_values(by="dataset_label") 
    
    # subset based on var_type argument
    if var_type != "all": df = df[df["var_type"] == var_type]
    
    # convert df to list of dicts
    dict_list = df.to_dict('records')
    
    return dict_list


@dataclass
class url_path:  
    """
    The concept of a url path and it's elements to drive site behaviour. 
    It can be instantiated in a variety of ways based on a url path or directly (to allow creation from browser path or from callback)
    It must translate non-allowed chars in the path also    
    
    e.g.
    https://worldatlas.org/ -> ['http:', '', '127.0.0.1:5000', ''] -> {level: map, series: none, year: none}    
    https://worldatlas.org/Access-to-electricity-(percent-of-population)/map/2022 -> ['http:', '', '127.0.0.1:5000', 'map', '2022'] -> {level: map, series: Access-to-electricity-(percent-of-population), year: 2022}
    https://worldatlas.org/Access-to-electricity-(percent-of-population)/bar/2022 -> {level: bar, series: Access-to-electricity-(percent-of-population), year: 2022}
    https://worldatlas.org/Access-to-electricity-(percent-of-population)/line/ -> {level: line, series: Access-to-electricity-(percent-of-population), year: None}
    """

    url:str=None            # e.g. https://worldatlas.org/map/2022
    level:str='map'         # map/bar/line/etc.
    series_html:str=None    # html friendly version of series name
    year:str=None           # year, if relevant
    first_load:bool=True

    def __post_init__(self):
        # based on starting conditions, attempt to fill in the blanks

        # CASE: url supplied (populate other attributes of object)
        if self.url is not None:

            # split it on / and drop first 3 elements
            url_frags = self.url.split('/')[3:]
            print(url_frags)

            # CASE: root url (first load of site)
            # i.e. ['https:', '', 'worldatlas.org', ''] and we grap 4th element        
            if len(url_frags) == 1 and url_frags[0] == '':  
                # keep defaults and return
                return

            # CASE: line
            if len(url_frags) == 2:
                self.first_load = False
                self.series_html = url_frags[0]
                self.level = url_frags[1]
                self.year = None
            
            # CASE: map or bar
            if len(url_frags) == 3:
                self.first_load = False
                self.series_html = url_frags[0]
                self.level = url_frags[1]
                self.year = url_frags[2]
                return
            

        # CASE: url NOT supplied (build url from other attributes)
        else:
            first_load=False
            self.url = f'{self.series_html}/{self.level}/{self.year}'
            return






    


@dataclass
class Data:
    # abstract all static data used by app at run-time (load once)
    
    # geojson data
    map_lowres: json
    map_medres: json
    map_hires: json
    globe_land_lowres: json
    globe_ocean_lowres: json
    globe_land_hires: json
    globe_ocean_hires: json
    
    # statistics
    stats: pd.DataFrame
    
    # experimental data
    EXP_POWER_PLANTS_DF: pd.DataFrame 
    
    # config dicts    
    # These are all basically ways to index the metatdata which is dict of type {dataset_id, dataset_label, dataset_html, dataset_raw, var_type, nav_cat, nav_cat_nest, colour, var_type, source, link, note} 
    # Each dict entry is typically thought of as 'series' metadata 
    config_key_dsraw: dict 
    config_key_dsid: dict
    config_key_navcat: dict
    config_key_dshtml: dict # for url lookup
    config_key_dslabel: dict # for url lookup

    # helpers
    dataset_count: int = None
    observation_count: int = None
    dataset_list: list = None    

    def __post_init__(self):
        self.dataset_count = len(pd.unique(self.stats['dataset_raw'])) 
        self.observation_count= len(self.stats.index)
        self.dataset_list = pd.unique(self.stats['dataset_raw']) 
    
    
    def get_numerical_series(self) -> list[str]:
        # Return an alphabetically sorted list of raw series names for numerical series only (i.e. continuous, ratio, quantitative)
        # use case: chart drop down selectors (we don't want users to select discrete/categorical series so we must exclude them)

        series=[]
        for key in self.config_key_dsraw:
            #print(f'{key} {self.config_key_dsraw[key]['var_type']}')
            if self.config_key_dsraw[key]['var_type'] == 'discrete': continue
            series.append(key)
                                
        series.sort()     

        #HACK remove first x rows as they are not sorted for some strange fucking reason
        series = series[19:]
        
        return series



    
    def get_countries(self, series_name:str, year:int=None) -> list[str]:
        # Return an alphabetically ascending list of countries available for the given dataset series and year.
        
        if year is not None:
            df = self.stats.loc[(self.stats['dataset_raw'] == series_name) & (self.stats['year'] == year)]         
        else:
            df = self.stats.loc[(self.stats['dataset_raw'] == series_name)]  
        
        countries_df = np.sort(pd.unique(df['country'].astype(str)))
        countries_lst = countries_df.tolist()
        return countries_lst        

    
    def get_stats(self, series_name:str, year:int|None, sort_by:str, ascending:bool=True) -> pd.DataFrame:
        # Query master stats and return a dataframe with all stats for a given dataset_raw name and year 
        # Convert value to correct data type based on series metatdata               
        
        # Master df.dtypes
        # m49_un_a3      category
        # country        category
        # year             uint16
        # dataset_raw    category
        # value            object
        # continent      category

        # var_type: continuous, quantitative, ratio, discrete
        var_type = self.config_key_dsraw[series_name]['var_type']
        
        # Slice stats out from master
        if year == None:
            df = self.stats.loc[(self.stats['dataset_raw'] == series_name)]  
        else:
            df = self.stats.loc[(self.stats['dataset_raw'] == series_name) & (self.stats['year'] == year)]     
        
        # Cast 'values' to relevant datatype if possible 
        if var_type == 'quantitative':            
            df.loc[:, 'value'] = df['value'].astype(int)
        elif var_type == 'ratio' or var_type == 'continuous':            
            df.loc[:, 'value'] = df['value'].astype(float)
        
        # Perform sort logic        
        df = df.sort_values(by=sort_by, ascending=ascending) 
     
        return df
        
    def get_stats_for_line(self, series_name:str, highlight_countries:list) -> pd.DataFrame:
        # return a df structure suitable for ingesting into the go.Scatter chart

        # need to build chart data to feed into fig
        # year  countryA    countyB     countryC
        # 2021  23.1        43.3        954

        # query series from master dataset
        df = self.get_stats(series_name=series_name, year=None, sort_by='year', ascending=True)          

        # prepare list of df chunks for each country
        df_chunks = []

        for country in highlight_countries:
            # Prepare df chunks of type [year country(val)]
            
            # subset to given country
            cdf = df[(df['country'] == country)]             

            # strip out any duplicate years for this series and country (just in case)
            cdf = cdf.drop_duplicates(subset=['year'])

            # select out year and country cols
            cdf = cdf[['year','value']]

            # rename value column to country name
            cdf = cdf.rename(columns={'value':country})            
                        
            df_chunks.append(cdf)
        
        # We now have a list of df chunks we want to merge, noting some countries might have no data in a given year but we want to display ALL yrs so we will OUTER merge.
        # year  countryA    countyB     countryC
        # 2021  23.1        43.3        954
        # 2022  NaN         34          NaN

        # CASE: 1 country selected
        if len(df_chunks) == 1: return df_chunks[0]
        
        # CASE: 2 countries (just merge)
        if len(df_chunks) == 2:
            merged_df = pd.merge(df_chunks[0], df_chunks[1], on='year', how='outer') 
            return merged_df
        
        # CASE: 3 countries or more (loop merge)
        if len(df_chunks) > 2:
            # first build base to merge against
            merged_df = pd.merge(df_chunks[0], df_chunks[1], on='year', how='outer') 

            # iterate, merging each chunk against the base
            for i in range(2,len(df_chunks)):
                merged_df = pd.merge(merged_df, df_chunks[i], on='year', how='outer')
            
            return merged_df

    

    def get_stats_for_dl(self, series_name:str, year:int|None=None) -> pd.DataFrame:
        # Prepare a cleaned DF suitable for download with year as optional (e.g. map dl vs bar vs line)

        # gather userful vars    
        series = self.config_key_dsraw[series_name]          
        series_label = series['dataset_label']      
        source = series['source']      
        link = series['link']
        
        # Query master stats and return a dataframe with all stats for a given dataset_raw name    
        if year is None:                      
            df = self.stats.loc[(self.stats['dataset_raw'] == series_name)].sort_values(['year','country'])  
        else:            
            df = self.get_stats(series_name, year, sort_by='country' )           
                      
        # make it pretty
        df['m49_un_a3'] = df['m49_un_a3'].astype(str).str.zfill(3) 
        df['United Nations m49 country code'] = df['m49_un_a3']        
        df = df.rename(columns={'value':series_label}) 
        df = df.drop(columns=['dataset_raw', 'm49_un_a3', 'continent'])        
                        
        #merge in source information 
        df['Source'] = f"{source} {link}"
  
        return df


    def get_latest_year(self, series_name:str) -> int:
        # Return the most recent year available for the given dataset
        yr = max(self.stats.loc[(self.stats['dataset_raw'] == series_name), 'year'])
        return int(yr) 
    
    def get_years(self, series_name:str) -> list[str]:
        # strip out avail years from dataset and return as list of str ['2012', '2013', '2014'] etc
        years = pd.unique(self.stats.loc[(self.stats['dataset_raw'] == series_name), 'year']).astype(str).tolist()
        return years


def get_time_slider(dobj, series_name:str, year=None) -> dict[str,int]:
    # return a dictionary representing time slider properties to set for a given series, selecting most recent year
    # marks [[val,mark], ...]  i.e. [[2000: '2000'], [2001: '2001'], [2002: '2002'], ... ]
    # marks_dict {2000: '2000', 2001:'2001', 2003:'' ...}
    # use case: normal dataset selection 
    
    years = dobj.get_years(series_name)       

    if not len(years) > 0:
        print("ERROR time slider years fucked")
        return
    
    marks = [[int(item),item] for item in years]  
    
    # CASE: display every 5th year    
    if len(marks) > 20 and len(marks) <= 50: 
        counter = 0
        for i in range(0,len(marks)):   
            if i == 0 or i == len(marks)-1:                              
                continue # Ensure 1st and last mark are displayed
            if counter != 4:
                marks[i][1] = ""               
                counter += 1
            else:                
                counter = 0

        #stop overlay
        marks[-2][1]=''        
    
    # CASE: display every 10th year
    elif len(marks) > 50 and len(marks) <= 100: 
        counter = 0
        for i in range(0,len(marks)):   
            if i == 0 or i == len(marks)-1:                              
                continue # Ensure 1st and last mark are displayed
            if counter != 9:
                marks[i][1] = ""               
                counter += 1
            else:                
                counter = 0
        
        #stop overlay
        marks[-2][1]=''
        marks[-3][1]=''        
        marks[-4][1]=''
        marks[-5][1]=''

    # CASE: display every 20th year
    elif len(marks) > 100 and len(marks) <= 200: 
        counter = 0
        for i in range(0,len(marks)):   
            if i == 0 or i == len(marks)-1:                              
                continue # Ensure 1st and last mark are displayed
            if counter != 19:
                marks[i][1] = ""               
                counter += 1
            else:                
                counter = 0
        
        #stop overlay
        marks[-2][1]=''
        marks[-3][1]=''        
        marks[-4][1]=''
        marks[-5][1]=''        
        marks[-6][1]=''
        marks[-7][1]=''        
        marks[-8][1]=''
        marks[-9][1]=''

    # CASE: display every 50th year
    elif len(marks) > 200:
        counter = 0
        for i in range(0,len(marks)):   
            if i == 0 or i == len(marks)-1:                              
                continue # Ensure 1st and last mark are displayed
            if counter != 49:
                marks[i][1] = ""               
                counter += 1
            else:                
                counter = 0

        
    # set selection
    if year == None:
        value = marks[-1][0] #most recent yr
    else:
        value = year

    # Convert marks to dict 
    marks_dict = {item[0]:item[1] for item in marks }  

    time_slider = {'marks':marks_dict, 'value':value}

    return time_slider


   
    
    
    #if len(year_dict) > 0:
    #    year_index = list(year_dict)[-1]
    #    year = year_dict[year_index] #what is returned
    #   year_slider_marks = data.get_year_slider_marks(series, pop, INIT_year_SLIDER_FONTSIZE, INIT_year_SLIDER_FONTCOLOR, year_slider_selected)
    #   year_slider_max = len(year_slider_marks)-1
    #   year_slider_selected = year_slider_max #select the most recent year by default
    #    year_slider_marks[year_slider_selected]['style']['fontWeight']='bold' #mark selected year bold  

   


def load(debug_mode: bool) -> Data:
    # Load all data either from local snapshot our cloud store based on debug flag. Return each item.
       
    if debug_mode:
        print('Loading data from local disk...')
        os.chdir(os.getcwd() + '/data')   #TODO change this when running docker. Will not run. Maybe use home ~ default in Dockerfile?? so can be universal?     
        
        # 2d map geojson polygons
        map_lowres = json.load(open(os.getcwd() + '/' + MAP_JSON_LOW_PATH_TITANIUM, 'r', encoding='utf-8'))
        map_medres = json.load(open(os.getcwd() + '/' + MAP_JSON_MED_PATH_TITANIUM, 'r', encoding='utf-8'))
        map_hires = json.load(open(os.getcwd() + '/' + MAP_JSON_HIGH_PATH_TITANIUM, 'r', encoding='utf-8'))
        
        # 3d globe geojson polygons
        globe_land_lowres = json.load(open(os.getcwd() + '/' + GLOBE_JSON_LAND_LOW_PATH_TITANIUM, 'r', encoding='utf-8'))
        globe_ocean_lowres = json.load(open(os.getcwd() + '/' + GLOBE_JSON_OCEAN_LOW_PATH_TITANIUM, 'r', encoding='utf-8'))
        globe_land_hires = json.load(open(os.getcwd() + '/' + GLOBE_JSON_LAND_HIGH_PATH_TITANIUM, 'r', encoding='utf-8'))
        globe_ocean_hires = json.load(open(os.getcwd() + '/' + GLOBE_JSON_OCEAN_LOW_PATH_TITANIUM, 'r', encoding='utf-8'))
        del(globe_ocean_lowres['features'][0]['geometry']['coordinates'][12]) #americas, also a problem on ne50m. Fix this later in pipeline.
        
        # statistics
        stats = pd.read_parquet(os.getcwd() + '/' + MASTER_STATS_PATH)
        
        # experimental data
        EXP_POWER_PLANTS_DF = pd.read_parquet(os.getcwd() + '/' + PWR_STN_PATH_TITANIUM)
        
        # load master config
        config_df = pd.read_csv(os.getcwd() + '/' + MASTER_CONFIG_PATH)  
        
        print('Success.')
        
    else:
        print('Loading data from blob...')
        # Get Azure Blob credentials for cloud data (if not in debug mode)
        load_dotenv() # read .env file in cwd
        container_name  = os.getenv("AZURE_STORAGE_ACCOUNT_CONTAINER_NAME")
        account_name = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
        account_key = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
        #sudo docker run -p 80:8050 -v /home/dan/atlas/.env:/usr/src/app/.env ghcr.io/danny-baker/atlas/atlas_app:latest 
        
        # 2d map geojson polygons
        map_lowres = read_blob(account_name, account_key, container_name, MAP_JSON_LOW_PATH_TITANIUM, 'json', 'json')
        map_medres = read_blob(account_name, account_key, container_name, MAP_JSON_MED_PATH_TITANIUM, 'json', 'json')
        map_hires = read_blob(account_name, account_key, container_name, MAP_JSON_HIGH_PATH_TITANIUM, 'json', 'json')
        
        # 3d globe geojson polygons
        globe_land_hires = read_blob(account_name, account_key, container_name, GLOBE_JSON_LAND_HIGH_PATH_TITANIUM, 'json', 'json') 
        globe_ocean_hires = read_blob(account_name, account_key, container_name, GLOBE_JSON_OCEAN_HIGH_PATH_TITANIUM, 'json', 'json') 
        globe_land_lowres = read_blob(account_name, account_key, container_name, GLOBE_JSON_LAND_LOW_PATH_TITANIUM, 'json', 'json') 
        globe_ocean_lowres = read_blob(account_name, account_key, container_name, GLOBE_JSON_OCEAN_LOW_PATH_TITANIUM, 'json', 'json') 
        del(globe_ocean_lowres['features'][0]['geometry']['coordinates'][12]) #americas, also a problem on ne50m. Fix this later in pipeline.
        
        # statistics
        stats = read_blob(account_name, account_key, container_name, MASTER_STATS_PATH, 'parquet', 'dataframe')
        
        # experimental data
        EXP_POWER_PLANTS_DF = read_blob(account_name, account_key, container_name, PWR_STN_PATH_TITANIUM, 'parquet', 'dataframe')
        
        # load master config
        config_df = read_blob(account_name, account_key, container_name, MASTER_CONFIG_PATH, 'csv', 'dataframe')
        
        print('Success.')
        
    # Add html dataset labels to master config
    config_df = add_html_friendly_dataset_labels(config_df)

    # build config dictionaries
    config_key_dsraw, config_key_dsid, config_key_navcat, config_key_dshtml, config_key_dslabel = build_config_dicts(['dataset_raw', 'dataset_id', 'nav_cat', 'dataset_html', 'dataset_label'], config_df)    
    #print(config_key_dsid[5])
    print(config_key_dshtml['Biodiversity-Red-List-Index'])

    # build data object
    data_obj = Data(map_lowres=map_lowres,
                    map_medres=map_medres,
                    map_hires=map_hires,
                    globe_land_lowres=globe_land_lowres,
                    globe_ocean_lowres=globe_ocean_lowres,
                    globe_land_hires=globe_land_hires,
                    globe_ocean_hires=globe_ocean_hires,
                    stats=stats,
                    EXP_POWER_PLANTS_DF=EXP_POWER_PLANTS_DF,
                    config_key_dsraw=config_key_dsraw,
                    config_key_dsid=config_key_dsid,
                    config_key_navcat=config_key_navcat,
                    config_key_dshtml=config_key_dshtml,
                    config_key_dslabel=config_key_dslabel                              
                    )    
    
    return data_obj

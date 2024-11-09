# This file contains all helper functions required by main app at run-time

import json
import pandas as pd
import numpy as np
import matplotlib as mpl #colour
import copy
import time
from PIL import ImageColor
import os
from datetime import datetime, timedelta
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions, BlobClient, ContainerClient


def get_list_of_dataset_labels_and_raw(master_config,var_type):

    # build and return list of dictionaries containing var_type, datset_raw, dataset_label
    # Special condition if var_type specified as "all" at calling, return all.
    # This is used heabily to subset datasets to build lots of the modal drop downs for charts.
    
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



def read_master_config(set_key_list, account_name, account_key, container_name, filepath):
    #The successor to read_dataset_metadata using new master_config.csv
    #Returns a dictionary of dictionaries, with a specified parent key (for rapid lookup)
  
    #master_config = d.read_master_config("dataset_raw") #used to lookup metadata based on dataset raw (often thru the app)
    #master_config_key_datasetid = d.read_master_config("dataset_id") #used by main callback upon user selection from navbar and key is datasetID (integer)
    #master_config_key_nav_cat = d.read_master_config("nav_cat") #used to lookup colour when constructing nav menu
    
    print('Building configuration dictionaries...')
    
    # Read in config csv as df
    master_config = read_blob(account_name, account_key, container_name, filepath, 'csv', 'dataframe')
    
    # Remove all rows with unprocessed configurations (i.e. pipeline has run but not updated by human yet)
    master_config = master_config[~master_config['dataset_label'].isin(["TODO"])]
    master_config = master_config[~master_config['var_type'].isin(["TODO"])]
    master_config = master_config[~master_config['nav_cat'].isin(["TODO"])]
    master_config = master_config[~master_config['colour'].isin(["TODO"])]
    master_config = master_config[~master_config['nav_cat_nest'].isin(["TODO"])]
    
    # Remove any NaN's in config variables (human error may create these)    
    master_config = master_config.dropna(subset=['dataset_label','var_type','nav_cat','colour','nav_cat_nest']) #specify cols to drop rows with NaN in them
        
    # transform df into dictionary of dictionaries
     
    # convert df to list of dicts as records 
    dict_list = master_config.to_dict('records')
    
    # now build a new dict setting keys based on the passed in list
    config_dict1 = {}
    for i in range(len(dict_list)):             
        # set key and values from this item on the list of dicts
        key = dict_list[i].get(set_key_list[0]) #e.g set dataset_raw as key for parent dictionary
        value = dict_list[i] #value is the whole dictionary     
        # insert item to dictionary (if duplicate dataset_raw in csv, it will only add 1, so this kind of filters crud)
        config_dict1[key]=value
        
    config_dict2 = {}
    for i in range(len(dict_list)):             
        # set key and values from this item on the list of dicts
        key = dict_list[i].get(set_key_list[1]) #e.g set dataset_id as key for parent dictionary
        value = dict_list[i] #value is the whole dictionary     
        # insert item to dictionary (if duplicate dataset_raw in csv, it will only add 1, so this kind of filters crud)
        config_dict2[key]=value
        
    config_dict3 = {}
    for i in range(len(dict_list)):             
        # set key and values from this item on the list of dicts
        key = dict_list[i].get(set_key_list[2]) #e.g set nav_cat as key for parent dictionary
        value = dict_list[i] #value is the whole dictionary     
        # insert item to dictionary (if duplicate dataset_raw in csv, it will only add 1, so this kind of filters crud)
        config_dict3[key]=value  
   
    return config_dict1, config_dict2, config_dict3



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
        
    
    

def create_api_lookup_dicts(master_config):
    
    # The goal of this is to modify the dataset raw and label strings to be URL path friendly
    # These are then put into dictionaries that are used to confert a URL path (api_label) to the original
    # At runtime, so queries can be performed on the master dataset.
        
    # get list of master config dictionaries
    config_list = get_list_of_dataset_labels_and_raw(master_config,"all")
    
    # convert this to a df
    df = pd.DataFrame(config_list)
    
    # subset it into a 3 col format
    df = df[['dataset_raw', 'dataset_label', 'dataset_label']].copy()
        
    # rename cols
    df.columns=['dataset_raw', 'dataset_label', 'api_label']       
    
    # make api labels URL path friendly
    df['api_label'] = df['api_label'].str.replace(' ','-', regex=True)
    df['api_label'] = df['api_label'].str.replace('%','percent', regex=True)
    df['api_label'] = df['api_label'].str.replace('?','-', regex=False) 
    df['api_label'] = df['api_label'].str.replace('+','-', regex=False) 
    df['api_label'] = df['api_label'].str.replace(',','-', regex=False)
    
    # declare new global dicts
    api_dict_raw_to_label={}
    api_dict_label_to_raw={}
    
    # build lookup dictionaries by iterating the DF (ineffecient but will do for now)
    for index,row in df.iterrows():
        api_dict_raw_to_label[row['dataset_raw']]=row['api_label']
        api_dict_label_to_raw[row['api_label']]=row['dataset_raw']
        
    return api_dict_raw_to_label, api_dict_label_to_raw


        
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



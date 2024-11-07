# Process data in staging -> copper
# step 1: run sequentially (old way)
# step 2: run in parallel (magic way)

from dotenv import load_dotenv
#from . import data_paths as paths
import json
import pandas as pd
import numpy as np
import glob
import os
import sys
import shutil
import time
import datetime
import matplotlib.pyplot as plt
import copy
#from azure.storage.blob import BlobServiceClient, BlobPrefix

from azure.storage.blob import (
    BlobServiceClient,
    BlobPrefix,
    ContainerClient,
    BlobClient,
    BlobSasPermissions,
    ContainerSasPermissions,
    ResourceTypes,
    AccountSasPermissions,
    UserDelegationKey,
    generate_account_sas,
    generate_container_sas,
    generate_blob_sas
)
#from py7zr import pack_7zarchive, unpack_7zarchive


# Azure storage blob config (access cloud data)
load_dotenv()
container_name  = os.getenv("AZURE_STORAGE_ACCOUNT_CONTAINER_NAME")
account_name = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
account_key = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")


def process_STAGING():
    # process STAGING => COPPER
    create_unique_country_list(paths.COUNTRY_LOOKUP_PATH_STAGING,paths.COUNTRY_LOOKUP_PATH_COPPER) #make this parquet?
    coppersmith_gapminder_fast_track(paths.FASTTRACK_PATH_STAGING, paths.FASTTRACK_PATH_COPPER, 'latin-1')
    coppersmith_gapminder_systema_globalis(paths.SYSTEMAGLOBALIS_PATH_STAGING, paths.SYSTEMAGLOBALIS_PATH_COPPER, 'latin-1')
    coppersmith_gapminder_world_dev_indicators(paths.WDINDICATORS_PATH_STAGING, paths.WDINDICATORS_PATH_COPPER, 'latin-1')
    coppersmith_sdgindicators(paths.SDG_PATH_STAGING, paths.SDG_PATH_COPPER) #Slow due to excel reader
    ##coppersmith_sdgindicators_new()
    coppersmith_map_json()
    coppersmith_globe_json()
    coppersmith_world_standards(paths.WS_PATH_STAGING, paths.WS_PATH_COPPER, 'latin-1')
    coppersmith_global_power_stations() #special data   
    coppersmith_bigmac(paths.BIG_MAC_PATH_STAGING, paths.BIG_MAC_PATH_COPPER)

    return


# Process country list (origin from UN?) to zero pad integers and store
def create_unique_country_list(path_origin, path_destination):     
    
    path_origin = os.getcwd()+path_origin
    path_destination = os.getcwd()+path_destination
    
    #read in m49 codes from csv
    c =  pd.read_csv(
       path_origin,
       encoding="utf-8",
       names=["m49_a3_country", "country", "continent", "region_un", "region_wb", "su_a3"],
    )
    
    #cast to string
    c["m49_a3_country"] = c["m49_a3_country"].astype(str) 
    
    #pad the 3 digit m49 country integer with zeros if it less than 100 (i.e. "3" will become "003")
    c['m49_a3_country'] = c['m49_a3_country'].str.zfill(3)  
    
    # delete first row (column headings)
    c = c.iloc[1:,]
    
    #write csv to file (overwrite by default)
    c.to_csv(path_destination,index=False)

    return

def coppersmith_gapminder_fast_track(origin, destination, encoding):
    # origin
    # https://github.com/open-numbers/ddf--gapminder--fasttrack
    
    #simply recursively convert all csvs to parquet and dump them in an equivalent folder in COPPER (create if needed)      
    tic = time.perf_counter()
    print("Processing gapminder fast track STAGING > COPPER")    
    convert_folder_csv_to_parquet_disk(origin, destination, encoding)
    toc = time.perf_counter()
    print("Processing time: ",toc-tic," seconds")
    return


def coppersmith_gapminder_systema_globalis(origin, destination, encoding):
    # origin
    # https://github.com/open-numbers/ddf--gapminder--systema_globalis
    
    #simply recursively convert all csvs to parquet and dump them in an equivalent folder in COPPER (create if needed)
    tic = time.perf_counter()
    print("Processing gapminder systema globalis STAGING > COPPER")    
    convert_folder_csv_to_parquet_disk(origin, destination, encoding)
    toc = time.perf_counter()
    print("Processing time: ",toc-tic," seconds")
    return

def coppersmith_gapminder_world_dev_indicators(origin, destination, encoding):
    # origin
    # https://github.com/open-numbers/ddf--open_numbers--world_development_indicators
    
    #simply recursively convert all csvs to parquet and dump them in an equivalent folder in COPPER (create if needed)
    tic = time.perf_counter()
    print("Processing gapminder world dev indicators STAGING > COPPER")    
    convert_folder_csv_to_parquet_disk(origin, destination, encoding)
    toc = time.perf_counter()
    print("Processing time: ",toc-tic," seconds")
    return

def coppersmith_undata(origin, destination, encoding):
    #simply recursively convert all csvs to parquet and dump them in an equivalent folder in COPPER (create if needed)
    tic = time.perf_counter()
    print("Processing gapminder UN data indicators STAGING > COPPER")
    convert_folder_csv_to_parquet_disk(origin, destination, encoding)    
    toc = time.perf_counter()
    print("Processing time: ",toc-tic," seconds")
    return

def coppersmith_sdgindicators(origin, destination):
    #simply recursively convert all xlsx files to parquet and dump them in an equivalent folder in COPPER (create if needed)
    tic = time.perf_counter()
    print("Processing sdg indicators STAGING > COPPER")   
    convert_folder_xlsx_to_parquet(origin, destination)
    toc = time.perf_counter()
    print("Processing time: ",toc-tic," seconds")
    return

def coppersmith_sdgindicators_new():
    # source
    # https://unstats.un.org/sdgs/indicators/database/archive
    # Still need to do lots of work to parse this properly. Can get 1.7GB CSV with all data and all years.
    
    # new file is a 1.7GB csv so we need to do some wrangling to even get it to a raw parquet
    
    origin = os.getcwd()+'/data_lakehouse/staging/statistics/sdgindicators_new/2024_Q1.2_AllData_Before_20240628.csv'
    destination_path =  os.getcwd()+'/data_lakehouse/copper/statistics/sdgindicators_new/'
    destination_filepath = destination_path+'sdgindicators_new.parquet'
    
    #Check if destination folder exists. If not, create it.
    if not os.path.exists(destination_path): os.mkdir(destination_path)  
    
    # Read in big bertha csv
    df0 = pd.read_csv(origin)
    
    # Subset the cols we need
    df1 = df0[['GeoAreaCode', 'GeoAreaName', 'TimePeriod', 'SeriesDescription', 'Value', 'Goal', 'Target', 'Indicator', 'ReleaseName', 'SeriesCode', 'Source', 'FootNote', 'Location','Age', 'Sex', 'Units', 'Quantile']]
                   
    # free mem
    del df0
    
    # data typing 
    df1 = df1.astype({'GeoAreaCode': 'uint16', 
                    'GeoAreaName':'category', 
                    'TimePeriod':'uint16', 
                    'SeriesDescription':'category', 
                    'Value':'str', 
                    'Goal':'str',
                    'Target':'str',
                    'Indicator':'str',
                    'ReleaseName':'str',
                    'SeriesCode':'str',
                    'Source':'str',
                    'FootNote':'str',
                    'Location':'str',
                    'Age':'str',
                    'Sex':'str',
                    'Units':'str',
                    'Quantile':'str',
                    })
    
    # write to parquet   
    df1.to_parquet(destination_filepath, engine='pyarrow', index=False)
    
    return
    
    


def coppersmith_map_json():
    #The map json (from memory) was unprocessed, sourced from Natural Earth
    # As it will be zipped up in STAGING, basically we just need to unzip it and move it to titanium during pipeline run 
        
    #Check if destination folder exists. If not, create it.
    if not os.path.exists(os.getcwd()+paths.MAP_JSON_PATH): os.mkdir(os.getcwd()+paths.MAP_JSON_PATH)  
    
    low_res_filepath_origin = os.getcwd()+paths.MAP_JSON_LOW_PATH_STAGING
    med_res_filepath_origin = os.getcwd()+paths.MAP_JSON_MED_PATH_STAGING
    high_res_filepath_origin = os.getcwd()+paths.MAP_JSON_HIGH_PATH_STAGING
    low_res_filepath_destination = os.getcwd()+paths.MAP_JSON_LOW_PATH_TITANIUM
    med_res_filepath_destination = os.getcwd()+paths.MAP_JSON_MED_PATH_TITANIUM
    high_res_filepath_destination = os.getcwd()+paths.MAP_JSON_HIGH_PATH_TITANIUM
    
    #unzip (in future)
    
    # do any processing (in future)
    
    # copy to titanium (assume folder structure undamaged)
    shutil.copyfile(low_res_filepath_origin, low_res_filepath_destination)
    shutil.copyfile(med_res_filepath_origin, med_res_filepath_destination)
    shutil.copyfile(high_res_filepath_origin, high_res_filepath_destination)
    
    return

def coppersmith_globe_json():
    # Attempt to process raw 3d json data for globe visualisation. FAIL.
    # This is really tricky, and some preprocessing was clearly done to prepare data for the cleaner functions. I never saved it.
    # In the interests of time, just storing processed data in staging to conform to the lakehouse architecture, if it ever needs to be processed.
    
    # This requires the titanium/globe folder to exist.
    
    #Check if destination folder exists. If not, create it.
    if not os.path.exists(os.getcwd()+paths.GLOBE_JSON_PATH): os.mkdir(os.getcwd()+paths.GLOBE_JSON_PATH) 
    
    # origin paths
    land_low_res_filepath_origin = os.getcwd()+paths.GLOBE_JSON_LAND_LOW_PATH_STAGING
    ocean_low_res_filepath_origin = os.getcwd()+paths.GLOBE_JSON_OCEAN_LOW_PATH_STAGING
    land_high_res_filepath_origin = os.getcwd()+paths.GLOBE_JSON_LAND_HIGH_PATH_STAGING
    ocean_high_res_filepath_origin = os.getcwd()+paths.GLOBE_JSON_OCEAN_HIGH_PATH_STAGING
    
    # destination paths
    land_low_res_filepath_destination = os.getcwd()+paths.GLOBE_JSON_LAND_LOW_PATH_TITANIUM
    ocean_low_res_filepath_destination = os.getcwd()+paths.GLOBE_JSON_OCEAN_LOW_PATH_TITANIUM
    land_high_res_filepath_destination = os.getcwd()+paths.GLOBE_JSON_LAND_HIGH_PATH_TITANIUM
    ocean_high_res_filepath_destination = os.getcwd()+paths.GLOBE_JSON_OCEAN_HIGH_PATH_TITANIUM
        
    #unzip (in future)
    
    # do any processing (in future)
    
    # copy to titanium (assume folder structure undamaged)
    shutil.copyfile(land_low_res_filepath_origin, land_low_res_filepath_destination)
    shutil.copyfile(ocean_low_res_filepath_origin, ocean_low_res_filepath_destination)
    shutil.copyfile(land_high_res_filepath_origin,land_high_res_filepath_destination )
    shutil.copyfile(ocean_high_res_filepath_origin, ocean_high_res_filepath_destination)
    
    # Some testing
    # Most need the countries list (for scraping suA3)
    #countries = get_unique_country_list()
    
    # start with land ne_50m FAIL
    #origin_filepath = os.getcwd()+"/data_lakehouse/staging/geojson/natural_earth/globe/land/ne_50m/ne_50m.geojson"
    #destination_filepath = os.getcwd()+"/data_lakehouse/titanium/geojson/globe/ne_50m.geojson"
    #lean_3d_land_data_JSON_ne50m(origin_filepath, countries, destination_filepath)
    
    #geojson_globe_countries_ne50m = d.clean_3d_land_data_JSON_ne50m("data/geojson/globe/ne_50m_land.geojson", country_lookup) #helper: this file has been modified to add in un_a3 integer identifiers. 
    #geojson_globe_land_cultural_ne110m = d.clean_3d_land_data_JSON_ne110m("data/geojson/globe/ne_110m_land_cultural.geojson") #helper function to clean and prepare
    
    return

def coppersmith_global_power_stations():
    # process the experimental globe powerstation dataset. Special treatment here as there are 2 files. One json and one CSV
    # We will process csv to parquet and dump both json and parquet directly into titanium (special data)
    
    tic = time.perf_counter()
    print("Processing global power station data STAGING > TITANIUIM (special)") 
    
    origin = paths.PWR_STN_PATH_STAGING
    destination = paths.PWR_STN_PATH_TITANIUM
    encoding = 'utf-8'
    filepath_json_origin = os.getcwd()+origin+"xp1_countries.geojson"
    filepath_json_destination = os.getcwd()+destination+"xp1_countries.geojson"
    
    #First convert csv to parquet and dump in titanium       
    convert_folder_csv_to_parquet_disk(origin, destination, encoding)
    
    #Next copy the geojson into same folder (so they stay together)
    shutil.copyfile(filepath_json_origin, filepath_json_destination)      
    
    toc = time.perf_counter()
    print("Processing time: ",toc-tic," seconds")
    return

def coppersmith_world_standards(origin, destination, encoding):
    #simply recursively convert all csvs to parquet and dump them in an equivalent folder in COPPER (create if needed)
    tic = time.perf_counter()
    
    #origin = "/data_lakehouse/staging/statistics/world-standards-unofficial-website/"
    #destination = "/data_lakehouse/copper/statistics/world-standards-unofficial-website/"
    
    print("Processing world standards STAGING > COPPER")    
    convert_folder_csv_to_parquet_disk(origin, destination, encoding)
    toc = time.perf_counter()
    print("Processing time: ",toc-tic," seconds")
        
    return

def coppersmith_bigmac(origin, destination):
    # origin
    # https://github.com/TheEconomist/big-mac-data
    # https://github.com/theeconomist/big-mac-data/releases/tag/2024-01
    
    origin_filepath = os.getcwd()+origin
    destination_path = os.getcwd()+destination
    destination_filepath = destination_path+'big-mac-index.parquet'
    
    # Read the index
    df = pd.read_csv(origin_filepath)    

    #Check if destination folder exists. If not, create it.
    if not os.path.exists(destination_path): os.mkdir(destination_path)  
    
    # Write parquet to disk
    df.to_parquet(destination_filepath, engine='pyarrow', index=False)   
    
    return

def convert_folder_csv_to_parquet_disk(origin_path, destination_path, encoding):
    #Helper function to convert a whole folder of .csv files to .parquet with same names in the destination
     
    origin_path = os.getcwd()+origin_path 
    destination_path = os.getcwd()+destination_path
  
    #Check if destination folder exists. If not, create it.
    if not os.path.exists(destination_path): os.mkdir(destination_path)  

    for filepath in glob.iglob(origin_path+'*.csv'):
        print(filepath)
        convert_csv_to_parquet(filepath, destination_path, encoding)
    
    return


def create_account_sas(account_name: str, account_key: str):
    # Create an account SAS that's valid for one day
    start_time = datetime.datetime.now(datetime.timezone.utc)
    expiry_time = start_time + datetime.timedelta(days=1)

    # Define the SAS token permissions
    sas_permissions=AccountSasPermissions(read=True)

    # Define the SAS token resource types
    # For this example, we grant access to service-level APIs
    sas_resource_types=ResourceTypes(service=True)

    sas_token = generate_account_sas(
        account_name=account_name,
        account_key=account_key,
        resource_types=sas_resource_types,
        permission=sas_permissions,
        expiry=expiry_time,
        start=start_time
    )

    return sas_token


def convert_folder_csv_to_parquet_blob():
    #blob version of disk version 

    print('Convert folder csv -> parquet in blob')
    #print('container name: ',container_name)
    print('storage account: ',account_name)
    #print('account key: ',account_key)

    # paths    
    origin_container_name = 'staging'
    origin_path = 'statistics/gapminder_fast-track/'
    destination_container_name = 'copper'
    destination_path = 'copper/gapminder_fast-track/'
    encoding = 'latin-1'
    

    

    # list files in origin container
    


    """
    sas_i = generate_blob_sas(account_name = account_name,
                                     container_name = container_name,
                                     blob_name = filepath,  # statistics/master_stats.parquet
                                     account_key=account_key,
                                     permission=BlobSasPermissions(read=True),
                                     expiry=datetime.utcnow() + timedelta(hours=1))

        #build sas URL using new sas sig
        sas_url = 'https://' + account_name+'.blob.core.windows.net/' + container_name + '/' + filepath + '?' + sas_i            
        df = pd.read_parquet(sas_url)
        """

### RUN ###

# create account SAS (should have full access to all containers)
sas_token = create_account_sas(account_name, account_key)
print(sas_token)

#convert_folder_csv_to_parquet_blob()

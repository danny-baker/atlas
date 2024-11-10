# Process data in staging -> copper (Azure Blob Data lake)
# step 1: run sequentially (old way)
# step 2: run in parallel (magic way)
    # https://learn.microsoft.com/en-us/python/api/overview/azure/storage-file-datalake-readme?view=azure-python

from dotenv import load_dotenv
import data_paths as paths
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
from io import BytesIO

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




def process_staging(blob_service_client, container_name_origin, container_name_destination):
    # process STAGING => COPPER
    #create_unique_country_list(paths.COUNTRY_LOOKUP_PATH_STAGING,paths.COUNTRY_LOOKUP_PATH_COPPER) #make this parquet?
   
    #coppersmith_gapminder_systema_globalis(paths.SYSTEMAGLOBALIS_PATH_STAGING, paths.SYSTEMAGLOBALIS_PATH_COPPER, 'latin-1')
    #coppersmith_gapminder_world_dev_indicators(paths.WDINDICATORS_PATH_STAGING, paths.WDINDICATORS_PATH_COPPER, 'latin-1')
    #coppersmith_sdgindicators(paths.SDG_PATH_STAGING, paths.SDG_PATH_COPPER) #Slow due to excel reader
    ##coppersmith_sdgindicators_new()
    #coppersmith_map_json()
    #coppersmith_globe_json()
    #coppersmith_world_standards(paths.WS_PATH_STAGING, paths.WS_PATH_COPPER, 'latin-1')
    #coppersmith_global_power_stations() #special data   
    #coppersmith_bigmac(paths.BIG_MAC_PATH_STAGING, paths.BIG_MAC_PATH_COPPER)
    
    print('Process staging...')
    coppersmith_gapminder_fast_track(blob_service_client, container_name_origin, container_name_destination, paths.FASTTRACK_PATH_STAGING, paths.FASTTRACK_PATH_COPPER, 'latin-1')

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

def coppersmith_gapminder_fast_track(blob_service_client: object, container_name_origin: str, container_name_destination: str, blob_folder_origin: str, blob_folder_destination: str, encoding: str):
    # origin
    # https://github.com/open-numbers/ddf--gapminder--fasttrack
    
    #recursively convert all csvs to parquet and dump them in a folder    
    tic = time.perf_counter()
    print("Processing gapminder fast track STAGING > COPPER")    
    convert_folder_csv_to_parquet_blob(blob_service_client, container_name_origin, container_name_destination, blob_folder_origin, blob_folder_destination, encoding)
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

    # Define the SAS token permissions (root)
    sas_permissions=AccountSasPermissions(read=True, write=True, delete=True, list=True, add=True, create=True, update=True, process=True, delete_previous_version=True)

    # Define the SAS token resource types (root)
    sas_resource_types=ResourceTypes(service=True, container=True, object=True)

    sas_token = generate_account_sas(
        account_name=account_name,
        account_key=account_key,
        resource_types=sas_resource_types,
        permission=sas_permissions,
        expiry=expiry_time,
        start=start_time
    )

    return sas_token


def get_blobs(blob_service_client: BlobServiceClient, container_name: str) -> list: 
    # list all filenames (blob.name) in a given container
    
    container_client = blob_service_client.get_container_client(container=container_name)
    blob_list = container_client.list_blobs()
    
    blob_lst=[]
    for blob in blob_list:
        blob_lst.append(blob.name)
    
    return blob_lst

def walk_blobs(blob_service_client: BlobServiceClient, container_name: str, folder_name: str) -> list: 
    # effectively the equivalent of list contents in a directory on a file system
    # list the names of all blobs in a given blob-directory
    
    container_client = blob_service_client.get_container_client(container=container_name)
    blob_list = container_client.walk_blobs(folder_name)
    
    blob_lst=[]
    for blob in blob_list:
        blob_lst.append(blob.name)
    
    return blob_lst




def convert_folder_csv_to_parquet_blob(blob_service_client: object, container_name_origin: str, container_name_destination: str, blob_folder_origin: str, blob_folder_destination: str, encoding: str):
    #blob version of disk version 
    
    print('blob client ', blob_service_client)
    print('origin container ',container_name_origin)
    print('destination container ',container_name_destination)
    print('origin folder ',blob_folder_origin)
    print('destination folder ', blob_folder_destination)
    print('encoding ',encoding)
  
    


    


### RUN ###

# Azure storage blob config (credentials)
load_dotenv()
account_name = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
account_key = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")

# create account SAS (should have root access to all containers)
sas_token = create_account_sas(account_name, account_key)

# build URL version in the proper format
account_sas_url = 'https://' + account_name+'.blob.core.windows.net/' + '?' + sas_token  
#print(account_sas_url)

# create BlobServiceClient object (we now have the power to do all the admin tasks)
blob_service_client = BlobServiceClient(account_url=account_sas_url)

# list blob containers (WORKING)
#containers = blob_service_client.list_containers(include_metadata=True)
#for container in containers:
#        print(container['name'])

# list all blobs in a given container (WORKING)
all_blobs_lst = get_blobs(blob_service_client, 'staging')

# list blobs in a given blob-directory (WORKING). Note can repurpose data_paths.
my_blobs_lst = walk_blobs(blob_service_client, 'staging', 'statistics/gapminder-fast-track/')


process_staging(blob_service_client, 'staging', 'copper')



"""

#build sas URL using existing token to a blob (i.e. first blob in list)
container_name_origin = 'staging'
sas_url_blob_origin = 'https://' + account_name+'.blob.core.windows.net/' + container_name_origin + '/' + my_blobs_lst[1] + '?' + sas_token          
print(sas_url_blob_origin)
df = pd.read_csv(sas_url_blob_origin)

# write to copper
container_name_destination = 'copper'

#trim filename .csv -> .parquet
blob_name = my_blobs_lst[1][:-3]+'parquet'

# build new blob sas URL
sas_url_blob_destination = 'https://' + account_name+'.blob.core.windows.net/' + container_name_destination + '/' + my_blobs_lst[1][:-3]+'parquet' + '?' + sas_token  
print(sas_url_blob_destination)

# write df to parquet stream (WORKING!!!)
stream = BytesIO() #initialise a stream
df.to_parquet(stream, engine='pyarrow') #write the parquet to the stream
stream.seek(0) #put pointer back to start of stream
blob_client = blob_service_client.get_blob_client(container=container_name_destination, blob="statistics/sample-blob.parquet")
blob_client.upload_blob(data=stream, overwrite=True, blob_type="BlockBlob")

# confirmed can write folder structure into blob

# TODO: start functionalising shit to churn through the statistics...basically get process_staging working completely. 1 step at a time.


"""












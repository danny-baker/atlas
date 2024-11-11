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




def process_staging(container_name_origin: str, container_name_destination: str):
    # process data from STAGING > COPPER 
    
    print('Process staging data ...')
    
    # PROCESS STATISTICAL DATA
    #coppersmith_gapminder_fast_track(container_name_origin, container_name_destination, paths.FASTTRACK_PATH_STAGING, 'latin-1')
    #coppersmith_gapminder_systema_globalis(container_name_origin, container_name_destination, paths.SYSTEMAGLOBALIS_PATH_STAGING,'latin-1')
    #coppersmith_gapminder_world_dev_indicators(container_name_origin, container_name_destination, paths.WDINDICATORS_PATH_STAGING, 'latin-1')
    #coppersmith_world_standards(container_name_origin, container_name_destination, paths.WS_PATH_STAGING, 'latin-1')
    #create_unique_country_list(container_name_origin, container_name_destination, paths.COUNTRY_LOOKUP_PATH_STAGING, 'utf-8')
    #coppersmith_bigmac(container_name_origin, container_name_destination, paths.BIG_MAC_PATH_STAGING, 'utf-8')    
    #coppersmith_sdgindicators(container_name_origin, container_name_destination, paths.SDG_PATH_STAGING, 'latin-1') 
    
    # PROCESS JSON (AND SPECIAL) DATA
    #coppersmith_map_json(container_name_origin, 'titanium')
    #coppersmith_globe_json(container_name_origin, 'titanium')
    #coppersmith_global_power_stations(container_name_origin, 'titanium', paths.PWR_STN_PATH_STAGING, paths.PWR_STN_PATH_TITANIUM, 'utf-8')    
    
    return



def create_unique_country_list(container_name_origin: str, container_name_destination: str, blob_path: str, encoding: str): 
    # Process country list (origin from UN?) to zero pad integers and store  (this is a single file that is important for later processing)  
    
    print('Processing metadata for country lookup')
    
    # build sas URL to the blob (so we can read it)
    sas_url_blob = 'https://' + account_name+'.blob.core.windows.net/' + container_name_origin + '/' + blob_path + '?' + sas_token 
    
    # read blob into df
    df = pd.read_csv(sas_url_blob, encoding=encoding, names=["m49_a3_country", "country", "continent", "region_un", "region_wb", "su_a3"])
    
    #cast to string
    df["m49_a3_country"] = df["m49_a3_country"].astype(str) 
    
    #pad the 3 digit m49 country integer with zeros if it less than 100 (i.e. "3" will become "003")
    df['m49_a3_country'] = df['m49_a3_country'].str.zfill(3)  
    
    # delete first row (column headings)
    df = df.iloc[1:,]
    
    # write df to csv stream
    stream = BytesIO() #initialise a stream
    df.to_csv(stream, index=False) #write the csv to the stream
    stream.seek(0) #put pointer back to start of stream
    
    # write the stream to blob
    blob_client = blob_service_client.get_blob_client(container=container_name_destination, blob=blob_path)
    blob_client.upload_blob(data=stream, overwrite=True, blob_type="BlockBlob")

    return

def coppersmith_gapminder_fast_track(container_name_origin: str, container_name_destination: str, blob_folder_origin: str, encoding: str):
    # origin
    # https://github.com/open-numbers/ddf--gapminder--fasttrack
    
    #recursively convert all csvs to parquet and dump them in a folder    
    tic = time.perf_counter()
    print("Processing gapminder fast track STAGING > COPPER")    
    convert_folder_csv_to_parquet_blob(container_name_origin, container_name_destination, blob_folder_origin, encoding)
    toc = time.perf_counter()
    print("Processing time: ",toc-tic," seconds")
    return


def coppersmith_gapminder_systema_globalis(container_name_origin: str, container_name_destination: str, blob_folder_origin: str, encoding: str):
    # origin
    # https://github.com/open-numbers/ddf--gapminder--systema_globalis
    
    #simply recursively convert all csvs to parquet and dump in a folder
    tic = time.perf_counter()
    print("Processing gapminder systema globalis STAGING > COPPER")    
    convert_folder_csv_to_parquet_blob(container_name_origin, container_name_destination, blob_folder_origin, encoding)
    toc = time.perf_counter()
    print("Processing time: ",toc-tic," seconds")
    return

def coppersmith_gapminder_world_dev_indicators(container_name_origin: str, container_name_destination: str, blob_folder_origin: str, encoding: str):
    # origin
    # https://github.com/open-numbers/ddf--open_numbers--world_development_indicators
    
    #simply recursively convert all csvs to parquet and dump them in an equivalent folder in COPPER (create if needed)
    tic = time.perf_counter()
    print("Processing gapminder world dev indicators STAGING > COPPER")    
    convert_folder_csv_to_parquet_blob(container_name_origin, container_name_destination, blob_folder_origin, encoding)
    toc = time.perf_counter()
    print("Processing time: ",toc-tic," seconds")
    return


def coppersmith_sdgindicators(container_name_origin: str, container_name_destination: str, blob_folder_origin: str, encoding: str):
    #simply recursively convert all xlsx files to parquet and dump them in an equivalent folder in COPPER (create if needed)
    tic = time.perf_counter()
    print("Processing sdg indicators STAGING > COPPER")   
    convert_folder_xlsx_to_parquet_blob(container_name_origin, container_name_destination, blob_folder_origin, encoding)
    toc = time.perf_counter()
    print("Processing time: ",toc-tic," seconds")
    return

"""
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
"""  
    


def coppersmith_map_json(container_name_origin: str, container_name_destination: str):
    #The map json (from memory) was unprocessed, sourced from Natural Earth
    # Move map json data from STAGING > TITANIUM
    # https://learn.microsoft.com/en-us/azure/storage/blobs/storage-blob-copy-python
    
    # Copy map json data blobs
    copy_blob(blob_service_client, container_name_origin, container_name_destination, paths.MAP_JSON_LOW_PATH_STAGING, paths.MAP_JSON_LOW_PATH_TITANIUM, sas_token)
    copy_blob(blob_service_client, container_name_origin, container_name_destination, paths.MAP_JSON_MED_PATH_STAGING, paths.MAP_JSON_MED_PATH_TITANIUM, sas_token)
    copy_blob(blob_service_client, container_name_origin, container_name_destination, paths.MAP_JSON_HIGH_PATH_STAGING, paths.MAP_JSON_HIGH_PATH_TITANIUM, sas_token)
        
    return

def copy_blob(blob_service_client, container_name_origin, container_name_destination, blob_origin, blob_destination, sas_token):
    # copy blob from one location to another
    print('Copying ', blob_origin, ' to ', blob_destination)

    # build sas URL to the blob (so we can read it)
    sas_url_blob = 'https://' + account_name+'.blob.core.windows.net/' + container_name_origin + '/' + blob_origin + '?' + sas_token 
    
    # copy the blob to target location
    target_blob = blob_service_client.get_blob_client(container_name_destination, blob_destination)
    target_blob.start_copy_from_url(sas_url_blob)

    
    return

def coppersmith_globe_json(container_name_origin: str, container_name_destination: str):
    # Attempt to process raw 3d json data for globe visualisation. FAIL.
    # This is really tricky, and some preprocessing was clearly done to prepare data for the cleaner functions. I never saved it.
    # In the interests of time, just storing processed data in staging to conform to the lakehouse architecture, if it ever needs to be processed.
    
    # Copy map json data blobs
    copy_blob(blob_service_client, container_name_origin, container_name_destination, paths.GLOBE_JSON_LAND_HIGH_PATH_STAGING, paths.GLOBE_JSON_LAND_HIGH_PATH_TITANIUM, sas_token)
    copy_blob(blob_service_client, container_name_origin, container_name_destination, paths.GLOBE_JSON_OCEAN_HIGH_PATH_STAGING, paths.GLOBE_JSON_OCEAN_HIGH_PATH_TITANIUM, sas_token)
    copy_blob(blob_service_client, container_name_origin, container_name_destination, paths.GLOBE_JSON_LAND_LOW_PATH_STAGING, paths.GLOBE_JSON_LAND_LOW_PATH_TITANIUM, sas_token)
    copy_blob(blob_service_client, container_name_origin, container_name_destination, paths.GLOBE_JSON_OCEAN_LOW_PATH_STAGING, paths.GLOBE_JSON_OCEAN_LOW_PATH_TITANIUM, sas_token)

    return

def coppersmith_global_power_stations(container_name_origin: str, container_name_destination: str, blob_path_origin: str, blob_path_destination: str, encoding: str):
    # process the experimental globe powerstation dataset csv to parquet directly from STAGING > TITANIUM
    
    tic = time.perf_counter()
    print("Processing global power station data STAGING > TITANIUIM (special)") 
    
    # build sas URL to the blob (so we can read it)
    sas_url_blob = 'https://' + account_name+'.blob.core.windows.net/' + container_name_origin + '/' + blob_path_origin + '?' + sas_token 
    
    # read blob into df
    df = pd.read_csv(sas_url_blob, encoding=encoding)
    
    # write df to csv stream
    stream = BytesIO() #initialise a stream
    df.to_parquet(stream, engine='pyarrow', index=False) #write the csv to the stream
    stream.seek(0) #put pointer back to start of stream
    
    # write the stream to blob
    blob_client = blob_service_client.get_blob_client(container=container_name_destination, blob=blob_path_destination)
    blob_client.upload_blob(data=stream, overwrite=True, blob_type="BlockBlob")
    
    toc = time.perf_counter()
    print("Processing time: ",toc-tic," seconds")
    return

def coppersmith_world_standards(container_name_origin: str, container_name_destination: str, blob_folder_origin: str, encoding: str):
    #simply recursively convert all csvs to parquet and dump them in an equivalent folder in COPPER (create if needed)
    tic = time.perf_counter()    
    print("Processing world standards STAGING > COPPER")    
    convert_folder_csv_to_parquet_blob(container_name_origin, container_name_destination, blob_folder_origin, encoding)
    toc = time.perf_counter()
    print("Processing time: ",toc-tic," seconds")
        
    return

def coppersmith_bigmac(container_name_origin: str, container_name_destination: str, blob_path: str, encoding: str):
    # https://github.com/TheEconomist/big-mac-data
    # https://github.com/theeconomist/big-mac-data/releases/tag/2024-01
    
    print('Processing BigMac index')
    
    # build sas URL to the blob (so we can read it)
    sas_url_blob = 'https://' + account_name+'.blob.core.windows.net/' + container_name_origin + '/' + blob_path + '?' + sas_token 
    
    # read blob into df
    df = pd.read_csv(sas_url_blob, encoding=encoding)
    
    # prepare destination blob path
    blob_path_destination = blob_path[:-3] + 'parquet'
    print(blob_path_destination)
    
    # write df to csv stream
    stream = BytesIO() #initialise a stream
    df.to_parquet(stream, engine='pyarrow', index=False) #write the csv to the stream
    stream.seek(0) #put pointer back to start of stream
    
    # write the stream to blob
    blob_client = blob_service_client.get_blob_client(container=container_name_destination, blob=blob_path_destination)
    blob_client.upload_blob(data=stream, overwrite=True, blob_type="BlockBlob")
    
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


def get_blobs(blob_service_client: object, container_name: str) -> list: 
    # list all filenames (blob.name) in a given container
    
    container_client = blob_service_client.get_container_client(container=container_name)
    blob_list = container_client.list_blobs()
    
    blob_lst=[]
    for blob in blob_list:
        blob_lst.append(blob.name)
    
    return blob_lst

def walk_blobs(blob_service_client: object, container_name: str, folder_name: str) -> list: 
    # effectively the equivalent of list contents in a directory on a file system
    # list the names of all blobs in a given blob-directory
    
    container_client = blob_service_client.get_container_client(container=container_name)
    blob_list = container_client.walk_blobs(folder_name)
    
    blob_lst=[]
    for blob in blob_list:
        blob_lst.append(blob.name)
    
    return blob_lst


def convert_folder_csv_to_parquet_blob(container_name_origin: str, container_name_destination: str, blob_folder_origin: str, encoding: str):
    # Transform a blob-folder of csvs in one container to parquet files in a target container
    
    # build list of blob names for this blob-folder
    blob_list = walk_blobs(blob_service_client, container_name_origin, blob_folder_origin)
    print('Converting ',len(blob_list),'files')
    
    # iterate the list read in each blob as df and write out to parquet stream to destination blob
    for blob in blob_list:
        print('Processing ', blob)
        
        # build sas URL to the blob (so we can read it)
        sas_url_blob = 'https://' + account_name+'.blob.core.windows.net/' + container_name_origin + '/' + blob + '?' + sas_token  
        #print(sas_url_blob)
        
        # read in blob as datafame     
        df = pd.read_csv(sas_url_blob, encoding=encoding)
        #print(df)
        
        # prepare destination blob path
        blob_path_destination = blob[:-3] + 'parquet'
        print(blob_path_destination)
        
        # write df to parquet stream
        stream = BytesIO() #initialise a stream
        df.to_parquet(stream, engine='pyarrow', index=False) #write the parquet to the stream
        stream.seek(0) #put pointer back to start of stream
        
        # write the stream to blob
        blob_client = blob_service_client.get_blob_client(container=container_name_destination, blob=blob_path_destination)
        blob_client.upload_blob(data=stream, overwrite=True, blob_type="BlockBlob")
    return

def convert_folder_xlsx_to_parquet_blob(container_name_origin: str, container_name_destination: str, blob_folder_origin: str, encoding: str):
    #Helper function to convert a whole folder of .xlsx files to .parquet with same names in the destination
    
    # build list of blob names for this blob-folder
    blob_list = walk_blobs(blob_service_client, container_name_origin, blob_folder_origin)
    print(len(blob_list))
    
    # iterate the list read in each blob as df and write out to parquet stream to destination blob
    for blob in blob_list:
        print('Processing ', blob)
        
        # build sas URL to the blob (so we can read it)
        sas_url_blob = 'https://' + account_name+'.blob.core.windows.net/' + container_name_origin + '/' + blob + '?' + sas_token  
        #print(sas_url_blob)
        
        # read in blob as datafame     
        df = pd.read_excel(sas_url_blob)
        
        # prepare destination blob path
        blob_path_destination = blob[:-4] + 'parquet'
        print(blob_path_destination)
        
        # write df to parquet stream
        stream = BytesIO() #initialise a stream
        df.to_parquet(stream, engine='pyarrow', index=False) #write the parquet to the stream
        stream.seek(0) #put pointer back to start of stream
        
        # write the stream to blob
        blob_client = blob_service_client.get_blob_client(container=container_name_destination, blob=blob_path_destination)
        blob_client.upload_blob(data=stream, overwrite=True, blob_type="BlockBlob")

    return
 

    
    



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

# create BlobServiceClient object (we now have the jedi power to do all the admin tasks)
blob_service_client = BlobServiceClient(account_url=account_sas_url)

# trigger the main operation
process_staging('staging', 'copper')


# TODO
# refactor and simplify. i.e don't need to pass blob_service_client as it should be global var
# clean up 
# harden: use try/catch statements in case of error. i.e. catch error and return false for function, so it can be rerun.
# try to catch errors at the file level (in the for loop) so can just repull the file rather than rerun the entire function (1000s of datafiles)#
# parallelise using laptop compute
# operationalise in cloud (custom VM) spin up with yaml, and run, spin down)











# Process data in COPPER > IRON

from dotenv import load_dotenv
import data_paths as paths
import json
import pandas as pd
#import numpy as np
import os
import sys
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


def process_copper(container_name_origin: str, container_name_destination: str):
    # process COPPER > IRON
    
    ironsmith_gapminder_fast_track('copper', paths.FASTTRACK_PATH_COPPER, paths.FASTTRACK_PATH_IRON)   #WORKING
    
    #ironsmith_gapminder_systema_globalis(paths.SYSTEMAGLOBALIS_PATH_COPPER, paths.SYSTEMAGLOBALIS_PATH_IRON)     
    #ironsmith_gapminder_world_dev_indicators(paths.WDINDICATORS_PATH_COPPER, paths.WDINDICATORS_PATH_IRON)   
    #ironsmith_sdgindicators(paths.SDG_PATH_COPPER, paths.SDG_PATH_IRON)
    #ironsmith_world_standards(paths.WS_PATH_COPPER, paths.WS_PATH_IRON)
    #ironsmith_bigmac(paths.BIG_MAC_PATH_COPPER, paths.BIG_MAC_PATH_IRON)
    return


def get_country_lookup_df(container_name: str, blob_path: str, encoding: str) -> pd.DataFrame():
    # read in country lookup csv file as df
    
    # build sas URL to the blob (so we can read it)
    sas_url_blob = 'https://' + account_name+'.blob.core.windows.net/' + container_name + '/' + blob_path + '?' + sas_token 
    
    # read blob into df
    df = pd.read_csv(sas_url_blob, encoding=encoding, names=["m49_a3_country", "country", "continent", "region_un", "region_wb", "su_a3"])
    
    return df


def walk_blobs(blob_service_client: object, container_name: str, folder_name: str) -> list: 
    # effectively the equivalent of list contents in a directory on a file system
    # list the names of all blobs in a given blob-directory
    
    container_client = blob_service_client.get_container_client(container=container_name)
    blob_list = container_client.walk_blobs(folder_name)
    
    blob_lst=[]
    for blob in blob_list:
        blob_lst.append(blob.name)
    
    return blob_lst


def ironsmith_gapminder_fast_track(container_name, origin_blob_folder, destination_blob_path):   
    # clean the copper version of these parquets (as was previously done) and place a single consolidated parquet in IRON
    # Goal of this function is to process each dataset into the master format and spit out a summary
    # 20x performance enhancement using pandas merge rather than FOR loop to set m49s etc.
    
    tic = time.perf_counter()
    print("Processing gapminder fast track COPPER > IRON")
    
    # read in unique country list from COPPER location
    countries = get_country_lookup_df('copper', paths.COUNTRY_LOOKUP_PATH_COPPER, 'utf-8')
    #print(countries)
    
    # read in metadata
    sas_url_blob = 'https://' + account_name+'.blob.core.windows.net/' + container_name + '/' + paths.FASTTRACK_META_COPPER + '?' + sas_token 
    lookup = pd.read_parquet(sas_url_blob).fillna("Not available")
    #print(lookup)
    
    # get file-blob list
    files = walk_blobs(blob_service_client, container_name, origin_blob_folder)
    
    #declare empty dataframe (which we'll append to)   
    pop = pd.DataFrame() 
    
    for file in files:
        if file == paths.FASTTRACK_META_COPPER: continue # skip metadata file
        
        print('Importing', file)
        
        # read file into df
        sas_url_blob = 'https://' + account_name+'.blob.core.windows.net/' + container_name + '/' + file + '?' + sas_token
        df = pd.read_parquet(sas_url_blob)
        
        # extract concept unique series id e.g. "mmr_who" (which can be queried from the concepts)
        concept = df.columns[2]
        
        # attempt to find series meta data in the concepts
        try:
            query = lookup[lookup['concept']==concept]            
        
        except KeyError as error:
            print("Exception thrown attempting to lookup ",concept)   
        
        # break if series not found in lookup
        if len(query) != 1:
            print("Query invalid, jumping to next file")
            continue                
        
        # break if no year ("time") is in the dataset (sometimes categoricals are like this)
        if "time" not in df.columns: continue #skip to next dataset
        
        # Add details from concept query              
        df['dataset_raw'] = query['name'].iloc[0]
        df['source'] = "Gapminder Fastrack Indicators." + " Updated " + query['updated'].iloc[0]
        df['link'] = query['source_url'].iloc[0]
        df['note'] =query['description'].iloc[0]               
        
        # Could add metadata if available such as format % etc. There is some good stuff in these which will help later.
        # NOTE FOR LATER
        
        #convert country codes to uppercase (and rename to match dataset lookup)
        df.columns.values[0] = 'su_a3'        
        df['su_a3'] = df['su_a3'].str.upper() #this is su_a3 e.g. AUD
        
        # add m49 integers and country name from the master country list
        df = df.merge(countries, on='su_a3', how='left')
        
        # reorganise cols and subset
        df = df.rename(columns={"time":"year", concept:'value', "m49_a3_country":"m49_un_a3"})
        df = df[['m49_un_a3', 'country', 'year', 'dataset_raw', 'value', 'continent','region_un', 'region_wb', 'source', 'link', 'note' ]]
        
        #strip out any non-country regions from the dataset, based on countries shortlist
        df = df[df['m49_un_a3'].isin(countries['m49_a3_country'])]   
        
        # append to pop dataframe
        pop = pd.concat([pop,df])
      
        
    # data typing 
    pop = pop.astype({'m49_un_a3': 'category', 
                    'country':'category', 
                    'year':'uint16', 
                    'dataset_raw':'category', 
                    'value':'str', 
                    'continent':'category',
                    'region_un':'category',
                    'region_wb':'category',
                    'source':'str',
                    'link':'str',
                    'note':'str',
                    })
     
    # write fast track dataset to parquet-blob
    # write df to stream
    stream = BytesIO() #initialise a stream
    pop.to_parquet(stream, engine='pyarrow', index=False) #write the csv to the stream
    stream.seek(0) #put pointer back to start of stream
    
    # write the stream to blob
    blob_client = blob_service_client.get_blob_client(container='iron', blob=destination_blob_path)
    blob_client.upload_blob(data=stream, overwrite=True, blob_type="BlockBlob")
     
    # summary
    toc = time.perf_counter()    
    print("Processed series: ",len(pd.unique(pop['dataset_raw']))," in ",(toc-tic)/60," minutes")
        
                
             
     
    
    
    
    
    """
    # set paths  
    destination_path = os.getcwd()+destination
    destination_filepath = os.getcwd()+destination+"gapminder_fast_track.parquet"
    origin_path = os.getcwd()+origin    
    metapath = origin_path+"ddf--concepts.parquet"
         
    # read in metatdata file (should be about 110 datasets)
    lookup = pd.read_parquet(metapath).fillna("Not available")   
    
    #declare empty dataframes    
    pop = pd.DataFrame()         
       
    # For each parquet, check if it's in the concepts (metadata) and if so, assemble to a dataframe chunk and append    
    for filepath in glob.iglob(origin_path+'*.parquet'):
        
        if filepath == metapath: continue
        
        print("Importing",filepath)
        
        # read in df
        df = pd.read_parquet(filepath)
        
        # extract concept unique series id e.g. "mmr_who" (which can be queried from the concepts)
        concept = df.columns[2]
        
        # attempt to find series meta data in the concepts
        try:
            query = lookup[lookup['concept']==concept]            
        
        except KeyError as error:
            print("Exception thrown attempting to lookup ",concept)   
        
        # break if series not found in lookup
        if len(query) != 1:
            print("Query invalid, jumping to next file")
            continue                
        
        # break if no year ("time") is in the dataset (sometimes categoricals are like this)
        if "time" not in df.columns: continue #skip to next dataset
        
        # Add details from concept query              
        df['dataset_raw'] = query['name'].iloc[0]
        df['source'] = "Gapminder Fastrack Indicators." + " Updated " + query['updated'].iloc[0]
        df['link'] = query['source_url'].iloc[0]
        df['note'] =query['description'].iloc[0]               
        
        # Could add metadata if available such as format % etc. There is some good stuff in these which will help later.
        # NOTE FOR LATER
        
        #convert country codes to uppercase (and rename to match dataset lookup)
        df.columns.values[0] = 'su_a3'        
        df['su_a3'] = df['su_a3'].str.upper() #this is su_a3 e.g. AUD
        #df = df.rename(columns={'country':'su_a3'})
        
        # add m49 integers and country name from the master country list
        df = df.merge(countries, on='su_a3', how='left')
        
        # reorganise cols and subset
        df = df.rename(columns={"time":"year", concept:'value', "m49_a3_country":"m49_un_a3"})
        df = df[['m49_un_a3', 'country', 'year', 'dataset_raw', 'value', 'continent','region_un', 'region_wb', 'source', 'link', 'note' ]]
        
        #strip out any non-country regions from the dataset, based on countries shortlist
        df = df[df['m49_un_a3'].isin(countries['m49_a3_country'])]   
        
        # append to clean pop dataframe
        pop = pd.concat([pop,df])
      
        
    # data typing 
    pop = pop.astype({'m49_un_a3': 'category', 
                    'country':'category', 
                    'year':'uint16', 
                    'dataset_raw':'category', 
                    'value':'str', 
                    'continent':'category',
                    'region_un':'category',
                    'region_wb':'category',
                    'source':'str',
                    'link':'str',
                    'note':'str',
                    })
    
    # write to parquet file
    if not os.path.exists(destination_path): os.mkdir(destination_path) 
    pop.to_parquet(destination_filepath, engine='pyarrow', index=False)    
    #pop.to_parquet(destination_filepath, engine='fastparquet', compression='gzip', index=False) #this didn't remove index either.
    
    # summary
    toc = time.perf_counter()    
    print("Processed series: ",len(pd.unique(pop['dataset_raw']))," in ",toc-tic," seconds")
    """
    
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
process_copper('copper', 'iron')

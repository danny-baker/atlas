# Process data in IRON > TITANIUM

from dotenv import load_dotenv
import data_paths as paths
import json
import pandas as pd
import os
import time
import datetime
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


def process_iron(container_name_origin: str, container_name_destination: str):
    # process data in IRON > TITANIUM
    
    smelt_iron(paths.IRON_STATS_PATH, paths.MASTER_META_PATH, paths.MASTER_STATS_PATH, container_name_origin, container_name_destination)
    update_config(paths.MASTER_META_PATH, paths.MASTER_CONFIG_PATH, 'titanium')
    return
    

def smelt_iron(origin_blob_folder: str, meta_file_path: str, stats_file_path: str, container_name_origin: str, container_name_destination: str):
        
    #smelt everything in iron statistics folder to produce master parquet and master meta in TITANIUM
    
    # obtain list of all standardised .parquet files recursively
    files = walk_blobs_recursive(blob_service_client, container_name_origin, origin_blob_folder)
    print('Smelting ',len(files), 'files...')
    print(files)
        
    # read all parquets as dataframe chunks into a list
    chunks=[]
    for file in files:
        sas_url_blob = 'https://' + account_name+'.blob.core.windows.net/' + container_name_origin + '/' + file + '?' + sas_token
        chunks.append(pd.read_parquet(sas_url_blob))
    
    # Concatenate df chunks into a master df
    master = pd.DataFrame()
    for df in chunks:        
        master = pd.concat([master,df])
            
    # Output summary
    series = len(pd.unique(master['dataset_raw']))
    observations = len(master.index)
    print("Master dataframe constructed in memory")
    print("Total series: ",series," Total observations: ",observations)    
       
    # Remove any series/year combinations where the count is less than 100 countries. i.e. we only want data with more than 100 country data points. Elliot's magic.
    print("Purging rows dataset-year combinations with less than 30 country datapoints...")
    master = master.groupby(['dataset_raw', 'year'], as_index=False).apply(lambda x: x if len(x) > 30 else pd.DataFrame())      
    print("Cleaned data. Series: ",len(pd.unique(master['dataset_raw']))," Total observations: ",len(master.index))
        
    # data typing
    master = master.astype({'m49_un_a3': 'category', 
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
    
    # Build meta data file from master stats
    meta = master.drop_duplicates(subset=['dataset_raw'])
    meta = meta.drop(columns=["m49_un_a3","country", "year", "value", "continent", "region_un", "region_wb" ])    
     
    # Write meta data to disk
    print("Writing metadata to blob")
    stream = BytesIO() #initialise a stream
    meta.to_parquet(stream, engine='pyarrow', index=False) #write the csv to the stream
    stream.seek(0) #put pointer back to start of stream
    
    # write the stream to blob
    blob_client = blob_service_client.get_blob_client(container=container_name_destination, blob=meta_file_path)
    blob_client.upload_blob(data=stream, overwrite=True, blob_type="BlockBlob")
    
    
    # Free up memory and purge master stats before writing to disk
    del chunks
    del meta
    del master['source']
    del master['link']
    del master['note']
    del master['region_un']
    del master['region_wb']
        
    # Write out master to file    
    print("Attempting to write master stats parquet to blob")
    #master.to_parquet(destination_filepath_stats, compression='brotli')  
    stream = BytesIO() #initialise a stream
    #master.to_parquet(stream, engine='pyarrow', compression='brotli', index=False) #write the csv to the stream
    master.to_parquet(stream, engine='pyarrow', index=False) #write the csv to the stream
    stream.seek(0) #put pointer back to start of stream
    
    # write the stream to blob
    blob_client = blob_service_client.get_blob_client(container=container_name_destination, blob=stats_file_path)
    blob_client.upload_blob(data=stream, overwrite=True, blob_type="BlockBlob")
        
    return  

def update_config(meta_blob_path, config_blob_path, container_name):
    # Update master_config file with any new data
    # Housekeeping like remove duplicate dataset_raws from config (no)
    # Update source, link, notes from meta for any dataset_raw (incase human fucked with it)    
    # Add (Concatenate) all datasets in meta_data that are not found in master_config
    # Sort file so anything without a dataset_label (i.e. unprocessed) is at the top
    # reset dataset_id index (numeric is fine) but this is critial for app loading and inputs etc.
    # write back to csv. No index.    
      
    print('Updating master config file ...')      
    
    # read master metadata into df
    sas_url_blob = 'https://' + account_name+'.blob.core.windows.net/' + container_name + '/' + meta_blob_path + '?' + sas_token
    meta = pd.read_parquet(sas_url_blob)
    print('Metadata read from blob. Length: ', len(meta))    
    
    # read master config into df
    sas_url_blob = 'https://' + account_name+'.blob.core.windows.net/' + container_name + '/' + config_blob_path + '?' + sas_token
    config = pd.read_csv(sas_url_blob)
    print('Config data read from blob. Length: ', len(config))
    
    # Housekeeping
    
    # Remove duplicate datasets from config
    #config = config.drop_duplicates(subset=['dataset_raw']) #pulled this to allow multiple placements in menu.
    
    # Identify series in config that are not in meta
    rem_series = pd.DataFrame()
    rem_series['dataset_raw'] = pd.unique(config['dataset_raw'])
    mask = ~rem_series['dataset_raw'].isin(pd.unique(meta['dataset_raw']))
    keep_series = rem_series[~mask]
    del_series = rem_series[mask]
    keep_series_list = keep_series['dataset_raw'].tolist()   
    
    # Add any special datasets to the list to keep (i.e. Global power station thingy)
    keep_series_list.append('Global power stations of the world')
    
    # Remove series in config that are not in meta
    config = config[config['dataset_raw'].isin(keep_series_list)]
    
    # Update source, link, notes from metadata (incase config has been fucked by human)
    config = config.drop(columns=['source', 'link', 'note'])
    
    # Merge in source, link, note from meta
    config = config.merge(meta, on='dataset_raw', how='left')
    
    # Identify new series (meta series not in config)
    new_series = pd.DataFrame()
    new_series['dataset_raw'] = pd.unique(meta['dataset_raw'])
    mask = new_series['dataset_raw'].isin(pd.unique(config['dataset_raw']))
    mask_invert = ~mask #insert boolean mask to identify missing data
    new_series = new_series[mask_invert]
    
    # Rebuild new dataset metadata ready for adding to config
    df = pd.DataFrame(columns = config.columns)
    df['dataset_raw'] = new_series['dataset_raw']
    df = df.drop(columns=['source', 'link', 'note'])
    df = df.merge(meta, on='dataset_raw', how='left')
    
    # Fill human required columns with helper text
    df['dataset_label'] = df['dataset_label'].fillna("TODO")
    df['var_type'] = df['var_type'].fillna("TODO")
    df['nav_cat'] = df['nav_cat'].fillna("TODO")
    df['colour'] = df['colour'].fillna("TODO")
    df['nav_cat_nest'] = df['nav_cat_nest'].fillna("TODO")
    
    # Append new datasets to config putting new stuff at the top
    config = pd.concat([df,config])
    
    # Reminder config used to have duplicated datasets for placeing in diff menu areas
    # If we want to display data in multiple areas (e.g. top 10 and SDG) then this must happen
    # But, think new standard should be to make them unique in config.
    
    # Reset dataset_id
    config['dataset_id'] = range(1, 1+len(config))
    
    # Update any NaN values that escaped parsing in notes.
    config['note'] = config['note'].fillna("Not available.")
    
    # Write config file to disk/blob
    stream = BytesIO() #initialise a stream
    config.to_csv(stream, index=False) #write the csv to the stream
    stream.seek(0) #put pointer back to start of stream 
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=config_blob_path)
    blob_client.upload_blob(data=stream, overwrite=True, blob_type="BlockBlob") # write the stream to blob
    
    #config.to_csv(filepath_config,index=False)
    
    print("Master config file successfully updated.")
   
    return


def walk_blobs(blob_service_client: object, container_name: str, folder_name: str) -> list: 
    # effectively the equivalent of list contents in a directory on a file system
    # list the names of all blobs in a given blob-directory
    
    container_client = blob_service_client.get_container_client(container=container_name)
    blob_list = container_client.walk_blobs(folder_name)
    
    blob_lst=[]
    for blob in blob_list:
        blob_lst.append(blob.name)
    
    return blob_lst

def walk_blobs_recursive(blob_service_client: object, container_name: str, folder_name: str) -> list: 
    # effectively the equivalent of list contents (and subfolders) in a directory on a file system
    # list the names of all blobs in a given blob-directory, including subdirectories
    # Note this needs refinement. It only goes 1 folder deep.
    
    container_client = blob_service_client.get_container_client(container=container_name)
    blob_list = container_client.walk_blobs(folder_name)
    
    blob_lst=[]
    for blob in blob_list:
        blob_lst.append(blob.name)
    
    # grab all blobs in each subdirectory
    files = []
    for folder in blob_lst:
        if folder[-1:] != '/': continue #skip if not folder
        files.append(walk_blobs(blob_service_client, container_name, folder))
    
    # this returns a list of lists, which we want to convert to a simple list of filenames
    files_clean = []
    for filelst in files:
        for f in range(0,len(filelst)):
            files_clean.append(filelst[f])
    
    return files_clean

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

# create BlobServiceClient object (we now have the jedi power to do all the admin tasks)
blob_service_client = BlobServiceClient(account_url=account_sas_url)

# trigger the main operation
process_iron('iron', 'titanium')
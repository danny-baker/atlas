# Houses all processing that can be done preruntime. In preparation for lakehouse build

# For now, if reprocessing is necessary this is done offline on a local machine using this file. (e.g. adding new datasets)
# run_lakehouse_tasks() to do a full pipeline build
# clean_lakehouse_for_build() to delete all uneeded files, zip up STAGING and leave TITANIUM files available for app
# Can then push repo to main and conform to the 100MB file size limit.

# This process must be run from the root repo directory. i.e. run python console and ensure in Spyder. Hit play button to parse Python and ensure back in the root project folder.


import data_paths as paths 
import json
import pandas as pd
import numpy as np
import glob
import os
import sys
import shutil
import time
import matplotlib.pyplot as plt
import copy
from py7zr import pack_7zarchive, unpack_7zarchive


# Azure storage blob config # (reminder to update yaml to fill these vals)
container_name = AZURE_STORAGE_ACCOUNT_CONTAINER_NAME #repository var
account_name = AZURE_STORAGE_ACCOUNT_NAME #repository var
account_key = AZURE_STORAGE_ACCOUNT_KEY #repository secret


# Virtually run lakehouse processing tasks 
def run_lakehouse_tasks():
    tic = time.perf_counter()
    process_STAGING()
    process_COPPER()
    process_IRON()  
    clean_lakehouse_for_build() #purge and zip, leaving TITANIUM (for run-time)
    #clean_lakehouse() #purge everything except STAGING (useful during pipeline testing)
    toc = time.perf_counter()
    print("Successfully ran data pipeline build. Operation time: ",(toc-tic)/60," minutes.")
    return

def process_STAGING():
    # process STAGING => COPPER
    decompress_staging()
    create_unique_country_list(paths.COUNTRY_LOOKUP_PATH_STAGING,paths.COUNTRY_LOOKUP_PATH_COPPER) #make this parquet?
    coppersmith_gapminder_fast_track(paths.FASTTRACK_PATH_STAGING, paths.FASTTRACK_PATH_COPPER, 'latin-1')
    coppersmith_gapminder_systema_globalis(paths.SYSTEMAGLOBALIS_PATH_STAGING, paths.SYSTEMAGLOBALIS_PATH_COPPER, 'latin-1')
    coppersmith_gapminder_world_dev_indicators(paths.WDINDICATORS_PATH_STAGING, paths.WDINDICATORS_PATH_COPPER, 'latin-1')
    #coppersmith_undata(paths.UNDATA_PATH_STAGING, paths.UNDATA_PATH_COPPER, 'latin-1')
    coppersmith_sdgindicators(paths.SDG_PATH_STAGING, paths.SDG_PATH_COPPER) #Slow due to excel reader
    #coppersmith_sdgindicators_new()
    coppersmith_map_json()
    coppersmith_globe_json()
    coppersmith_world_standards(paths.WS_PATH_STAGING, paths.WS_PATH_COPPER, 'latin-1')
    coppersmith_global_power_stations() #special data   
    coppersmith_bigmac(paths.BIG_MAC_PATH_STAGING, paths.BIG_MAC_PATH_COPPER)

    return

def process_COPPER():
    # process COPPER => IRON
    
    ironsmith_gapminder_fast_track(paths.FASTTRACK_PATH_COPPER, paths.FASTTRACK_PATH_IRON)   
    ironsmith_gapminder_systema_globalis(paths.SYSTEMAGLOBALIS_PATH_COPPER, paths.SYSTEMAGLOBALIS_PATH_IRON)      
    ironsmith_gapminder_world_dev_indicators(paths.WDINDICATORS_PATH_COPPER, paths.WDINDICATORS_PATH_IRON)   
    ironsmith_sdgindicators(paths.SDG_PATH_COPPER, paths.SDG_PATH_IRON)
    ironsmith_world_standards(paths.WS_PATH_COPPER, paths.WS_PATH_IRON)
    ironsmith_bigmac(paths.BIG_MAC_PATH_COPPER, paths.BIG_MAC_PATH_IRON)
    return

def process_IRON():
    # process IRON => TITANIUM
    smelt_iron(paths.IRON_STATS_PATH, paths.MASTER_META_PATH, paths.MASTER_STATS_PATH)
    update_config(paths.MASTER_META_PATH, paths.MASTER_CONFIG_PATH)
    return

def update_config(meta_path, config_path):
    # Update master_config file with any new data
    # Housekeeping like remove duplicate dataset_raws from config
    # Update source, link, notes from meta for any dataset_raw (incase human fucked with it)    
    # Add (Concatenate) all datasets in meta_data that are not found in master_config
    # Sort file so anything without a dataset_label (i.e. unprocessed) is at the top
    # reset dataset_id index (numeric is fine) but this is critial for app loading and inputs etc.
    # write back to csv. No index.    
      
    filepath_meta = os.getcwd()+meta_path
    filepath_config = os.getcwd()+config_path      
    
    meta = pd.read_parquet(filepath_meta)    
    config = pd.read_csv(filepath_config)
    
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
    
    # Write file to disk
    config.to_csv(filepath_config,index=False)
    
    print("Master config file successfully updated.")
   
    return


def clean_lakehouse():
    # helper function for full reset to test pipeline build from STAGING > TITANIUM    
    # needs hardening to pull all files or folders as a generic function. But works for now.
    
    # TITANIUM: purge everything except config csv.
    # IRON: purge
    # COPPER: purge
    # STAGING: no action.      
    
    #TITANIUM   
    
    #geojson
    folders = glob.glob(os.getcwd()+'/data_lakehouse/titanium/geojson/*')
    for f in folders: shutil.rmtree(f)   
    #meta
    try: os.remove(os.getcwd()+paths.MASTER_META_PATH)
    except: print("File not found. Skipping")    
    #stats
    try: os.remove(os.getcwd()+paths.MASTER_STATS_PATH)
    except: print("File not found. Skipping")
    
    #IRON
    
    #geojson
    folders = glob.glob(os.getcwd()+'/data_lakehouse/iron/geojson/*')
    for f in folders: shutil.rmtree(f)    
    #meta
    folders = glob.glob(os.getcwd()+'/data_lakehouse/iron/meta/*')
    for f in folders: shutil.rmtree(f)    
    #stats
    folders = glob.glob(os.getcwd()+'/data_lakehouse/iron/statistics/*')
    for f in folders: shutil.rmtree(f)
    
    #COPPER
    
    #geojson
    folders = glob.glob(os.getcwd()+'/data_lakehouse/copper/geojson/*')
    for f in folders: shutil.rmtree(f)    
    #meta
    files = glob.glob(os.getcwd()+'/data_lakehouse/copper/meta/*')
    for f in files: os.remove(f)        
    #stats
    folders = glob.glob(os.getcwd()+'/data_lakehouse/copper/statistics/*')
    for f in folders: shutil.rmtree(f)
        
    return

def clean_lakehouse_for_build():
    # Function to prepare the folder and files for production container build.
    # TITANIUM: no action
    # IRON: purge
    # COPPER: purge
    # STAGING: zip up. 7z
    
    print("Purging uneeded data.")     
    
    #IRON
    
    #geojson
    folders = glob.glob(os.getcwd()+'/data_lakehouse/iron/geojson/*')
    for f in folders: shutil.rmtree(f)    
    #meta
    folders = glob.glob(os.getcwd()+'/data_lakehouse/iron/meta/*')
    for f in folders: shutil.rmtree(f)    
    #stats
    folders = glob.glob(os.getcwd()+'/data_lakehouse/iron/statistics/*')
    for f in folders: shutil.rmtree(f)
    
    #COPPER
    
    #geojson
    folders = glob.glob(os.getcwd()+'/data_lakehouse/copper/geojson/*')
    for f in folders: shutil.rmtree(f)    
    #meta
    files = glob.glob(os.getcwd()+'/data_lakehouse/copper/meta/*')
    for f in files: os.remove(f)        
    #stats
    folders = glob.glob(os.getcwd()+'/data_lakehouse/copper/statistics/*')
    for f in folders: shutil.rmtree(f)
    
    print("Data purged. Attempting to zip STAGING folder")
    
    # STAGING
    
    #Zip up entire folder
    
    #testing to create multivolume archive (to get around github had filesize limit of 100MB)
    # sadly the volume_size argument is failing on latest version. So close :(
    #import multivolumefile
    #import py7zr
    #target = os.getcwd()+'/data_lakehouse/staging/'
    #with multivolumefile.open('example.7z', mode='wb', volume_size=50000) as target_archive:
    #    with SevenZipFile(target_archive, 'w') as archive:
    #        archive.writeall(target, 'target')
    # https://py7zr.readthedocs.io/en/latest/user_guide.html
    
    #trying other compression algorithms (also didn't get there)
    #my_filters = [{"id": py7zr.FILTER_ZSTD}]
    #my_filters = [{'id': py7zr.FILTER_BROTLI, "preset": 11}] #105MB took 20 mins on 600MB of csv
    #my_filters = [{"id": py7zr.FILTER_LZMA2, "preset": 9}] #106MB 3mins
    #my_filters = [{"id": py7zr.FILTER_ARM}, {"id": py7zr.FILTER_LZMA2, "preset": 7}] #106MB 3mins
    #with py7zr.SevenZipFile('staging_test.7z', 'w', filters=my_filters) as archive:
    #    archive.writeall('/home/dan/atlas/data_lakehouse/staging', 'base')

    
    # register 7zip helper (for using shutil to easily archive and extract)
    try:
        shutil.register_archive_format('7zip', pack_7zarchive, description='7zip archive')
        shutil.register_unpack_format('7zip', ['.7z'], unpack_7zarchive)  
    except: print("Shutil already registered")
    
    # compress folder
    #try:
    #    shutil.make_archive(os.getcwd()+'/data_lakehouse/staging', '7zip', os.getcwd()+'/data_lakehouse/staging/')
    #    shutil.rmtree(os.getcwd()+'/data_lakehouse/staging/')
    #    print("Successfully Zipped STAGING folder and removed decompressed data.")
    #except:
    #    print("Could not compress STAGING folder. Aborting delete")
    # 
    
    # Work around (100MB file size limit)

    # First compress each dataset folder in STAGING/statistics/ 
    folders = glob.glob(os.getcwd()+'/data_lakehouse/staging/statistics/*')
    for f in folders: 
        if f[-3:] == '.7z': continue #skip if not folder
        print("Archiving ",f)
        try:            
            shutil.make_archive(f, '7zip', f+'/')
            shutil.rmtree(f+'/')
            print("Successfully Zipped STAGING folder and removed decompressed data.")
        except:
            print("Could not compress STAGING folder. Aborting delete")
        
    # Next compress each folder in STAGING/ (skip STAGING/statistics)    
     
    folders = glob.glob(os.getcwd()+'/data_lakehouse/staging/*')
    for f in folders: 
        if f[-3:] == '.7z': continue #skip if not folder
        if f == os.getcwd()+'/data_lakehouse/staging/statistics': continue #skip if stats folder (as we don't want to zip this)
        
        print("Archiving ",f)
        try:            
            shutil.make_archive(f, '7zip', f+'/')
            shutil.rmtree(f+'/')
            print("Successfully Zipped STAGING folder and removed decompressed data.")
        except:
            print("Could not compress STAGING folder. Aborting delete")
  
       
    
    return

def decompress_staging():
    #Check if staging folder exists. If not, decompress.
    
    print("Decompressing STAGING folder in lakehouse")
    
    # register file format at first.
    try:
        shutil.register_archive_format('7zip', pack_7zarchive, description='7zip archive')
        shutil.register_unpack_format('7zip', ['.7z'], unpack_7zarchive)   
    except: print("Shutil already registered")
    
    # decompress each parent folder      
    
    # Extract archives in STAGING (meta, stats, geojson)
    files = glob.glob(os.getcwd()+'/data_lakehouse/staging/*')
    for f in files:    
        print("Extracting ",f)
        try:
            shutil.unpack_archive(f, f[:-3]+'/')
        except: print("Error. Folder may already exist. Skipping.")
    
    # Next extract all datasets in STAGING/statistics/        
    files = glob.glob(os.getcwd()+'/data_lakehouse/staging/statistics/*')
    for f in files:    
        print("Extracting ",f)
        try:
            shutil.unpack_archive(f, f[:-3]+'/')
        except: print("Error. Folder may already exist. Skipping.")
    
    
    return


def list_parquet_files(dir):
    r = []
    for root, dirs, files in os.walk(dir):
        for name in files:
            filepath = root + os.sep + name
            if filepath.endswith(".parquet"):
                r.append(os.path.join(root, name))
    return r

def smelt_iron(origin, meta_path, stats_path):
        
    #smelt everything in iron statistics folder to produce master parquet and master meta in TITANIUM
           
    origin_path = os.getcwd()+origin
    destination_filepath_meta = os.getcwd()+meta_path
    destination_filepath_stats = os.getcwd()+stats_path
    
    # obtain list of all .parquet files recursively
    files = list_parquet_files(origin_path) 
    
    # read all parquets as dataframe chunks into a list
    chunks=[]
    for file in files:
        chunks.append(pd.read_parquet(file))
    
    # Concatenate df chunks into a master df
    master = pd.DataFrame()
    for df in chunks:        
        master = pd.concat([master,df])
            
    # Output summary
    series = len(pd.unique(master['dataset_raw']))
    observations = len(master.index)
    print("Master dataframe constructed in memory")
    print("Total series: ",series," Total observations: ",observations)
    
    # Housekeeping
    
    '''
    #testing
    path=os.getcwd()+"/data_lakehouse/titanium/statistics/master_stats.parquet" 
    df = pd.read_parquet(path)            
    
    # take a look at data grouping by dataset and year, counting rows essentially
    t = df.groupby(["dataset_raw", "year"], as_index=False)["country"].count()
    t = t.sort_values(by=['dataset_raw', 'year'])
    t = t[t['country'] != 0] #some datasets have years that go right back to 600bc, so the groupby preduces shit tones of rows with 0 counts.
       
    # Summary stats on dataset-year combinations, counting country data points.     
    dist = t['country'].to_numpy()
    median = np.median(dist) #131
    average = np.mean(dist) #127
    max = np.max(dist)
    less_than_50_countries = (dist < 50).sum()
    less_than_100_countries = (dist < 100).sum() 
    '''
        
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
    print("Writing metadata to disk")
    meta.to_parquet(destination_filepath_meta)
    
    # Free up memory and purge master stats before writing to disk
    del chunks
    del meta
    del master['source']
    del master['link']
    del master['note']
    del master['region_un']
    del master['region_wb']
        
    # Write out master to file    
    print("Attempting to write master stats parquet to disk")
    master.to_parquet(destination_filepath_stats, compression='brotli')  

    return  


def migrate_master_meta():
    #helper function to build new master meta file to succeed dataset_lookup.csv
    # This is no longer used in the pipeline and was part of the transition. Keeping as a ref.
    
    path_origin = os.getcwd()+"/data_lakehouse/snapshot/meta/dataset_lookup.csv"
    path_destination = os.getcwd()+"/data_lakehouse/titanium/meta/master_config.csv"
    
    #read in dataset_lookup    
    df= pd.read_csv(
       path_origin,
       encoding="utf-8",
       names=["dataset_id", "dataset_raw", "dataset_label", "source", "link", "var_type", "nav_cat", "colour", "nav_cat_nest", "tag1", "tag2", "explanatory_note"],
    )    
        
    # delete first 1 rows (col headers)
    df = df.iloc[1:,]    
    
    # write to new csv location
    df.to_csv(path_destination,index=False)
   
    # read in new file to begin hacking it
    master_config = pd.read_csv(path_destination)    
       
    # transform df into dictionary of dictionaries
     
    # convert df to list of dicts as records 
    dict_list = master_config.to_dict('records')
    
    # now build a new dict setting keys to what we want (at this stage 'dataset_raw' as this is how we look shit up)
    config_dict = {}
    for i in range(len(dict_list)):        
        
        # set key and values from this item on the list of dicts
        key = dict_list[i].get("dataset_raw") #set dataset_raw as key for parent dictionary
        value = dict_list[i] #value is the whole dictionary
        
        # insert item to dictionary (if duplicate dataset_raw in csv, it will only add 1, so this kind of filters crud)
        config_dict[key]=value
    
    # a few quick tests
    series = "Internet users per 100 inhabitants"
    result = config_dict[query]
    item = result.get("explanatory_note")  
    

    return
   

def coppersmith_gapminder_fast_track(origin, destination, encoding):
    # origin
    # https://github.com/open-numbers/ddf--gapminder--fasttrack
    
    #simply recursively convert all csvs to parquet and dump them in an equivalent folder in COPPER (create if needed)      
    tic = time.perf_counter()
    print("Processing gapminder fast track STAGING > COPPER")    
    convert_folder_csv_to_parquet(origin, destination, encoding)
    toc = time.perf_counter()
    print("Processing time: ",toc-tic," seconds")
    return

def coppersmith_gapminder_systema_globalis(origin, destination, encoding):
    # origin
    # https://github.com/open-numbers/ddf--gapminder--systema_globalis
    
    #simply recursively convert all csvs to parquet and dump them in an equivalent folder in COPPER (create if needed)
    tic = time.perf_counter()
    print("Processing gapminder systema globalis STAGING > COPPER")    
    convert_folder_csv_to_parquet(origin, destination, encoding)
    toc = time.perf_counter()
    print("Processing time: ",toc-tic," seconds")
    return

def coppersmith_gapminder_world_dev_indicators(origin, destination, encoding):
    # origin
    # https://github.com/open-numbers/ddf--open_numbers--world_development_indicators
    
    #simply recursively convert all csvs to parquet and dump them in an equivalent folder in COPPER (create if needed)
    tic = time.perf_counter()
    print("Processing gapminder world dev indicators STAGING > COPPER")    
    convert_folder_csv_to_parquet(origin, destination, encoding)
    toc = time.perf_counter()
    print("Processing time: ",toc-tic," seconds")
    return

def coppersmith_undata(origin, destination, encoding):
    #simply recursively convert all csvs to parquet and dump them in an equivalent folder in COPPER (create if needed)
    tic = time.perf_counter()
    print("Processing gapminder UN data indicators STAGING > COPPER")
    convert_folder_csv_to_parquet(origin, destination, encoding)    
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
    convert_folder_csv_to_parquet(origin, destination, encoding)
    
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
    convert_folder_csv_to_parquet(origin, destination, encoding)
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


def ironsmith_gapminder_fast_track(origin, destination):   
    # clean the copper version of these parquets (as was previously done) and place a single consolidated parquet in IRON
    # Goal of this function is to process each dataset into the master format and spit out a summary
    # 20x performance enhancement using pandas merge rather than FOR loop to set m49s etc.
    
    tic = time.perf_counter()
    print("Processing gapminder fast track COPPER > IRON")
    
    # read in unique country list from COPPER location
    countries = get_unique_country_list()

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
    
    return


def ironsmith_gapminder_systema_globalis(origin, destination):
    # clean the copper version of these parquets (as was previously done) and place a single consolidated parquet in IRON
    # Goal of this function is to process each dataset into the master format and spit out a summary
    
    tic = time.perf_counter()
    print("Processing gapminder systema globalis COPPER > IRON")
    
    # read in unique country list from COPPER location
    countries = get_unique_country_list()      
    
    # set paths  
    destination_path = os.getcwd()+destination
    destination_filepath = destination_path+"gapminder_systema_globalis.parquet"
    origin_path = os.getcwd()+origin    
    metapath = origin_path+"ddf--concepts.parquet"

     
    # read in metatdata file (should be about 500 datasets)
    lookup = pd.read_parquet(metapath).fillna("Not available")   
     
    #declare empty dataframes    
    pop = pd.DataFrame()       
        
    for filepath in glob.iglob(origin_path+'*.parquet'):
        
        if filepath == metapath: continue #skip
        
        print("Importing",filepath)
        
        # read in df
        df = pd.read_parquet(filepath)
        
        # extract id
        concept = df.columns[2]        
        
        # attempt to find details in lookup
        try:
            query = lookup[lookup['concept']==concept]            
        
        except KeyError as error:
            print("Exception thrown attempting to lookup ",concept)   
        
        # break if series not found in lookup
        if len(query) != 1:
            print("Query invalid, jumping to next file")
            continue                
        
        # break if no year ("time") is in the dataset (sometimes categoricals are like this)
        if "time" not in df.columns: continue #skip dataset
        
        # at this point we are good and ready to start building the pop structure               
        df['dataset_raw'] = query['name'].iloc[0]
        #query['description'] = query['description'].fillna('')  #warning here
        query = query.fillna('') #for description sometimes being empty
        df['source'] = "Gapminder Systema Globalis Indicators."
        df['link'] = query['source_url'].iloc[0]
        
        # add explanatory notes
        if query['description_long'].iloc[0] != None: df['note'] = query['description'].iloc[0] + " " + query['description_long'].iloc[0]
        else: df['note'] = query['description'].iloc[0] 
                
        #convert country codes to uppercase (and rename to match dataset lookup)
        df['geo'] = df['geo'].str.upper() #this is su_a3 e.g. AUD
        df = df.rename(columns={'geo':'su_a3'})
        
        # add m49 integers and country name from the master country list
        df = df.merge(countries, on='su_a3', how='left')

        # reorganise cols and subset
        df = df.rename(columns={"time":"year", concept:'value', "country":"country", "m49_a3_country":"m49_un_a3"})
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
    pop.to_parquet(destination_filepath)
    
    # summary
    toc = time.perf_counter()    
    print("Processed series: ",len(pd.unique(pop['dataset_raw']))," in ",toc-tic," seconds")
    
    return


def ironsmith_gapminder_world_dev_indicators(origin, destination): 
    # clean the copper version of these parquets (as was previously done) and place a single consolidated parquet in IRON
    # Goal of this function is to process each dataset into the master format and spit out a summary
    
    tic = time.perf_counter()   
    print("Processing world development indicators COPPER > IRON")
    
    # read in unique country list from COPPER location
    countries = get_unique_country_list()
   
    # set paths  
    destination_path = os.getcwd()+destination
    destination_filepath = destination_path+"world_development_indicators.parquet"
    origin_path = os.getcwd()+origin    
    metapath1 = origin_path+"ddf--concepts--continuous.parquet"
    metapath2 = origin_path+"ddf--concepts--discrete.parquet" #checked this. It's all crud. keeping here so it can be skipped
       
    # read in metatdata file (about 1400 datasets)
    lookup = pd.read_parquet(metapath1) 
    
    #declare empty dataframe   
    pop = pd.DataFrame()
    
    #Metrics    
    files=len(glob.glob(os.getcwd()+"/data_lakehouse/copper/statistics/world-development-indicators/*"))    
    runcount=0    
    batch_size=500
    batch_counter=0
    filewritecount=1
    
    for filepath in glob.iglob(origin_path+'*.parquet'):
        
        runcount = runcount +1
        batch_counter = batch_counter+1
        
        # Check for batching first, before any breaks occur
        #batch save files (mem management) every 500
        if batch_counter == batch_size:
            
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
            
            # clean out any commas from string numbers (known issue) Presume to do with parsing "12,300" > "12300"
            pop["value"] = pop["value"].str.replace(",","")
            
            # write to parquet file                       
            if not os.path.exists(destination_path): os.mkdir(destination_path) 
            print("Writing batch file ",destination_filepath)
            pop.to_parquet((destination_filepath[:-8])+str(filewritecount)+".parquet"  )
            
            # batch run logic
            filewritecount = filewritecount + 1            
            batch_counter = 0 #reset
            
            # Empty dataframe rapidly
            pop.drop(pop.columns, inplace=True, axis=1)    
            pop = pop.iloc[0:0]
            
        # Continue normal parse
        # in future should scan for filename pattern "ddf-concepts" and "ddf-entities" etc and ignore. This works though.
        if filepath == metapath1: continue
        if filepath == metapath2: continue
        
        print("Importing",runcount,"/",files," ",filepath)       
        
        # read in df
        df = pd.read_parquet(filepath)
        
        # extract id
        concept = df.columns[2]      
        
        # attempt to find details in lookup
        try:
            query = lookup[lookup['concept']==concept].fillna('')            
        
        except KeyError as error:
            print("Exception thrown attempting to lookup ",concept)   
        
        # break if series not found in lookup
        if len(query) != 1:
            print("Query invalid, jumping to next file")
            continue                
        
        # break if no year ("time") is in the dataset (sometimes categoricals are like this)
        if "time" not in df.columns: continue #skip dataset
        
        # Add in metadata from query            
        df['dataset_raw'] = query['name'].iloc[0]          
        df['source'] = "World Bank - World Development Indicators." + " Series code: " + query['series_code'].iloc[0]
        df['link'] = "https://github.com/open-numbers/ddf--open_numbers--world_development_indicators"                     
        df['note'] = query['development_relevance'].iloc[0] + " " + query['long_definition'].iloc[0] + " " + query['statistical_concept_and_methodology'].iloc[0] + " " + query['general_comments'].iloc[0] + " " + query['limitations_and_exceptions'].iloc[0]
        
        # strip out new lines \n
        df['note'] = df['note'].str.replace(r'\\n', '', regex=True)        
               
        #convert country codes to uppercase (to match datasetlookup)
        try:
            df['geo'] = df['geo'].str.upper() #this is su_a3 e.g. AUD
        
        except KeyError as error:
            print("Exception thrown attempting to lookup Geo. Likely a global dataset only. Skipping")
            continue    
        
        
        # Rename cols so far
        df = df.rename(columns={"time":"year", concept:'value', 'geo':'su_a3'})
        
        # Merge in metadata from unique country list
        df = df.merge(countries, on='su_a3', how='left')
        
        # Rename new cols
        df = df.rename(columns={"m49_a3_country":"m49_un_a3", 'geo':'su_a3'})
        
        # reorganise cols and subset        
        df = df[['m49_un_a3', 'country', 'year', 'dataset_raw', 'value', 'continent','region_un', 'region_wb', 'source', 'link', 'note' ]]
        
        #strip out any non-country regions from the dataset, based on countries shortlist
        df = df[df['m49_un_a3'].isin(countries['m49_a3_country'])]  
        
        # append to clean pop dataframe
        pop = pd.concat([pop,df])       
       
    # BREAK FOR LOOP
    
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
    
    # clean out any commas from string numbers (known issue) Presume to do with parsing "12,300" > "12300"
    pop["value"] = pop["value"].str.replace(",","")
    
    # write to (final) parquet file
    if not os.path.exists(destination_path): os.mkdir(destination_path)   
    pop.to_parquet(pop.to_parquet((destination_filepath[:-8])+str(filewritecount)+".parquet"  )) 
    
    # summary
    toc = time.perf_counter()    
    print("Processed series: ",len(pd.unique(pop['dataset_raw']))," in ",toc-tic," seconds")
    
    return 


def ironsmith_undata(origin, destination):
    # clean the copper version of these parquets (as was previously done) and place a single consolidated parquet in IRON
    # Goal of this function is to process each dataset into the master format and spit out a summary
    # this data has metadata embedded in each dataset, so less complex to parse than gapminder stuff
    # this parser will have to be improved to handle different no.s of columns. It's not hardened. Some variation exists in their datasets.    

    tic = time.perf_counter()      
    print("Processing UN data COPPER > IRON")
    
    # read in unique country list from COPPER location
    countries = get_unique_country_list()
    
    destination_path = os.getcwd()+destination
    destination_filepath = destination_path+"undata.parquet"
    origin_path = os.getcwd()+origin
    
    #declare empty dataframe which we'll add chunks to   
    pop = pd.DataFrame() 
        
    for filepath in glob.iglob(origin_path+'*.parquet'):
                        
        print("Importing",filepath)
                
        df = pd.read_parquet(filepath)
          
        if len(df.columns) == 9: 
            # if have 9 columns, drop at index 4 and 5 (manually checked)
            df = df.drop(df.columns[[4, 5]], axis=1)
            
        
        if len(df.columns) != 7: continue #break if we don't have 7 cols
                
        # rename columns
        df.columns=["m49_a3_country", "country", "year", "dataset_raw", "value", "note", "source"]
        
        # drop country, as we'll use the standardised ones and merge in later
        df = df.drop(columns=['country'])
        
        #add column for Link (THIS IS MANUAL ADDITION)
        df["link"] = "https://data.un.org/"
        
        #pad the 3 digit m49 country integer with zeros if it less than 100 (i.e. "3" will become "003")
        df['m49_a3_country'] = df['m49_a3_country'].str.zfill(3)  
        
        #merge in m49 integers and region metadata     
        df = df.merge(countries, on='m49_a3_country', how='left')

        #  subset and reorder cols        
        df = df[['m49_a3_country', 'country', 'year', 'dataset_raw', 'value', 'continent','region_un', 'region_wb', 'source', 'link', 'note' ]]
        
        # rename where necessary
        df = df.rename(columns={"m49_a3_country":"m49_un_a3"})
        
        # delete first 2 rows (as this often has crud meta in it)
        df = df.iloc[2:,]
        
        #remove any commas from the value common before casting it (can't remember why)
        df["value"] = df["value"].str.replace(',','')
        
        #strip out any non-country regions from the dataset, based on countries shortlist
        df = df[df['m49_un_a3'].isin(countries['m49_a3_country'])]        
        
        #Fill any NaN values in notes with text
        df['note'] = df['note'].fillna("Not available.")
        
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
    pop.to_parquet(destination_filepath)
    
    # summary
    toc = time.perf_counter()    
    print("Processed series: ",len(pd.unique(pop['dataset_raw']))," in ",toc-tic," seconds")

    return


def ironsmith_sdgindicators(origin, destination):
    # clean the copper version of these parquets (as was previously done) and place a single consolidated parquet in IRON
    # Goal of this function is to process each dataset into the master format and spit out a summary
    # this data has metadata embedded in each dataset, so less complex to parse than gapminder stuff    
    
    tic = time.perf_counter()  
    print("Processing SDG indicator data COPPER > IRON")
    
    # read in unique country list from COPPER location
    countries = get_unique_country_list()
    
    destination_path = os.getcwd()+destination
    destination_filepath = destination_path+"sdgindicators.parquet"
    origin_path = os.getcwd()+origin
    
    #declare empty dataframe    
    pop = pd.DataFrame() 
           
    for filepath in glob.iglob(origin_path+'*.parquet'):
        #dataframe_collection[filepath] = pd.read_parquet(filepath)

        print("Loading data: ", filepath)    
        
        df = pd.read_parquet(filepath)   
                
        # concatenate the goal/target/indicator to source
        df['curatedSrc'] = 'United Nations Sustainable Development Goals (SDG) Indicators Database. '
        df['goalid']=' Goal '
        df['targetid']=' Target '
        df['indicatorid']=' Indicator '
        df['seriesid']=' Series ID: '   
        df['newSource'] = df['curatedSrc'] + df['Source'] + df['goalid'] + df['Goal'].astype(str) + df['targetid'].astype(str) + df['Target'].astype(str) + df['indicatorid'] + df['Indicator'] + df['seriesid'] + df['SeriesCode'] 
        
        #drop unneeded columns
        df = df.drop(columns=['goalid','targetid','indicatorid','seriesid','Source','Goal','Target','Indicator','SeriesCode'])
        
        #add column for Link (THIS IS MANUAL ADDITION)
        df['Link'] = "https://unstats.un.org/sdgs/dataportal"
        
        #Note for meta. Units is available. eg PERCENT
        #CLAIMER FOR LATER
        
        # subset cols
        df = df[["GeoAreaCode", "TimePeriod", "SeriesDescription", "Value", "newSource" , "Link", "FootNote"]]
        
        # rename cols
        df = df.rename(columns={"GeoAreaCode":'m49_a3_country', "TimePeriod":'Year', "SeriesDescription":'Series', "FootNote":'Note', "newSource":"Source"})
                
        #pad the 3 digit m49 country integer with zeros if it less than 100 (i.e. "3" will become "003")    
        df['m49_a3_country'] = df['m49_a3_country'].astype(str).str.zfill(3) 
        
        #merge in additional region info and country name (for consistency)
        df = df.merge(countries, on='m49_a3_country', how='left')

        #  subset and reorder cols        
        df = df[['m49_a3_country', 'country', 'Year', 'Series', 'Value', 'continent','region_un', 'region_wb', 'Source', 'Link', 'Note' ]]
        
        # rename where necessary
        df = df.rename(columns={"m49_a3_country":"m49_un_a3"})
                
        #strip out any non-country regions from the dataset, based on countries shortlist
        df = df[df['m49_un_a3'].isin(countries['m49_a3_country'])]   
        
        #drop any rows with nan value
        df = df.dropna(subset=['Value'])       
          
        # rename cols to new standard
        df = df.rename(columns={"m49_a3_country":"m49_un_a3", "Year":"year", "Series":"dataset_raw", "Value":"value", "Source":"source", "Link":"link", "Note":"note" })
        
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
    pop.to_parquet(destination_filepath)
    
    # summary
    toc = time.perf_counter()    
    print("Processed series: ",len(pd.unique(pop['dataset_raw']))," in ",toc-tic," seconds")
    
    return 


def ironsmith_sdgindicators_new():
    # Parse new sdg indicators and do lots of cleaning to get to 1 year per region for each series
    
    origin_filepath = os.getcwd()+'/data_lakehouse/copper/statistics/sdgindicators_new/sdgindicators_new.parquet'
    destination = os.getcwd()+'/data_lakehouse/iron/statistics/sdgindicators_new/'
    destination_filepath = destination+'sdgindicators_new.parquet'
    
    # read in unique country list from COPPER location
    countries = get_unique_country_list()   
    
    # read in raw parquet
    df = pd.read_parquet(origin_filepath)
    
    # First drop all rows with non regions (i.e. world and multi country amalgamates)
    df = df.astype({'GeoAreaCode': 'str'})
    df['GeoAreaCode'] = df['GeoAreaCode'].str.zfill(3)     
    df = df[df['GeoAreaCode'].isin(countries['m49_a3_country'])]   
    
    # how many series to parse?
    indicators = len(pd.unique(df['Indicator']))
    series = len(pd.unique(df['SeriesDescription']))
    
    series_with_dups = 0
    series_without_dups = 0
    
    # Goal is to have a generic parser that ends up with no duplicate years for a given dataset and region
    for series in pd.unique(df['SeriesDescription']):
        #print(series)
        
        #subset to just that series
        s = df[df['SeriesDescription']==series]
        
        # Check for variations
        var_location = len(pd.unique(s['Location']))
        var_age = len(pd.unique(s['Age']))
        var_sex = len(pd.unique(s['Sex']))
        
        #tally countries with multiple years 
        d = s.groupby(['GeoAreaName','TimePeriod']).count()
        d = d[d['Value']!=0] #drop zero counts
        d = d[d['Value']>1] #identify more than 1 year found        
        
        if len(d) == 0: series_without_dups += 1
        else: series_with_dups += 1
        
        print('obs:',len(s),' dups:',len(d), ' location:', var_location, ' age:',var_age,' sex:',var_sex,' in ',series)
     
    
    print("Series with dupes: ",series_with_dups)
    print("Series without dupes: ",series_without_dups)
    
    # First, lets try to visualise present state
    t = df.groupby(['SeriesDescription', 'GeoAreaName','TimePeriod']).count()
    t = t[t['Value']!=0]
    t = t[t['Value']>1] #goal is to get this to 0 in size
    dups_before = len(t)
    
    # Loop through each series and check for duplicates
    #for series in pd.unique(df[''])
    
    #testing
    blah = df[df['SeriesDescription']=='Number of fixed broadband subscriptions, by speed (number)']
    
    return


def ironsmith_world_standards(origin, destination):
    #Parse csvs here.
    #CV format scraped manually from website.
    #CSV format: Country, Year, Series, Value, Note, Source, Link (add link manually)
    #country format: m49_a3_country, country, continent, region_un, region_wb, SU_A3 
    
    country_tweaks = {
        'Bolivia' : 'Bolivia (Plurin. State of)',
        'Bonaire' : 'Bonaire, St. Eustatius & Saba',
        'Brunei' : 'Brunei Darussalam',
        'Burma (officially Myanmar)' : 'Myanmar', #not working properly. Despite being fine if I run this script line by line
        'China, Peoples Republic of' : 'China',
        'Congo, Democratic Republic of the (Congo-Kinshasa)' : 'Dem. Rep. of the Congo',
        'Congo, Republic of the (Congo-Brazzaville)': 'Congo',
        'Curaaso' : 'Curaçao',
        'Czechia (Czech Republic)' : 'Czechia',
        'Côte dIvoire (Ivory Coast)': 'Côte dIvoire', #384 (ivory coast)
         #'East Timor (Timor-Leste)' : 
        'United Kingdom (UK)': 'United Kingdom',
        'Falkland Islands': 'Falkland Islands (Malvinas)',
        'Gabon (Gabonese Republic)': 'Gabon',
         #'Guadeloupe (French overseas department)': 
         #'Guernsey': 
        'Holland (officially the Netherlands)': 'Netherlands',
        'Hong Kong': 'China, Hong Kong SAR',
        'Iran': 'Iran (Islamic Republic of)',
        'Ireland (Eire)': 'Ireland',
         #'Jersey'
        'Korea, South': 'Republic of Korea',
        'Laos': "Lao People's Dem. Rep.",
        'Micronesia (officially: Federated States of Micronesia)': 'Micronesia (Fed. States of)',
        'Moldova': 'Republic of Moldova',
        'New Caledonia (French overseas collectivity)': 'New Caledonia',
        'Myanmar (formerly Burma)': 'Myanmar',
         #'Somaliland (unrecognised, self-declared state)': 'Somalia', #706
         #'North Korea'
        'Palestine': 'State of Palestine',
        'Russia (officially the Russian Federation)': 'Russian Federation', #643 Not working properly
        'Syria': 'Syrian Arab Republic',
        'Suriname (Surinam)': 'Suriname', #740
        'Tanzania': 'United Rep. of Tanzania',
        'United Arab Emirates (UAE)': 'United Arab Emirates',
        'United States of America (USA)': 'United States of America',
        'Venezuela': 'Venezuela (Boliv. Rep. of)',
        'Vietnam': 'Viet Nam',
       
        }
    
      
    #testing
    #origin = "/data_lakehouse/copper/statistics/world-standards-unofficial-website/"
    #destination = "/data_lakehouse/iron/statistics/world-standards-unofficial-website/"
    #iron = pd.read_parquet("/home/dan/atlas/data_lakehouse/iron/statistics/world-standards-unofficial-website/world-standards.parquet")
    #copper = pd.read_parquet("/home/dan/atlas/data_lakehouse/copper/statistics/world-standards-unofficial-website/driving_side2.parquet")
    
    tic = time.perf_counter()
    
    origin_path = os.getcwd()+origin
    destination_path = os.getcwd()+destination
    destination_filepath = destination_path+"world-standards.parquet"
    
    # read in unique country list from COPPER location
    countries = get_unique_country_list()
    
    #declare empty dataframe    
    pop = pd.DataFrame() 
           
    for filepath in glob.iglob(origin_path+'*.parquet'):
        
        print("Loading data: ", filepath)    
        
        # Read file from copper
        df = pd.read_parquet(filepath)
        
        # For this data, we must merge UN data on country name (problematic). First do some custom substitutions.
        df = df.replace({"country":country_tweaks})  
        
        #merge in additional info such as m49 integer identifier
        df = df.merge(countries, how='left', on='country')
        
        # reconfigure dataframe to conform to iron standard           
        
        # subset and reorganise columns to iron standard
        df = df[['m49_a3_country', 'country', 'year', 'dataset_raw', 'value', 'continent', 'region_un', 'region_wb', 'source', 'link', 'note' ]]
        
        # rename cols to new standard
        df = df.rename(columns={"m49_a3_country":"m49_un_a3" })
        
        # pad empty notes
        df['note'] = df['note'].fillna('Not available.')
        
        # count missing values
        print("Missing values: ",df['m49_un_a3'].isna().sum())
        
        pop = pd.concat([pop,df])  #This could be the problem?
    
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
    pop.to_parquet(destination_filepath)
    
    # summary
    toc = time.perf_counter()    
    print("Processed series: ",len(pd.unique(pop['dataset_raw']))," in ",toc-tic," seconds")
    
    return


def ironsmith_bigmac(origin, destination):
    # Transform the data to conform to Atlas data structure and write to IRON
    
    tic = time.perf_counter()     
    
    #testing
    destination = "/data_lakehouse/iron/statistics/big-mac-index/"
    origin = "/data_lakehouse/copper/statistics/big-mac-index/"
    
    origin_filepath = os.getcwd()+origin+'big-mac-index.parquet'
    destination_path = os.getcwd()+destination
    destination_filepath = destination_path+'big-mac-index.parquet'
    
    # read in dataframe
    df = pd.read_parquet(origin_filepath)
    
    # subset to remove redundant data
    df = df[['date', 'iso_a3', 'dollar_price']]
    
    # extract year from date string
    year = df['date'].str.split(pat="-", expand=True)
    df['year'] = year[[0]]
    
    # merge in country M49s and names from meta
    countries = get_unique_country_list()    
    df = df.rename(columns={'iso_a3':'su_a3'})   
    df = df.merge(countries, on='su_a3', how='left')
    
    # Prep
    df['dataset_raw'] = 'Big mac index (US Dollars)'
    df = df.rename(columns={'dollar_price':'value', 'm49_a3_country':'m49_un_a3'})
    
    # Subset and reorganise to align with master structure
    df = df[['m49_un_a3', 'country', 'year', 'dataset_raw', 'value', 'continent', 'region_un', 'region_wb' ]]
    
    # Add custom source, link and note for this dataset
    df['source'] = 'The Economist Big Mac Index https://www.economist.com/big-mac-index'
    df['link'] = 'https://github.com/TheEconomist/big-mac-data'
    df['note'] = 'THE BIG MAC index was invented by The Economist in 1986 as a lighthearted guide to whether currencies are at their “correct” level. It is based on the theory of purchasing-power parity (PPP), the notion that in the long run exchange rates should move towards the rate that would equalise the prices of an identical basket of goods and services (in this case, a burger) in any two countries.'
    
    # data typing 
    df = df.astype({'m49_un_a3': 'category', 
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
    df.to_parquet(destination_filepath)
    
    # summary
    toc = time.perf_counter()    
    print("Processed series: ",len(pd.unique(df['dataset_raw']))," in ",toc-tic," seconds")
    


def get_unique_country_list():
    
    df_countries = pd.read_csv(
       os.getcwd()+paths.COUNTRY_LOOKUP_PATH_COPPER,
       encoding="utf-8",
       names=["m49_a3_country", "country", "continent", "region_un", "region_wb", "su_a3"],
    )
    return df_countries


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



def convert_csv_to_parquet(path, destination_path, encoding):    
    df = pd.read_csv(path,encoding=encoding)     
    filename = path.rsplit('/', 1)[1]
    pq_path = destination_path+(filename[:-3])+"parquet"
    df.to_parquet(pq_path, engine='pyarrow', index=False)
    
    return
    
def convert_xlsx_to_parquet(path, destination_path):    
    df = pd.read_excel(path)      
    filename = path.rsplit('/', 1)[1]
    pq_path = destination_path+(filename[:-4])+"parquet"
    df.to_parquet(pq_path, engine='pyarrow', index=False)
    return


def convert_folder_csv_to_parquet(origin_path, destination_path, encoding):
    #Helper function to convert a whole folder of .csv files to .parquet with same names in the destination
     
    origin_path = os.getcwd()+origin_path 
    destination_path = os.getcwd()+destination_path
  
    #Check if destination folder exists. If not, create it.
    if not os.path.exists(destination_path): os.mkdir(destination_path)  

    for filepath in glob.iglob(origin_path+'*.csv'):
        print(filepath)
        convert_csv_to_parquet(filepath, destination_path, encoding)
    
    return


def convert_folder_xlsx_to_parquet(origin_path, destination_path):
    #Helper function to convert a whole folder of .xlsx files to .parquet with same names in the destination
    
    origin_path = os.getcwd()+origin_path 
    destination_path = os.getcwd()+destination_path
    
    #Check if destination folder exists. If not, create it.
    if not os.path.exists(destination_path): os.mkdir(destination_path)  

    for filepath in glob.iglob(origin_path+'*.xlsx'):
        print(filepath)
        convert_xlsx_to_parquet(filepath, destination_path)
    
    return

















def clean_3d_land_data_JSON_ne110m(json_path):
    
    #this dataset does in fact have the integer codes we want, so all we need to do is some basic processing to make it consistent with what is expected by update_3d_geo_data_JSON
    #i.e. add a few properties with consistent names to what is used in the ne50m data
    #these clean functions are helpers, they only really need to be run once, to producea cleaned geojson file for importing at runtime.
    
    #load data    
    countries_json = json.load(open(json_path, 'r', encoding='utf-8'))
    
    #bring country name up to feature level (from properties.) This is required for tooltip to work on deck.gl    
    gj = copy.deepcopy(countries_json)
    
    #add country name and random colours
    for i in range(0, len(gj['features'])):
        gj['features'][i]['COUNTRY'] = gj['features'][i]['properties']['SUBUNIT'] #grab country name from json(this fieldname differs between natural earth datasets)
        gj['features'][i]['properties']['red']= np.random.randint(0,255)
        gj['features'][i]['properties']['green']= np.random.randint(0,255)
        gj['features'][i]['properties']['blue']= np.random.randint(0,255)
    
    #now we simply create a new property 'sr_un_a3' for consistency with the other datasets so all functions work. In this case, we'll duplicate ISO_n3
    for i in range(0, len(gj['features'])):
        gj['features'][i]['properties']['sr_un_a3'] = gj['features'][i]['properties']['ISO_N3']
    
    
    #now try to write the json as a once off and test it.       
    with open('data/geojson/globe/ne_110m_land_test.geojson', 'w') as outfile:
        json.dump(gj, outfile) 
    
    return gj


def clean_3d_land_data_JSON_ne50m(json_path, countries, json_destination):    
    #Not working. I think some preprocessing was done to the json before this could run on it.
    # Given the time to reengineer, it's simply not worth it unless I need to reprocess it.
    # Storing this on ice.
    
    #This dataset does NOT have the unique integer codes for which I've used as the primary key to extract from pop when updating (in another func)
    #consequently I've added alphanumeric codes "AUS" to the country_lookup, then extracted the integer code and added it to this json under 'sr_un_a3'
    
    #load data    
    countries_json = json.load(open(json_path, 'r', encoding='utf-8'))
            
    #bring country name up to feature level (from properties.) This is required for tooltip to work on deck.gl    
    gj = copy.deepcopy(countries_json)
    
    #add country name and random colours
    for i in range(0, len(gj['features'])):
        gj['features'][i]['COUNTRY'] = gj['features'][i]['properties']['sr_subunit'] #grab country name from json  
        gj['features'][i]['properties']['red']= np.random.randint(0,255)
        gj['features'][i]['properties']['green']= np.random.randint(0,255)
        gj['features'][i]['properties']['blue']= np.random.randint(0,255)
  
    #add in the un_a3 integer code (once) and test out writing this file
    for i in range(0, len(gj['features'])):
        #print(gj['features'][i]['properties']['sr_su_a3'])
        
        if gj['features'][i]['properties']['sr_adm0_a3'] in countries['su_a3'].values:
            #extract un_a3 integer code from lookup and set it as a new feature property in the json
            gj['features'][i]['properties']['sr_un_a3'] = countries[countries["su_a3"]==gj['features'][i]['properties']['sr_adm0_a3']].iloc[0,0]
        else:            
            gj['features'][i]['properties']['sr_un_a3'] = "none"
            
    #now try to write the json as a once off and test it.       
    #with open('data/geojson/globe/ne_50m_land_test.geojson', 'w') as outfile:
    with open(json_destination, 'w') as outfile:
        json.dump(gj, outfile)    
             
    return 


def clean_3d_ocean_data_JSON_ne110m(json_path):
    
    # Storing this on ice.
    
    #load raw json
    geojson_globe_ocean_ne50m = json.load(open(json_path, 'r', encoding='utf-8'))
    
    #deep copy json (had problems so this works)    
    ocean_coords = copy.deepcopy(geojson_globe_ocean_ne50m)

    #ocean: add json features
    geojson_globe_ocean_ne50m['features'][0]['properties']['sr_un_a3'] = "000" 
    geojson_globe_ocean_ne50m['features'][0]['COUNTRY'] = "Ocean"
    geojson_globe_ocean_ne50m['features'][0]['geometry']['type'] = "Polygon"
    #geojson_globe_ocean_ne50m['features'][0]['geometry']['coordinates'] = coord2_L
    geojson_globe_ocean_ne50m['features'][0]['geometry']['coordinates'] = ocean_coords['features'][1]['geometry']['coordinates'][0] 
    
    #append a duplicate of this dictionary to list (i.e. because it was not read in from file like this)
    #geojson_globe_ocean_ne50m['features'].append(copy.deepcopy(geojson_globe_ocean_ne50m['features'][0]))
    
    #Caspian sea: add json features
    geojson_globe_ocean_ne50m['features'][1]['properties']['sr_un_a3'] = "000" #must add this custom property to json
    geojson_globe_ocean_ne50m['features'][1]['COUNTRY'] = "Caspian Sea"
    geojson_globe_ocean_ne50m['features'][1]['geometry']['type'] = "Polygon"
    #geojson_globe_ocean_ne50m['features'][1]['geometry']['coordinates'] = coord1_L
    geojson_globe_ocean_ne50m['features'][1]['geometry']['coordinates'] = ocean_coords['features'][0]['geometry']['coordinates'][0] #caspian sea
    
    #now try to write the json as a once off and test it.       
    gj = geojson_globe_ocean_ne50m
    with open('data/geojson/globe/ne_110m_ocean_test.geojson', 'w') as outfile:
        json.dump(gj, outfile) 
    
    return geojson_globe_ocean_ne50m



def clean_3d_ocean_data_JSON_ne50m(json_path):
    
    # Storing this on ice.
    
    #load raw json
    geojson_globe_ocean_ne50m = json.load(open(json_path, 'r', encoding='utf-8'))
    
    #deep copy json (had problems so this works)    
    ocean_coords = copy.deepcopy(geojson_globe_ocean_ne50m)

    #geojson_globe_ocean_ne50m_test = d.load_3d_geo_data_JSON_cleaned("data/geojson/globe/ne_50m_ocean.geojson")
    
    del(ocean_coords['features'][0]['geometry']['coordinates'][1][98])
        
    #ocean: add json features
    geojson_globe_ocean_ne50m['features'][0]['properties']['sr_un_a3'] = "000" 
    geojson_globe_ocean_ne50m['features'][0]['COUNTRY'] = "Ocean"
    geojson_globe_ocean_ne50m['features'][0]['geometry']['type'] = "Polygon"
    #geojson_globe_ocean_ne50m['features'][0]['geometry']['coordinates'] = coord2_L
    geojson_globe_ocean_ne50m['features'][0]['geometry']['coordinates'] = ocean_coords['features'][0]['geometry']['coordinates'][1] #main ocean
    
    #append a duplicate of this dictionary to list (i.e. because it was not read in from file like this)
    geojson_globe_ocean_ne50m['features'].append(copy.deepcopy(geojson_globe_ocean_ne50m['features'][0]))
    
    #Caspian sea: add json features
    geojson_globe_ocean_ne50m['features'][1]['properties']['sr_un_a3'] = "000" #must add this custom property to json
    geojson_globe_ocean_ne50m['features'][1]['COUNTRY'] = "Caspian Sea"
    geojson_globe_ocean_ne50m['features'][1]['geometry']['type'] = "Polygon"
    #geojson_globe_ocean_ne50m['features'][1]['geometry']['coordinates'] = coord1_L
    geojson_globe_ocean_ne50m['features'][1]['geometry']['coordinates'] = ocean_coords['features'][0]['geometry']['coordinates'][0] #caspian sea
    
    #now try to write the json as a once off and test it.       
    gj = geojson_globe_ocean_ne50m
    with open('data/geojson/globe/ne_50m_ocean_test.geojson', 'w') as outfile:
        json.dump(gj, outfile) 
    
    return geojson_globe_ocean_ne50m



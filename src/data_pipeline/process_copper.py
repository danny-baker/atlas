# Process data in COPPER > IRON

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


def process_copper(container_name_origin: str, container_name_destination: str):
    # process COPPER > IRON
    
    ironsmith_gapminder_fast_track('copper', paths.FASTTRACK_PATH_COPPER, paths.FASTTRACK_PATH_IRON)   #WORKING
    ironsmith_gapminder_systema_globalis('copper', paths.SYSTEMAGLOBALIS_PATH_COPPER, paths.SYSTEMAGLOBALIS_PATH_IRON)     
    ironsmith_gapminder_world_dev_indicators('copper', paths.WDINDICATORS_PATH_COPPER, paths.WDINDICATORS_PATH_IRON)   
    ironsmith_sdgindicators('copper', paths.SDG_PATH_COPPER, paths.SDG_PATH_IRON)
    ironsmith_world_standards('copper', paths.WS_PATH_COPPER, paths.WS_PATH_IRON)
    ironsmith_bigmac('copper', paths.BIG_MAC_PATH_COPPER, paths.BIG_MAC_PATH_IRON)
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


def ironsmith_bigmac(container_name: str, origin_blob_path: str, destination_blob_path: str):
    # Transform the data to conform to Atlas data structure and write to IRON
    
    print('Processing data: ', origin_blob_path)
    
    tic = time.perf_counter()     
    
    # read in unique country list from COPPER location
    countries = get_country_lookup_df('copper', paths.COUNTRY_LOOKUP_PATH_COPPER, 'utf-8')
    
    #read blob-file into df
    sas_url_blob = 'https://' + account_name+'.blob.core.windows.net/' + container_name + '/' + origin_blob_path + '?' + sas_token
    df = pd.read_parquet(sas_url_blob)
    
    # subset to remove redundant data
    df = df[['date', 'iso_a3', 'dollar_price']]
    
    # extract year from date string
    year = df['date'].str.split(pat="-", expand=True)
    df['year'] = year[[0]]    
    
    # merge in country M49s and names from meta
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
    
    # write fast track dataset to parquet-blob
    stream = BytesIO() #initialise a stream
    df.to_parquet(stream, engine='pyarrow', index=False) #write the csv to the stream
    stream.seek(0) #put pointer back to start of stream
    
    # write the stream to blob
    blob_client = blob_service_client.get_blob_client(container='iron', blob=destination_blob_path)
    blob_client.upload_blob(data=stream, overwrite=True, blob_type="BlockBlob")

    # summary
    toc = time.perf_counter()    
    print("Processed series: ",len(pd.unique(df['dataset_raw']))," in ",toc-tic," seconds")
    return


def ironsmith_world_standards(container_name: str, origin_blob_folder: str, destination_blob_path: str):
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
    
    
    tic = time.perf_counter()
    
    # read in unique country list from COPPER location
    countries = get_country_lookup_df('copper', paths.COUNTRY_LOOKUP_PATH_COPPER, 'utf-8')
    
    #declare empty dataframe    
    pop = pd.DataFrame() 
    
    # get file-blob list
    files = walk_blobs(blob_service_client, container_name, origin_blob_folder)
    
    for file in files:
        print("Processing data: ", file)    
        
        #read blob-file into df
        sas_url_blob = 'https://' + account_name+'.blob.core.windows.net/' + container_name + '/' + file + '?' + sas_token
        df = pd.read_parquet(sas_url_blob)
        
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
    
    # write fast track dataset to parquet-blob
    stream = BytesIO() #initialise a stream
    pop.to_parquet(stream, engine='pyarrow', index=False) #write the csv to the stream
    stream.seek(0) #put pointer back to start of stream
    
    # write the stream to blob
    blob_client = blob_service_client.get_blob_client(container='iron', blob=destination_blob_path)
    blob_client.upload_blob(data=stream, overwrite=True, blob_type="BlockBlob")
    
    # summary
    toc = time.perf_counter()    
    print("Processed series: ",len(pd.unique(pop['dataset_raw']))," in ",toc-tic," seconds")
    
    return


def ironsmith_sdgindicators(container_name: str, origin_blob_folder: str, destination_blob_path: str):
    # clean the copper version of these parquets (as was previously done) and place a single consolidated parquet in IRON
    # Goal of this function is to process each dataset into the master format and spit out a summary
    # this data has metadata embedded in each dataset, so less complex to parse than gapminder stuff    
    
    tic = time.perf_counter()  
    print("Processing SDG indicator data COPPER > IRON")
    
    # read in unique country list from COPPER location
    countries = get_country_lookup_df('copper', paths.COUNTRY_LOOKUP_PATH_COPPER, 'utf-8')
    
    #declare empty dataframe    
    pop = pd.DataFrame() 
    
    # get file-blob list
    files = walk_blobs(blob_service_client, container_name, origin_blob_folder)
    
    for file in files:
        print("Loading data: ", file)    
        
        #read blob-file into df
        sas_url_blob = 'https://' + account_name+'.blob.core.windows.net/' + container_name + '/' + file + '?' + sas_token
        df = pd.read_parquet(sas_url_blob)
     
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
    
    # write fast track dataset to parquet-blob
    stream = BytesIO() #initialise a stream
    pop.to_parquet(stream, engine='pyarrow', index=False) #write the csv to the stream
    stream.seek(0) #put pointer back to start of stream
    
    # write the stream to blob
    blob_client = blob_service_client.get_blob_client(container='iron', blob=destination_blob_path)
    blob_client.upload_blob(data=stream, overwrite=True, blob_type="BlockBlob")
    
    # summary
    toc = time.perf_counter()    
    print("Processed series: ",len(pd.unique(pop['dataset_raw']))," in ",(toc-tic)/60," minutes")
    
    return 

def ironsmith_gapminder_fast_track(container_name: str, origin_blob_folder: str, destination_blob_path: str):   
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
    stream = BytesIO() #initialise a stream
    pop.to_parquet(stream, engine='pyarrow', index=False) #write the csv to the stream
    stream.seek(0) #put pointer back to start of stream
    
    # write the stream to blob
    blob_client = blob_service_client.get_blob_client(container='iron', blob=destination_blob_path)
    blob_client.upload_blob(data=stream, overwrite=True, blob_type="BlockBlob")
     
    # summary
    toc = time.perf_counter()    
    print("Processed series: ",len(pd.unique(pop['dataset_raw']))," in ",(toc-tic)/60," minutes")
        
    return


def ironsmith_gapminder_systema_globalis(container_name: str, origin_blob_folder: str, destination_blob_path: str):
    # clean the copper version of these parquets (as was previously done) and place a single consolidated parquet in IRON
    # Goal of this function is to process each dataset into the master format and spit out a summary
    
    tic = time.perf_counter()
    print("Processing systema globalis COPPER > IRON")
    
    # read in unique country list from COPPER location
    countries = get_country_lookup_df('copper', paths.COUNTRY_LOOKUP_PATH_COPPER, 'utf-8')
    
    # read in metadata
    sas_url_blob = 'https://' + account_name+'.blob.core.windows.net/' + container_name + '/' + paths.SYSTEMAGLOBALIS_META_COPPER + '?' + sas_token 
    lookup = pd.read_parquet(sas_url_blob).fillna("Not available")
    
    # get file-blob list
    files = walk_blobs(blob_service_client, container_name, origin_blob_folder)
    
    #declare empty dataframe (which we'll append to)   
    pop = pd.DataFrame() 
    
    for file in files:
        if file == paths.SYSTEMAGLOBALIS_META_COPPER : continue # skip metadata file
        
        print('Importing', file)
        
        # read file into df
        sas_url_blob = 'https://' + account_name+'.blob.core.windows.net/' + container_name + '/' + file + '?' + sas_token
        df = pd.read_parquet(sas_url_blob)
        
        # extract concept unique series id e.g. "mmr_who" (which can be queried from the concepts)
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
   
     
    # write dataset to parquet-blob
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
  
    return


def ironsmith_gapminder_world_dev_indicators(container_name: str, origin_blob_folder: str, destination_blob_path: str): 
    # clean the copper version of these parquets (as was previously done) and place a single consolidated parquet in IRON
    # Goal of this function is to process each dataset into the master format and spit out a summary
    
    tic = time.perf_counter()   
    print("Processing world development indicators COPPER > IRON")
    
    # read in unique country list from COPPER location
    countries = get_country_lookup_df('copper', paths.COUNTRY_LOOKUP_PATH_COPPER, 'utf-8')
    
    # read in metadata
    sas_url_blob = 'https://' + account_name+'.blob.core.windows.net/' + container_name + '/' + paths.WDINDICATORS_META_COPPER + '?' + sas_token 
    lookup = pd.read_parquet(sas_url_blob)
    
    #declare empty dataframe   
    pop = pd.DataFrame()
    
    # get file-blob list
    files = walk_blobs(blob_service_client, container_name, origin_blob_folder)
    
    #Metrics    
    files_num=len(files) 
    runcount=0    
    batch_size=400 #500
    batch_counter=0
    filewritecount=1
    
    #meta paths
    metapath1 = paths.WDINDICATORS_META_COPPER
    metapath2 = origin_blob_folder+"ddf--concepts--discrete.parquet" #checked this. It's all crud. keeping here so it can be skipped
 
    for file in files:
        
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
            destination_filepath = destination_blob_path[:-8]+str(filewritecount)+".parquet"
            print("Writing batch file ",destination_filepath)
            stream = BytesIO() #initialise a stream
            pop.to_parquet(stream, engine='pyarrow', index=False) #write the parquet to the stream
            stream.seek(0) #put pointer back to start of stream
            blob_client = blob_service_client.get_blob_client(container='iron', blob=destination_filepath)
            blob_client.upload_blob(data=stream, overwrite=True, blob_type="BlockBlob")  
            #pop.to_parquet((destination_filepath[:-8])+str(filewritecount)+".parquet"  )
            
            # batch run logic
            filewritecount = filewritecount + 1            
            batch_counter = 0 #reset
            
            # Empty dataframe rapidly
            pop.drop(pop.columns, inplace=True, axis=1)    
            pop = pop.iloc[0:0]
            
        # Continue normal parse
        # in future should scan for filename pattern "ddf-concepts" and "ddf-entities" etc and ignore. This works though.
        if file == metapath1: continue
        if file == metapath2: continue
        
        print("Importing",runcount,"/",files_num," ",file)       
        
        # read in df
        sas_url_blob = 'https://' + account_name+'.blob.core.windows.net/' + container_name + '/' + file + '?' + sas_token 
        df = pd.read_parquet(sas_url_blob)
        
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
    destination_filepath = destination_blob_path[:-8]+str(filewritecount)+".parquet"
    print("Writing batch file ",destination_filepath)
    stream = BytesIO() #initialise a stream
    pop.to_parquet(stream, engine='pyarrow', index=False) #write the parquet to the stream
    stream.seek(0) #put pointer back to start of stream
    blob_client = blob_service_client.get_blob_client(container='iron', blob=destination_filepath)
    blob_client.upload_blob(data=stream, overwrite=True, blob_type="BlockBlob")  
    
    # summary
    toc = time.perf_counter()    
    print("Processed series: ",len(pd.unique(pop['dataset_raw']))," in ",toc-tic," seconds")
    
    
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

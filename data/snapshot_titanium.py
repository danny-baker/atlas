# Download the contents of titanium folder into a new folder on local disk in CWD for the purpose of reading data locally in debug mode
# This would need to be done on local machine manually to update the snapshot and commit changes to branch (repo)

from dotenv import load_dotenv
import data_paths as paths
import pandas as pd
import os #get env vars
import time #tic-toc
import datetime #sas token expiry
from io import BytesIO #stream df > blob


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


def download_blob_to_file(blob_service_client: BlobServiceClient, container_name, blob_path):
    
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_path)
    
    # build full target filepath
    file_path = os.getcwd() + '/' + blob_path      
    
    # fragment this to identify path and filename separately
    path_frags = file_path.split('/')[1:]     
    file = path_frags[-1]    
    path = file_path[:-len(file)]  
    
    # create directory on local disk (if needed)
    os.makedirs(path, exist_ok=True)
    
    # download blob to file
    with open(file=file_path, mode="wb") as sample_blob:
        download_stream = blob_client.download_blob()
        sample_blob.write(download_stream.readall())
        
    print(file_path)


# RUN #

# target folder
target_directory_name = 'data_snapshot'

# Azure storage blob config (credentials)
load_dotenv()
account_name = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
account_key = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
container_name = 'titanium'

# create account SAS (should have root access to all containers)
sas_token = create_account_sas(account_name, account_key)

# build URL version in the proper format
account_sas_url = 'https://' + account_name+'.blob.core.windows.net/' + '?' + sas_token  
#print(account_sas_url)

# create BlobServiceClient object (we now have the jedi power to do all the admin tasks)
blob_service_client = BlobServiceClient(account_url=account_sas_url)

# create target folder
target_path = os.getcwd() + '/' + target_directory_name
os.makedirs(target_path, exist_ok=True)

# set cwd to target folder
os.chdir(target_path)

# list all blobs in container
blb_lst = get_blobs(blob_service_client, container_name)

# select only .geojson .csv .parquet files
blb_lst_files = []
for blob in blb_lst:    
    path_frags = blob.split('.')
    if len(path_frags) == 2: #we only care about files with normal extension (not baks)       
        if path_frags[1] in ['parquet', 'csv', 'json', 'geojson']:            
            blb_lst_files.append(blob)

# download these files from blob to local disk
print('Writing blob to local disk:', os.getcwd())
for file in blb_lst_files:
    download_blob_to_file(blob_service_client, container_name, file)




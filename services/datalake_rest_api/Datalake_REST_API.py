'''
FastAPI REST API Service for DAtafabrikken Demo, DataLake access
----------------------------------------------------------------
https://fastapi.tiangolo.com/
https://realpython.com/fastapi-python-web-apis/
python -m pip install fastapi uvicorn[standard]

See also: https://www.starlette.io/, https://pydantic-docs.helpmanual.io/

Deploy FastAPI on Azure:
https://techcommunity.microsoft.com/t5/apps-on-azure/deploying-a-python-fastapi-on-azure-app-service/m-p/1757016
https://www.youtube.com/watch?v=oLdEI3zUcFg
https://azure.microsoft.com/en-us/services/app-service/api/

Run app with: uvicorn Datalake_REST_API:app --reload
App: http://127.0.0.1:8000
Swagger: http://127.0.0.1:8000/docs
'''

# ------------------------------------------------------------------------------------------------------------

from typing import Optional, List

from datetime import datetime
import uuid
import math
import json
import timeit
import requests
import jsonschema
from jsonschema import validate
import matplotlib as mpl
from matplotlib import pyplot as plt
import seaborn as sns
import os
from os.path import exists
import pandas as pd
import io
import time
import yaml
import collections
import scipy.stats
from scipy.stats import kurtosis, skew
import dicttoxml
from dict2xml import dict2xml
from dicttoxml import dicttoxml
import xml.etree.ElementTree as ET

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from starlette.responses import StreamingResponse, JSONResponse, HTMLResponse, Response
from fastapi import FastAPI, Body, Path, Query, Cookie, Header
from pydantic import BaseModel, Field, EmailStr

from starlette.middleware.cors import CORSMiddleware
# from pycaret.classification import *

# For Azure Blob Storage:
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from azure.core.exceptions import ResourceNotFoundError

BytesIO = pd.io.common.BytesIO

# ------------------------------------------------------------------------------------------------------------

app = FastAPI(title='DataFabrikken 2.0 Datalake Demo API')

# https://fastapi.tiangolo.com/tutorial/sql-databases/
SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"
# SQLALCHEMY_DATABASE_URL = "postgresql://user:password@postgresserver/db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

origins = [
    '*'
]

app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=['GET','POST'],
        allow_headers=['Content-Type','application/xml','application/json'],
    )

course_items = [{"course_name": "Python"}, {"course_name": "SQLAlchemy"}, {"course_name": "NodeJS"}]

'''
class Item(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    tax: Optional[float] = None
'''

# TODO: Enable format conversions (XML/JSON/YAML etc.) with the conversion (XXXReader) routines in DataFabrikken_2_0_TBAK.ipynb
class MyDataLake():
    '''
    Class to get data from Azure blob storage
    '''
    # TODO: KeyVault for Blob storage secret handling for JupyterHub Pod in AKS
    DEBUG = True
    FOLDER = 'Hackathon/'
    storage_account_name = os.environ['STORAGE']
    storage_account_access_key = os.environ['STORAGE_AC']
    storage_container = 'data'
    
    def __init__(self):
        blob_service_client = BlobServiceClient(account_url="https://" + \
                                                self.storage_account_name + \
                                                ".blob.core.windows.net", credential=self.storage_account_access_key)
        self.container_client = blob_service_client.get_container_client(self.storage_container)

        if self.DEBUG:
            print('List data lake contents...')
            try:
                for blob in self.container_client.list_blobs(name_starts_with='Hackathon'):
                    print('File:', blob.name)
            except ResourceNotFoundError:
                print('Unable to locate container!')
        return None
            
    
    async def get_data(self, blob_name, sep=';', encoding='iso-8859-1', header=1, download=False):
        if not self.FOLDER in blob_name:
            blob_name = self.FOLDER + blob_name
        # print(blob_name)
        blob_client = self.container_client.get_blob_client(blob_name)
        blob_content = blob_client.download_blob().readall() # Som bytes
        # blob_content = blob_client.download_blob().content_as_text()
        
        # TODO: We need to check that the blob actually exists, and give a better error message (not exception dump)
        
        if header <= 0:
            header = 1
            
        blob_name = blob_name.upper()
        if not 'ZIP' in blob_name and not 'GZ' in blob_name:
            if 'CSV' in blob_name:
                if self.DEBUG:
                    print('Getting CSV file...')
                self.df = pd.read_csv(BytesIO(blob_content), header=header-1, sep=sep, encoding=encoding)
                # df = pd.read_csv(StringIO(blob_content), header=1, sep=sep, encoding=encoding)
                if download:
                    return self.df.to_csv(index=False)
                else:
                    return self.df.to_dict()
            elif 'XLS' in blob_name:
                if self.DEBUG:
                    print('Getting Excel file...')
                self.df = pd.read_excel(BytesIO(blob_content), header=header-1, engine='openpyxl', index_col=None,
                                       usecols=lambda x: 'Unnamed' not in x) # Convert bytes-array to pandas DataFrame 
                if download:
                    return self.df
                else:
                    return self.df.to_dict()
            elif 'JSON' in blob_name:
                if self.DEBUG:
                    print('Getting JSON file...')
                self.df = pd.read_json(BytesIO(blob_content), header=header-1) # Convert bytes-array to pandas DataFrame 
                return self.df.to_dict()
        else:
            if 'GZ' in blob_name:
                if self.DEBUG:
                    print('Getting GZ file...')
                buffer = zlib.decompress(blob_content, 32 + zlib.MAX_WBITS)  # Offset 32 to skip the header
                return buffer # Return raw?

# -----------------------------------------------------------------------------------------------------------------------------

dl_obj = MyDataLake()

@app.get('/')
async def root():
    return {'message': 'DataFabrikken 2.0 API. See <url>/docs for documentation about the API'}

# Return dataset for download if ?download parameter present, otherwise return dataframe
# https://fastapi.tiangolo.com/tutorial/query-params/
# https://fastapi.tiangolo.com/advanced/custom-response/
@app.get('/datasets/{dataset_name}')
async def download_dataset(dataset_name:str, download: Optional[str]=None):
    if download:
        is_download = True
    else:
        is_download = False

    dataset = await dl_obj.get_data(f'{dataset_name}.csv', sep=';', encoding='utf-8', download=is_download)

    # return str(download)
    if download:
        # TODO: Check the dataset format from param (or in get_data()) and retrun correct media type
        return Response(content=dataset, media_type='text/csv')
    else:
        return dataset
    # Create response object for download that can be saved if 'download' param is not None


# Just for localhost
if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=8000)
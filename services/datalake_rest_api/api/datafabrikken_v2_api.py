'''
FastAPI REST API Service for Datafabrikken Demo, DataLake access
----------------------------------------------------------------
https://fastapi.tiangolo.com/
https://realpython.com/fastapi-python-web-apis/
https://github.com/ecerami/fastapi_azure (This example)
https://github.com/tonybaloney/ants-azure-demos/tree/master/fastapi-functions
https://docs.microsoft.com/en-us/azure/azure-functions/functions-reference-python

For running on uviorn: python -m pip install fastapi uvicorn[standard]

See also: https://www.starlette.io/, https://pydantic-docs.helpmanual.io/

Deploy FastAPI on Azure:
https://medium.com/fastapi-tutorials/serverless-fastapi-on-azure-cddf8cd50482 (Azure Functions)
https://techcommunity.microsoft.com/t5/apps-on-azure/deploying-a-python-fastapi-on-azure-app-service/m-p/1757016
https://www.youtube.com/watch?v=oLdEI3zUcFg
https://azure.microsoft.com/en-us/services/app-service/api/
https://docs.microsoft.com/en-us/azure/app-service/overview-security

Various tips:
https://dev.to/fuadrafid/fastapi-the-good-the-bad-and-the-ugly-20ob

Run app on uvicorn with: uvicorn datafabrikken_api:app --reload

Application: http://127.0.0.1:7071
Swagger page: http://localhost:7071/docs
'''

import azure.functions as func
from .http_asgi import AsgiMiddleware
# import mimesis
import fastapi
# ----
from typing import Optional, List, Union

from datetime import datetime

import uuid
import math
import json
import timeit
import zlib
# import jsonschema
import pandas as pd
# from jsonschema import validate
from urllib.parse import unquote
import os
from os.path import exists
# import pandas as pd
import io
import time
# import yaml
import collections
# import scipy.stats
# from scipy.stats import kurtosis, skew
# import dicttoxml
# from dict2xml import dict2xml
# from dicttoxml import dicttoxml
# import xml.etree.ElementTree as ET

# from sqlalchemy import create_engine
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import sessionmaker

from starlette.responses import StreamingResponse, JSONResponse, HTMLResponse, Response
from starlette.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Body, Path, Query, Cookie, Header, HTTPException
from pydantic import BaseModel, Field, EmailStr

# For Azure Blob Storage:
from azure.storage.blob import BlobServiceClient, ContainerClient # , BlobClient
from azure.storage.blob.aio import BlobClient
from azure.core.exceptions import ResourceNotFoundError

# BytesIO = pd.io.common.BytesIO
# StringIO = pd.io.common.StringIO


app = fastapi.FastAPI(title='DataFabrikken 2.0 Datalake Demo API')

# TODO: Enable format conversions (XML/JSON/YAML etc.) with the conversion (XXXReader) routines
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
            
    
    async def get_data(self, blob_name, page_no=None, per_page=None):
        if not self.FOLDER in blob_name:
            blob_name = self.FOLDER + blob_name
        # print(blob_name)
        blob_client = self.container_client.get_blob_client(blob_name)
        # blob_exists = blob_client.exists()
        try:
            blob_content = blob_client.download_blob().readall() # Som bytes
            blob_exists = True
        except:
            blob_exists = False
        # blob_content = blob_client.download_blob().content_as_text()
        # stream = await blob_client.download_blob()
        # data = await stream.readall()
        
        # TODO: We need to check that the blob actually exists, and give a better error message (not exception dump)
        
        if not blob_exists:
            return False
        
        blob_name = blob_name.upper()
        if not 'ZIP' in blob_name and not 'GZ' in blob_name:
            if 'CSV' in blob_name:
                if self.DEBUG:
                    print('Getting CSV file...')
            elif 'XLS' in blob_name:
                if self.DEBUG:
                    print('Getting Excel file...')
            elif 'JSON' in blob_name:
                if self.DEBUG:
                    print('Getting JSON file...')

            if page_no:
                # TODO: Validate range of page_no and per_page (not negative, etc.)
                # TEST: Need to find linefeed chars to detect number of lines in raw text buffer?
                return blob_content # Default for now
            else:
                return blob_content
        else:
            if 'GZ' in blob_name:
                if self.DEBUG:
                    print('Getting GZ file...')
                buffer = zlib.decompress(blob_content, 32 + zlib.MAX_WBITS)  # Offset 32 to skip the header
                return buffer # Return raw?

# -----------------------------------------------------------------------------------------------------------------------------

dl_obj = MyDataLake()


@app.on_event('startup')
async def startup():
    # TODO: Do init stuff here
    pass

@app.on_event('shutdown')
async def shutdown():
    # TODO: Do cleanup stuff here
    pass

@app.get('/')
async def root():
    return {'message': 'DataFabrikken 2.0 API (TEST). See <url>/docs for Swagger API documentation'}

'''
@app.get("/user/{user_id}")
async def get_user(user_id: int):
    fake_user = mimesis.Person()
    return {
        "user_id": user_id,
        "username": fake_user.username(),
        "firstname": fake_user.first_name(),
        "lastname": fake_user.last_name(),
    }
'''

# Return dataset content or HTTPException if not found
# https://fastapi.tiangolo.com/tutorial/query-params/
# https://fastapi.tiangolo.com/advanced/custom-response/
@app.get('/datasets/{dataset_name}')
async def download_dataset(dataset_name:str, page_no:Optional[int]=None, per_page:Optional[int]=30) -> Union[Response, HTTPException]:
    dataset_name = unquote(dataset_name)
    print('Dataset name:', dataset_name)
    # return dataset_name

    if '.XLS' in dataset_name.upper():
        extension = 'excel'
        # Content-Type': 'application/vnd.ms-excel
    if '.CSV' in dataset_name.upper():
        extension = 'csv'
    if '.XML' in dataset_name.upper():
        extension = 'xml'
    if '.JSON' in dataset_name.upper():
        extension = 'json'

    try:
        dataset = await dl_obj.get_data(f'{dataset_name}', page_no=page_no, per_page=per_page)
    except Exception as e:
        return HTTPException(status_code=500, detail=f'An error occured: {e.message}')
       
    if not dataset:
        return HTTPException(status_code=404, detail=f'File \'{dataset_name}\' does not exist.')

    return Response(content=dataset, media_type=f'text/{extension}')

# --------------------------------------------------------------------------------------------------

def main(req: func.HttpRequest, context: func.Context) -> func.HttpResponse:
    return AsgiMiddleware(app).handle(req, context)

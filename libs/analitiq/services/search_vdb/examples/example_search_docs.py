"""
This is an example of how to search documents using search services.
"""

import os
import sys
# Get the home directory
home_directory = os.environ['HOME']
# Dynamically construct the path
dynamic_path = f'{home_directory}/Documents/Projects/analitiq/libs/'
sys.path.insert(0, dynamic_path)

from analitiq.services.search_vdb.search_vdb import SearchVdb
from analitiq.base.llm.BaseLlm import BaseLlm
from analitiq.base.vectordb.weaviate.weaviate_vs import WeaviateHandler

user_prompt = "Please give me revenues by month."

llm_params = {'type': 'bedrock'
    , 'name': 'aws_llm'
    , 'api_key': None
    , 'temperature': 0.0
    , 'llm_model_name': 'anthropic.claude-v2'
    , 'credentials_profile_name': 'xxx'
    , 'provider': 'anthropic'
    , 'aws_access_key_id': 'xxxx'
    , 'aws_secret_access_key': 'xxx'
    , 'region_name': 'eu-central-1'}
llm = BaseLlm(llm_params)

params = {
    "collection_name": "my_collection",
    "host": "https://xxxxx.weaviate.network",
    "api_key": "xxxxx"
}

vdb = WeaviateHandler(params)

# Example of using the SQLGenerator class
service = SearchVdb(llm, vdb=vdb)
result = service.run("Please give me revenues by month.")
print(result)


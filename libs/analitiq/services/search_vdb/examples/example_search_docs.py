"""
This is an example of how to search documents using search services.
"""

import os

from analitiq.services.search_vdb.search_vdb import SearchVdb
from analitiq.base.llm.BaseLlm import BaseLlm
from analitiq.vectordb.weaviate import WeaviateHandler

from dotenv import load_dotenv

load_dotenv()

WV_URL = os.getenv("WEAVIATE_URL")
WV_CLIENT_SECRET = os.getenv("WEAVIATE_CLIENT_SECRET")

if not WV_URL or not WV_CLIENT_SECRET:
    raise KeyError("Environment Variables not set. Please set variables!")

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
    "host": WV_URL,
    "api_key": WV_CLIENT_SECRET,
}

vdb = WeaviateHandler(params)

# Example of using the SQLGenerator class
service = SearchVdb(llm, vdb=vdb, search_mode="hybrid")
result = service.run("Please give me revenues by month.")
print(result)


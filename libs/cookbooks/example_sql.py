"""
This is an example of how to run this service as a standalone in order to test it or play with it.
"""
import os
import sys
# Get the home directory
home_directory = os.environ['HOME']
# Dynamically construct the path
dynamic_path = f'{home_directory}/Documents/Projects/analitiq/libs/'
sys.path.insert(0, dynamic_path)

from analitiq.services.sql.sql import Sql
from analitiq.base.Database import DatabaseWrapper
from analitiq.base.llm.BaseLlm import BaseLlm
from analitiq.base.vectordb.weaviate.weaviate_vs import WeaviateHandler

db_params = {'name': 'prod_dw'
    , 'type': 'redshift'
    , 'host': 'xxxx'
    , 'username': 'xxxx'
    , 'password': 'xxxx'
    , 'port': 5439
    , 'db_name': 'xxxx'
    , 'db_schemas': ['xxx', 'xxx']
    , 'threads': 4
    , 'keepalives_idle': 240
    , 'connect_timeout': 10}
db = DatabaseWrapper(db_params)

llm_params = {'type': 'bedrock'
    , 'name': 'aws_llm'
    , 'api_key': None
    , 'temperature': 0.0
    , 'llm_model_name': 'anthropic.claude-v2'
    , 'credentials_profile_name': 'xxx'
    , 'provider': 'anthropic'
    , 'aws_access_key_id': 'xxxxxx'
    , 'aws_secret_access_key': 'xxxxx'
    , 'region_name': 'eu-central-1'}
llm = BaseLlm(llm_params)

params = {
    "collection_name": "my_project",
    "host": "https://analitiq-vpgg1crw.weaviate.network",
    "api_key": "xxxxx"
}

vdb = WeaviateHandler(vdb_params)

# Example of using the SQLGenerator class
agent = Sql(db, llm, vdb=vdb)
result = agent.run("Please give me revenues by month.")
print(result)


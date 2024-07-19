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

from analitiq.agents.sql.sql import Sql
from analitiq.base.Database import DatabaseWrapper
from analitiq.base.llm.BaseLlm import BaseLlm
from analitiq.vectordb.weaviate import WeaviateHandler

from dotenv import load_dotenv

load_dotenv()

WV_COLLECTION = os.getenv("WEAVIATE_COLLECTION")
WV_URL = os.getenv("WEAVIATE_URL")
WV_CLIENT_SECRET = os.getenv("WEAVIATE_CLIENT_SECRET")

LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME")
CREDENTIALS_PROFILE_NAME = os.getenv("CREDENTIALS_PROFILE_NAME")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
REGION_NAME = os.getenv("REGION_NAME")

DB_NAME = os.getenv("DB_NAME")
DB_TYPE = os.getenv("DB_TYPE")
DB_HOST = os.getenv("DB_HOST")
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = os.getenv("DB_PORT")
DB_DB_NAME = os.getenv("DB_DB_NAME")
DB_SCHEMAS = os.getenv("DB_SCHEMAS").split(',')  # Assuming schemas are comma separated in .env
DB_THREADS = int(os.getenv("DB_THREADS"))
DB_KEEPALIVES_IDLE = int(os.getenv("DB_KEEPALIVES_IDLE"))
DB_CONNECT_TIMEOUT = int(os.getenv("DB_CONNECT_TIMEOUT"))

db_params = {
    'name': DB_NAME,
    'type': DB_TYPE,
    'host': DB_HOST,
    'username': DB_USERNAME,
    'password': DB_PASSWORD,
    'port': DB_PORT,
    'db_name': DB_DB_NAME,
    'db_schemas': DB_SCHEMAS,
    'threads': DB_THREADS,
    'keepalives_idle': DB_KEEPALIVES_IDLE,
    'connect_timeout': DB_CONNECT_TIMEOUT
}
db = DatabaseWrapper(db_params)

llm_params = {'type': 'bedrock'
    , 'name': 'aws_llm'
    , 'api_key': None
    , 'temperature': 0.0
    , 'llm_model_name': LLM_MODEL_NAME
    , 'credentials_profile_name': CREDENTIALS_PROFILE_NAME
    , 'provider': 'anthropic'
    , 'aws_access_key_id': AWS_ACCESS_KEY_ID
    , 'aws_secret_access_key': AWS_SECRET_ACCESS_KEY
    , 'region_name': REGION_NAME
}
llm = BaseLlm(llm_params)

vdb_params = {
    "collection_name": WV_COLLECTION,
    "host": WV_URL,
    "api_key": WV_CLIENT_SECRET
}

vdb = WeaviateHandler(vdb_params)

# Example of using the SQLGenerator class
agent = Sql(db, llm, vdb=vdb)
result = agent.run("Please give me revenues by month.")
print(result)


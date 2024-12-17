"""
This is an example of how to gete all objects from Weaviate.
"""
import os
from analitiq.factories.vector_database_factory import VectorDatabaseFactory
from dotenv import load_dotenv

load_dotenv()

vdb_params = {
    "collection_name": os.getenv("COLLECTION_NAME"),
    "tenant_name": os.getenv("WEAVIATE_TENANT_NAME"),
    "type": os.getenv("VDB_TYPE"),
    "host": os.getenv("VDB_HOST"),
    "api_key": os.getenv("VDB_API_KEY")
}


vdb = VectorDatabaseFactory.connect(vdb_params)

collection = vdb.client.collections.get(vdb_params['collection_name']).with_tenant(vdb_params['tenant_name'])

print(f"Found {len(collection)} items:")

for item in collection.iterator():
    content = item.properties.get('content', None)
    print(content)
    print('-'*100)

vdb.client.close()

import requests
import json


# Note: Replace "YOUR_API_KEY_HERE" with your actual OpenAI API key.
# You can obtain an API key from https://platform.openai.com/account/api-keys

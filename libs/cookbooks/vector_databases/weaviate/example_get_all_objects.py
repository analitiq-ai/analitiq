"""
This is an example of how to gete all objects from Weaviate.
"""
import os
from analitiq.factories.vector_database_factory import VectorDatabaseFactory
from dotenv import load_dotenv

load_dotenv()

vdb_params = {
    "collection_name": os.getenv("WEAVIATE_COLLECTION"),
    "tenant_name": os.getenv("WEAVIATE_TENANT_NAME"),
    "type": os.getenv("VDB_TYPE"),
    "host": os.getenv("WEAVIATE_URL"),
    "api_key": os.getenv("WEAVIATE_CLIENT_SECRET")
}


vdb = VectorDatabaseFactory.connect(vdb_params)

collection = vdb.client.collections.get(vdb_params['collection_name']).with_tenant(vdb_params['tenant_name'])

for item in collection.iterator():
    print(item.uuid, item.properties)

vdb.client.close()

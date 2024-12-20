"""
This is an example of how to create a collection in Vector Database using Analitiq.
"""
import os
from analitiq.factories.vector_database_factory import VectorDatabaseFactory
from dotenv import load_dotenv

load_dotenv()

vdb_params = {
    "type": os.getenv("VDB_TYPE"),
    "collection_name": os.getenv("COLLECTION_NAME"),
    "tenant_name": os.getenv("WEAVIATE_TENANT_NAME"),
    "host": os.getenv("VDB_HOST"),
    "api_key": os.getenv("VDB_API_KEY")
}

vdb = VectorDatabaseFactory.connect(vdb_params)

multi_collection = vdb.client.collections.get(vdb_params['collection_name'])

result = multi_collection.tenants.remove(['Belle'])

vdb.close()

print(result)

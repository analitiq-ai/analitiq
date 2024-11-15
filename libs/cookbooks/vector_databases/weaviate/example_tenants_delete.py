"""
This is an example of how to create a collection in Vector Database using Analitiq.
"""
import os
from analitiq.factories.vector_database_factory import VectorDatabaseFactory
from dotenv import load_dotenv

load_dotenv()

vdb_params = {
    "type": os.getenv("VDB_TYPE"),
    "collection_name": os.getenv("WEAVIATE_COLLECTION"),
    "tenant_name": os.getenv("WEAVIATE_TENANT_NAME"),
    "host": os.getenv("WEAVIATE_URL"),
    "api_key": os.getenv("WEAVIATE_CLIENT_SECRET")
}

vdb = VectorDatabaseFactory.connect(vdb_params)

multi_collection = vdb.client.collections.get(vdb_params['collection_name'])

result = multi_collection.tenants.remove(['12345-12345-24324'])

vdb.close()

print(result)

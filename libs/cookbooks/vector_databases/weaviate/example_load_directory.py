"""
This is an example of how to load a directory into the Vector Database using Analitiq.
"""
import os
from analitiq.factories.vector_database_factory import VectorDatabaseFactory
from dotenv import load_dotenv
load_dotenv()

vdb_params = {
    "collection_name": os.getenv("WEAVIATE_COLLECTION"),
    "tenant_name": os.getenv("WEAVIATE_TENANT_NAME"),
    "type": os.getenv("VDB_TYPE"),
    "host": os.getenv("VDB_HOST"),
    "api_key": os.getenv("VDB_API_KEY")
}

vdb = VectorDatabaseFactory.connect(vdb_params)

response = vdb.load_dir("/xxx/xxx/xxx/xxx", 'txt')

print(response)

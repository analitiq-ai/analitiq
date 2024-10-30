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
    "host": os.getenv("WEAVIATE_URL"),
    "api_key": os.getenv("WEAVIATE_CLIENT_SECRET")
}


vdb = VectorDatabaseFactory.connect(vdb_params)

FILE_PATH = '/Users/kirillandriychuk/Documents/Projects/analitiq-ai/libs/cookbooks/vector_databases/weaviate/test_file.txt'
response = vdb.load_file(FILE_PATH)

print(response)

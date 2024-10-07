"""
This is an example of how to delete a bunch of objects from weaviate by specifying their matadata parameters.
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


filter_list = [
    {"property": "document_type", "operator": "=", "value": "txt"}
]

vdb = VectorDatabaseFactory.create_database(vdb_params)
result = vdb.delete_on_metadata_and(filter_list)

print(result)

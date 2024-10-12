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

filter_expression = {
    "and": [
        {"property": "document_tags", "operator": "contains_any", "value": ["ddl"]}
    ]
}

vdb = VectorDatabaseFactory.connect(vdb_params)

response = vdb.search_filter('venue', filter_expression)

print(response)

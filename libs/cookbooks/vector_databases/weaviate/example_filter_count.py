"""
This is an example of how to create a collection in Vector Database using Analitiq.
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
    "or": [
        {
            "and": [
                {"property": "document_name", "operator": "like", "value": "test"},
                {"property": "document_source", "operator": "like", "value": "test"},
            ]
        },
        {
            "and": [
                {
                    "property": "document_name",
                    "operator": "=",
                    "value": "test_document_1.txt",
                },
                {
                    "property": "document_name",
                    "operator": "=",
                    "value": "test_document_1",
                },
            ]
        },
    ]
}

vdb = VectorDatabaseFactory.create_database(vdb_params)


response = vdb.filter_count(filter_expression)
print(response)

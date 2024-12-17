"""
This is an example of how to load a directory into the Vector Database using Analitiq.
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


filter_expression = {
    "and": [
        {"property": "document_tags", "operator": "contains_any", "value": ["ddl"]}
    ]
}

vdb = VectorDatabaseFactory.connect(vdb_params)

response = vdb.search_filter('venue', filter_expression)

# Iterate through each object in the 'objects' list
for obj in response.objects:
    # Access the properties of the object
    uuid = obj.uuid
    metadata = obj.metadata
    properties = obj.properties

    # Print or process the object details as needed
    print(f"UUID: {uuid}")
    print(f"Metadata: {metadata}")
    print(f"Properties: {properties}")
    print("-" * 40)  # Separator for clarity


#print(response)

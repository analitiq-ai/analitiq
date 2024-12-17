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


vdb = VectorDatabaseFactory.connect(vdb_params)

response = vdb.vector_search('appointment')


# Iterate through each object and extract relevant information
for obj in response.objects:
    # Extract properties
    uuid = obj.uuid
    collection = obj.collection
    properties = obj.properties

    # Print the properties or store them in a list
    print(f"UUID: {uuid}")
    print(f"Collection: {collection}")
    for key, value in properties.items():
        print(f"{key}: {value}")
    print("-" * 40)

#print(response)

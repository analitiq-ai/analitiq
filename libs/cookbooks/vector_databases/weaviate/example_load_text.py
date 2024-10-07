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


vdb = VectorDatabaseFactory.create_database(vdb_params)

document = {
    "document_text": "This is sample document text",
    "metadata": {
        "document_name": "schema.table",
        "document_type": "ddl",
        "document_uuid": "uuid1234567",
        "source": "host.database"
    }
}

response = vdb.load_text(document['document_text'], document['metadata'])

print(response)

"""
This is an example of how to load a directory into the Vector Database using Analitiq.
"""
import os
from analitiq.factories.vector_database_factory import VectorDatabaseFactory

from dotenv import load_dotenv

load_dotenv()

vdb_params = {
    "collection_name": os.getenv("COLLECTION_NAME"),
    "tenant_name": "Belle",
    "type": os.getenv("VDB_TYPE"),
    "host": os.getenv("VDB_HOST"),
    "api_key": os.getenv("VDB_API_KEY")
}

vdb = VectorDatabaseFactory.connect(vdb_params)

result = vdb.load_text("This is a sample text", "appointments", "txt", "4435056b-44b2-4935-a11f-2adb3c06b305", ["Surgeon","tag2"])

print(result)



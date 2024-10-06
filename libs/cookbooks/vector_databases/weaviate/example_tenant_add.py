"""
This is an example of how to create a collection in Vector Database using Analitiq.
"""
import os
from analitiq.factories.vector_database_factory import VectorDatabaseFactory
from dotenv import load_dotenv

load_dotenv()

vdb_params = {
    "collection_name": "Analitiq",
    "tenant_name": "d3449862-40f1-708f-1e1e-2ebff76034f5",
    "type": os.getenv("VDB_TYPE"),
    "host": os.getenv("WEAVIATE_URL"),
    "api_key": os.getenv("WEAVIATE_CLIENT_SECRET")
}

vdb = VectorDatabaseFactory.create_database(vdb_params)

with vdb:
    response = vdb.collection_add_tenant(vdb_params['tenant_name'])


print(response)

"""
# Deleting a tenant
# Caution - this will remove all of the associated data for the tenants
with vdb:
    collection = vdb.client.collections.get(vdb_params['collection_name'])
    response = collection.tenants.remove([
        vdb_params['tenant_name']
    ])

print(response)
"""

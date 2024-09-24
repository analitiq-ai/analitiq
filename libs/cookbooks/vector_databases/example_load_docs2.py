import weaviate
from weaviate.classes.query import Filter
from weaviate.classes.aggregate import GroupByAggregate
import os
from dotenv import load_dotenv
load_dotenv()

# Establish a connection to Weaviate Cloud
with weaviate.connect_to_weaviate_cloud(
        cluster_url=os.getenv("WEAVIATE_URL"),
        auth_credentials=weaviate.AuthApiKey(api_key=os.getenv("WEAVIATE_CLIENT_SECRET"))
) as client:

    collection = client.collections.get("Test")

    # Get collection specific to the required tenant
    multi_tenant = collection.with_tenant("test")

    tenant_id = "test"

    # Build and execute the aggregate query using client.query
    response = multi_tenant.aggregate.over_all(
        filters=Filter.by_property(name="document_name").like("*test*"),
        group_by=GroupByAggregate(prop="date_loaded"),
        total_count=True
    )

    print(response)
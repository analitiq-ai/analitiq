"""This is an example of how to load documents into VectorDB before allowing analitiq access them."""
import os
from analitiq.factories.vector_database_factory import VectorDatabaseFactory
from dotenv import load_dotenv
import sys

load_dotenv()


vdb_params = {
        "collection_name": "c3b428e2_8031_7034_2cb0_dc342a086229",
        "type": "weaviate",
        "host": os.getenv("WEAVIATE_URL"),
        "api_key": os.getenv("WEAVIATE_CLIENT_SECRET")
    }

vdb = VectorDatabaseFactory.create_database(vdb_params)

#response = vdb.delete_collection("test")
#response = vdb.create_collection("test")
#response = vdb.load_dir('/Users/kirillandriychuk/Documents/Projects/analitiq-ai/libs/tests/unit/databases/vector/', 'txt')
#response = vdb.hybrid_search("bikes")

filter_expression = {
    "and": [
        {"property": "document_name", "operator": "=", "value": "schema.table"},
        {"property": "document_type", "operator": "=", "value": "ddl"},
        {"property": "source", "operator": "=", "value": "host.database"}
    ]
}
with vdb:
    response = vdb.search('sample')
print(response)

sys.exit()
#for g in response.groups:
#    print(g.total_count)
    #print(g.properties)
    #print(g.grouped_by)


"""
Load a directory
"""
# FILE_PATH = '/xxx/xxx/xxx/xxx/models'
# vdb.load(FILE_PATH, 'sql')

"""
Loading a single file
"""
# FILE_PATH = '/xxx/xxx/xxx/xxx/models'
# vdb.load(FILE_PATH)

"""
Search for results
"""

# result = vdb.kw_search("bike")
# print(result)

"""
Search for results and filter by parameter
"""
# result = vdb.search_vector_database_with_filter('revenue', 'document_name', 'schema.yml')
# print(result)

"""
Delete a collection
"""
# vdb.delete_collection(vdb_params['collection_name'])

"""
Delete by document type
"""
# parameters = [("document_name", 'schema_cds'),
#                          ("document_type", 'ddl')]
# vdb.delete_objects(parameters)

"""
Match object by UUID
"""

# uuid='f33971d7-8adf-5127-99bb-8307f24f50c3'
# result = vdb.get_by_uuid(uuid)
# print(result)


"""
Count objects by parameter fileter
"""
# parameters = [("document_name", 'cds'),("document_type", 'ddl')]
# response = vdb.count_objects_by_properties(parameters, 'like')
# print(response.total_count)

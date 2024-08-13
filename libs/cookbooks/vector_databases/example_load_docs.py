"""This is an example of how to load documents into VectorDB before allowing analitiq access them."""
import os
from libs.analitiq.vectordb.weaviate_handler import WeaviateHandler
from dotenv import load_dotenv
import sys

load_dotenv()

ENV_VARIABLES = ["WEAVIATE_COLLECTION", "WEAVIATE_URL", "WEAVIATE_CLIENT_SECRET"]


def load_env_variables():
    load_dotenv()
    env_vars = {variable_name: os.getenv(variable_name) for variable_name in ENV_VARIABLES}

    for var, value in env_vars.items():
        if value is None:
            msg = f"Environment variable {var} not loaded."
            raise EnvironmentError(msg)
    return env_vars


env_vars = load_env_variables()


def define_vdb_params(env_vars):
    return {
        "collection_name": 'test_collection',
        "host": "xxxx",
        "api_key": "xxxxx",
    }


vdb_params = define_vdb_params(env_vars)
weaviate_handler = WeaviateHandler(vdb_params)

weaviate_handler.client.connect()
#response = weaviate_handler.delete_collection("test_collection")
#weaviate_handler.client.connect()
#response = weaviate_handler.create_collection("test_collection")
#response = weaviate_handler.load_dir('/Users/kirillandriychuk/Documents/Projects/analitiq/libs/tests/vectordb/test_dir', 'txt')

filter_expression = {
    "and": [
        {
            "or": [
                {"property": "document_name", "operator": "like", "value": "test"},
                {"property": "content", "operator": "!=", "value": "This is the first test document."}
            ]
        },
        {
            "or": [
                {"property": "document_name", "operator": "=", "value": "project_plan.txt"},
                {"property": "content", "operator": "like", "value": 'project'}
            ]
        }
    ]
}
response = weaviate_handler.count_with_filter(filter_expression)
print(response)

#for g in response.groups:
#    print(g.total_count)
    #print(g.properties)
    #print(g.grouped_by)

sys.exit()
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

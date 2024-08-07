"""
This is an example of how to load documents into VectorDB before allowing analitiq access them.
"""

import os
from libs.analitiq.vectordb.weaviate import WeaviateHandler
from dotenv import load_dotenv

load_dotenv()

ENV_VARIABLES = ["WEAVIATE_COLLECTION", "WEAVIATE_URL", "WEAVIATE_CLIENT_SECRET"]


def load_env_variables():
    load_dotenv()
    env_vars = {variable_name: os.getenv(variable_name) for variable_name in ENV_VARIABLES}

    for var, value in env_vars.items():
        if value is None:
            raise EnvironmentError(f"Environment variable {var} not loaded.")
    return env_vars


env_vars = load_env_variables()


def define_vdb_params(env_vars):
    return {
        "collection_name": "test",
        "host": env_vars.get("WEAVIATE_URL"),
        "api_key": env_vars.get("WEAVIATE_CLIENT_SECRET")
    }


vdb_params = define_vdb_params(env_vars)
vdb = WeaviateHandler(vdb_params)


response = vdb.get_all_objects()
for item in response:
    print(item)
#for g in response.groups:
#    print(g.total_count)
    #print(g.properties)
    #print(g.grouped_by)

exit()
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
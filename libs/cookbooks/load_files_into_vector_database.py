from libs.analitiq.vectordb.weaviate import WeaviateHandler

params = {
    "collection_name": "xxx",
    "host": "xxxxx",
    "api_key": "xxxx"
}

vdb = WeaviateHandler(params)

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

result = vdb.kw_search("bike")
print(result)

"""
Delete a collection
"""
# vdb.delete_collection(params['collection_name'])

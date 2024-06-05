from analitiq.vectordb.weaviate import WeaviateHandler

params = {
    "collection_name": "my_collection",
    "host": "https://xxxx.xxxx.gcp.weaviate.cloud",
    "api_key": "xxxxx"
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

result = vdb.kw_search("revenue")
print(result)

"""
Delete a collection
"""
# vdb.delete_collection(params['collection_name'])

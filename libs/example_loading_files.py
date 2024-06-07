from analitiq.vectordb.weaviate import WeaviateHandler

params = {
    "collection_name": "bikmo",
    "host": "https://cgde46retuswar6uiwfva.c0-1.europe-west3.gcp.weaviate.cloud",
    "api_key": "7j8EFvegyKRqO1szJzMoLz63B3JKekGxp4io"
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

"""
This is an example of how to load documents into VectorDB before allowing analitiq access them.
"""

import os

from libs.analitiq.vectordb.weaviate import WeaviateHandler

from dotenv import load_dotenv

load_dotenv()

WV_COLL = os.getenv("WEAVIATE_COLLECTION_NAME")
WV_URL = os.getenv("WEAVIATE_URL")
WV_CLIENT_SECRET = os.getenv("WEAVIATE_CLIENT_SECRET")

if not WV_URL or not WV_CLIENT_SECRET:
    raise KeyError("Environment Variables not set. Please set variables!")


params = {
    "collection_name": WEAVIATE_COLLECTION_NAME,
    "host": WV_URL,
    "api_key": WV_CLIENT_SECRET
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

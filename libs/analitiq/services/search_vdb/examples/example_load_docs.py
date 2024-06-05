"""
This is an example of how to load documents into VectorDB before allowing analitiq access them.
"""

import os
import sys
# Get the home directory
home_directory = os.environ['HOME']
# Dynamically construct the path
dynamic_path = f'{home_directory}/Documents/Projects/analitiq/libs/'
sys.path.insert(0, dynamic_path)

from analitiq.base.vectordb.weaviate.weaviate_vs import WeaviateHandler

params = {
    "collection_name": "my_collection",
    "host": "https://xxxxx.weaviate.network",
    "api_key": "xxxxx"
}


wc=WeaviateHandler(params)
FILE_PATH = '/xxx/xxx/xxx/xxx/xxx/test_schema.yml'
wc.load(FILE_PATH)

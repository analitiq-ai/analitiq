"""
This is an example of how to load documents into VectorDB before allowing analitiq access them.
"""

import os

from analitiq.vectordb.weaviate import WeaviateHandler

from dotenv import load_dotenv

load_dotenv()

WV_URL = os.getenv("WEAVIATE_URL")
WV_CLIENT_SECRET = os.getenv("WEAVIATE_CLIENT_SECRET")

if not WV_URL or not WV_CLIENT_SECRET:
    raise KeyError("Environment Variables not set. Please set variables!")


params = {
    "collection_name": "bikmo",
    "host": WV_URL,
    "api_key": WV_CLIENT_SECRET
}


wc = WeaviateHandler(params)
FILE_PATH = './example_test_files/elefants.txt'
wc.load(FILE_PATH)

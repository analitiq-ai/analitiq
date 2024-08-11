"""This is an example of how to load documents into VectorDB before allowing analitiq access them."""

import os
import pathlib
from analitiq.vectordb.weaviate import WeaviateHandler

from dotenv import load_dotenv

load_dotenv()

WV_URL = os.getenv("WEAVIATE_URL")
WV_CLIENT_SECRET = os.getenv("WEAVIATE_CLIENT_SECRET")

if not WV_URL or not WV_CLIENT_SECRET:
    raise KeyError("Environment Variables not set. Please set variables!")


params = {"collection_name": "daniel_test", "host": WV_URL, "api_key": WV_CLIENT_SECRET}


wc = WeaviateHandler(params)
# wc.delete_collection("daniel_test")
CURRENT_DIR = pathlib.Path(__file__).resolve().parent
FILE_DIR = pathlib.Path(CURRENT_DIR / "example_test_files")
FILES = [file for file in FILE_DIR.iterdir() if file.is_file()]
for file in FILES:
    wc.load(str(file))
    print(file)

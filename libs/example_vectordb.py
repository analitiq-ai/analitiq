from analitiq.storage.weaviate.weaviate_vs import WeaviateVS
import os
host = "https://test-b12yfnl7.weaviate.network"
api_key = "pozRTL69FRGla8Jpe5Oq1bKJUonfxj43MtnR"
project_name = "analitiq"

wc=WeaviateVS(host, api_key, project_name)
FILE_PATH = '/Users/kirillandriychuk/Documents/Intellij Projects/bikmo/etl/dbt/target/compiled/BIkmo/models'
wc.load_dir(FILE_PATH, 'sql')
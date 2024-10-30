# Weaviate Vector Database Integration Example

This Python module demonstrates how to interact with a Weaviate vector database, including loading document chunks and performing searches.

## Usage Examples

You may need to add directory for Analitiq to your Python path.
Here is an example:
```python
import os
import sys
# Get the home directory
home_directory = os.environ['HOME']
# Dynamically construct the path
dynamic_path = f'{home_directory}/Documents/Projects/analitiq/libs/'
sys.path.insert(0, dynamic_path)
```

Loading all SQL files from a directory into your Weaviate vectore store and indexing them for search

```python
from analitiq.factories.vector_database_factory import VectorDatabaseFactory

params = {
    "collection_name": "my_project",
    "type": 'weaviate',
    'tenant_name': 'my_project',
    "host": "https://XXXXXXX.weaviate.network",
    "api_key": "XXXXXX"
}

vdb = VectorDatabaseFactory.connect(params)
FILE_PATH = './project/My_Project/sql'

vdb.load(FILE_PATH, 'sql')
```

Loading one file into your Weaviate vectore store and indexing it for search

```python
from analitiq.factories.vector_database_factory import VectorDatabaseFactory

params = {
    "collection_name": "my_project",
    "type": 'weaviate',
    'tenant_name': 'my_project',
    "host": "https://XXXXXXX.weaviate.network",
    "api_key": "XXXXXX"
}

vdb = VectorDatabaseFactory.connect(params)
FILE_PATH = './project/My_Project/my_file.sql'
vdb.load_file(FILE_PATH)
```

## Searching for data
Our search service offers two primary functionalities: performing keyword searches to retrieve documents from a database and grouping search results by document name and source for organized analysis. These functionalities are accessible through two methods in the SearchService class, utilizing Python decorators for flexibility in handling search results.

### Keyword Search
The `kw_search` method performs a keyword search in the database and returns a list of documents matching the search query.

Usage Example:

```python
from analitiq.factories.vector_database_factory import VectorDatabaseFactory

params = {
    "collection_name": "my_project",
    "type": 'weaviate',
    'tenant_name': 'my_project',
    "host": "https://XXXXXXX.weaviate.network",
    "api_key": "XXXXXX"
}

vdb = VectorDatabaseFactory.connect(params)
FILE_PATH = './project/My_Project/my_file.sql'
vdb.load_file(FILE_PATH)
search_results = vdb.kw_search("climate change", limit=5)
```
Returned Data Format:
The method returns a dictionary containing the search results. Each item in the dictionary represents a document matching the query.

```json
{
"document_id_1": {
"content": "Document content related to climate change...",
"document_name": "Document 1",
"source": "Source A"
},
"document_id_2": {
"content": "Another document content about climate change...",
"document_name": "Document 2",
"source": "Source B"
}
}
```
### Grouped Search Results
The `kw_search_grouped` method extends the keyword search functionality by grouping the search results based on their document_name and source. This method is useful for analyzing the distribution of documents across different sources or document types.

Usage Example:

```python
from analitiq.factories.vector_database_factory import VectorDatabaseFactory

params = {
    "collection_name": "my_project",
    "type": 'weaviate',
    'tenant_name': 'my_project',
    "host": "https://XXXXXXX.weaviate.network",
    "api_key": "XXXXXX"
}

vdb = VectorDatabaseFactory.connect(params)
FILE_PATH = './project/My_Project/my_file.sql'
vdb.load_file(FILE_PATH)
grouped_results = vdb.kw_search_grouped("sustainable energy", limit=5)
```
Returned Data Format:
This method returns a dictionary where each key is a tuple of (document_name, source), and the value is a list of documents that belong to that document name and source.

```json
{
"('Document 1', 'Source A')": [
"Document content related to sustainable energy...",
"Another piece of content from the same document and source..."
],
"('Document 2', 'Source B')": [
"Document content on sustainable energy from a different source..."
]
}
```
These functionalities aim to provide an efficient and flexible way to search and analyze documents in our database. Whether you need a straightforward list of search results or a grouped view based on specific attributes, the `SearchService` class caters to both requirements seamlessly.

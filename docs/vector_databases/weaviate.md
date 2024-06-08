# Analitiq Weaviate Integration Documentation

This documentation covers the `WeaviateHandler` module, part of the larger Analitiq framework. This module facilitates interactions with a Weaviate vector database, including loading document chunks and performing searches.

## Table of Contents
1. [Overview](#overview)
2. [Installation Requirements](#installation-requirements)
3. [Quick Start](#quick-start)
4. [Modules](#modules)
    - [Decorators](#decorators)
    - [Chunk Class](#chunk-class)
    - [WeaviateHandler Class](#weaviatehandler-class)
5. [Usage Examples](#usage-examples)
    - [Loading Files](#loading-files)
    - [Searching for Data](#searching-for-data)

## Overview

The `WeaviateHandler` module provides a set of tools for managing and querying a Weaviate vector database. It allows users to load documents, split them into chunks, and perform keyword searches. This module is designed to integrate seamlessly with other parts of the Analitiq framework.

## Installation Requirements

Before using the `WeaviateHandler` module, ensure you have the following software and libraries installed:

- Python 3.6+
- Weaviate Python Client
- Pydantic
- Analitiq Framework

## Quick Start

Here's a simple example demonstrating the basic functionality of the `WeaviateHandler` module:

```python
from analitiq.vectordb.weaviate import WeaviateHandler

params = {
    "project_name": "my_project",
    "host": "https://XXXXXXX.weaviate.network",
    "api_key": "XXXXXX"
}

vdb = WeaviateHandler(params)
FILE_PATH = './project/My_Project/sql'
vdb.load(FILE_PATH, 'sql')
```

## Modules

### Decorators

#### `search_only`

This decorator wraps a function to ensure it only performs search operations.

```python
def search_only(func):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper
```

#### `search_grouped`

This decorator wraps a function to group the search response by document and source.

```python
def search_grouped(func):
    def wrapper(*args, **kwargs):
        response = func(*args, **kwargs)
        self = args[0]
        return self._group_by_document_and_source(response)
    return wrapper
```

### Chunk Class

The `Chunk` class represents a chunk of text in a document.

```python
class Chunk(BaseModel):
    project_name: str = None
    document_name: str = None
    document_type: Optional[str] = None
    content: str = None
    source: str
    document_num_char: int
    chunk_num_char: int
```

### WeaviateHandler Class

The `WeaviateHandler` class handles interactions with a Weaviate cluster and manages a collection within the cluster.

#### Initialization

```python
def __init__(self, params):
    super().__init__(params)
    if not self.try_connect():
        self.connected = False
        self.collection = None
    else:
        multi_collection = self.client.collections.get(self.collection_name)
        self.collection = multi_collection.with_tenant(self.collection_name)
    self.chunk_processor = DocumentChunkLoader(self.collection_name)
```

#### Methods

- **connect**: Connect to the Weaviate database.
- **create_collection**: Create a new collection in Weaviate.
- **close**: Close the Weaviate client connection.
- **_chunk_load_file_or_directory**: Load files from a directory or a single file, split them into chunks, and insert them into Weaviate.
- **load**: Load a file or directory into Weaviate.
- **_group_by_document_and_source**: Group a list of dictionaries by their 'document_name' and 'source'.
- **kw_search**: Perform a keyword search in the Weaviate database.
- **delete_many_like**: Delete multiple documents from the collection where the given property value is similar.
- **get_many_like**: Retrieve objects from the collection that have a property whose value matches the given pattern.
- **delete_collection**: Delete a collection and all its data.

## Usage Examples

### Loading Files

#### Loading all SQL files from a directory

```python
from analitiq.vectordb.weaviate import WeaviateHandler

params = {
    "project_name": "my_project",
    "host": "https://XXXXXXX.weaviate.network",
    "api_key": "XXXXXX"
}

vdb = WeaviateHandler(params)
FILE_PATH = './project/My_Project/sql'
vdb.load(FILE_PATH, 'sql')
```

#### Loading a single file

```python
from analitiq.vectordb.weaviate import WeaviateHandler

params = {
    "project_name": "my_project",
    "host": "https://XXXXXXX.weaviate.network",
    "api_key": "XXXXXX"
}

vdb = WeaviateHandler(params)
FILE_PATH = './project/My_Project/my_file.sql'
vdb.load(FILE_PATH)
```

### Searching for Data

#### Keyword Search

The `kw_search` method performs a keyword search in the database.

```python
search_results = vdb.kw_search("climate change", limit=5)
```

Returned Data Format:

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

#### Grouped Search Results

The `kw_search_grouped` method groups the search results based on their document_name and source.

```python
grouped_results = vdb.kw_search_grouped("sustainable energy", limit=5)
```

Returned Data Format:

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

These functionalities provide an efficient and flexible way to search and analyze documents in the Weaviate database. Whether you need a straightforward list of search results or a grouped view based on specific attributes, the `WeaviateHandler` class caters to both requirements seamlessly.

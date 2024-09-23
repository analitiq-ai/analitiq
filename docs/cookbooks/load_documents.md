
# Loading Documents into Analitiq Cloud Repository

Use the Analitiq application to load documents into your cloud repository to give Analitiq more context to work with and answer questions effectively. Follow the steps below to load documents and utilize the Analitiq capabilities.

## Prerequisites

Make sure you have the necessary parameters:
- **collection_name**: Your collection name (obtained from Analitiq support team)
- **host**: The host address of your Weaviate instance (obtained from Analitiq support team)
- **api_key**: Your API key (obtained from Analitiq support team)

## Code Snippets

### 1. Initialize the Weaviate Handler

```python
from libs.analitiq.vector_databases.weaviate import WeaviateHandler

params = {
    "collection_name": "xxx",
    "host": "xxxxx",
    "api_key": "xxxx"
}

vdb = WeaviateHandler(params)
```

### 2. Load a Directory

To load all files from a directory, use the following code:

```python
# Load a directory
FILE_PATH = '/xxx/xxx/xxx/xxx/models'
vdb.load(FILE_PATH, 'sql')
```

### 3. Load a Single File

To load a single file, use the following code:

```python
# Load a single file
FILE_PATH = '/xxx/xxx/xxx/xxx/models'
vdb.load(FILE_PATH)
```

### 4. Search for Results

To search for specific keywords in your loaded documents, use the following code:

```python
# Search for results
result = vdb.kw_search("bike")
print(result)
```

### 5. Delete a Collection

To delete a collection, use the following code:

```python
# Delete a collection
vdb.delete_collection(params['collection_name'])
```

If you encounter any issues or need assistance, please visit our [Support Page](https://analitiq-app.com/support) or contact us at support@analitiq-app.com.

We are here to help you make the most of your data with Analitiq!

---

Thank you for choosing Analitiq!

**The Analitiq Team**

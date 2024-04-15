# ChromaDB Python API

This code is a Python API for interacting with ChromaDB, a document database designed for storing and retrieving vector data. The API provides functions for saving, deleting, and retrieving documents from a specified collection in ChromaDB.

## Modules

### save_document

This module contains the `save_document` function, which takes in a `ClientAPI` object, a collection name, a document name, and a document metadata object. It then attempts to save the document to the specified collection in ChromaDB. If successful, it returns `True`, otherwise it returns `False`.

### delete_document

This module contains the `delete_document` function, which takes in a `ClientAPI` object, a collection name, and a document name. It then attempts to delete the specified document from the specified collection in ChromaDB. If successful, it returns `True`, otherwise it returns `False`.

### get_document_by_metadata

This module contains the `get_document_by_metadata` function, which takes in a `ClientAPI` object, a collection name, and a metadata object. It then attempts to retrieve a document from the specified collection in ChromaDB that matches the given metadata. If successful, it returns a list of `Vect

from analitiq.logger import logger
import chromadb
import os
from chromadb.api import ClientAPI
from typing import List, Optional
from schemas.vector_store import VectoreStoreCollection


def get_vector_store():
    vector_store = chromadb.HttpClient(
        host=os.getenv("CHROMA_DB_HOST"),
        port=os.getenv("CHROMA_DB_PORT")
    )
    try:
        yield vector_store
    finally:
        del vector_store


class ChromaHandler:

    def save_document(
            client: ClientAPI,
            collection_name: str,
            document_text: str,
            document_metadata: object,
            document_ids: list
    ):
        """
        Saves a document in a specified collection.

        Args:
        - client (ClientAPI): The client interface to interact with the database.
        - collection_name (str): The name of the collection where the document will be saved.
        - document_name (str): The name of the document to be saved.
        - document_metadata (object): The metadata associated with the document.

        Returns:
        - bool: True if the document is saved successfully, False otherwise.
        """
        try:
            collection = client.get_or_create_collection(collection_name)
            response = collection.add(documents=[document_text], metadatas=[document_metadata], ids=document_ids)
            return response
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create document: {e}")
        return False

    def delete_document(client: ClientAPI, collection_name: str, document_uuid: str) -> bool:
        """
        Deletes a document from a specified collection.

        Args:
        - client (ClientAPI): The client interface to interact with the database.
        - collection_name (str): The name of the collection from which the document will be deleted.
        - document_name (str): The name of the document to be deleted.

        Returns:
        - bool: True if the document is deleted successfully, False otherwise.
        """
        try:
            collection = client.get_or_create_collection(collection_name)
            response = collection.delete(ids=[document_uuid])
            return response
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            return False

    def get_document_by_metadata(client: ClientAPI, collection_name: str, metadata: object) -> Optional[list[VectoreStoreCollection]]:
        """
        Retrieves documents from a specified collection based on metadata.

        Args:
        - client (ClientAPI): The client interface to interact with the database.
        - collection_name (str): The name of the collection to query.
        - metadata (object): The metadata used to filter documents.

        Returns:
        - Optional[List[VectoreStoreCollection]]: A list of documents matching the metadata, or None if an error occurs.
        """
        try:
            collection = client.get_or_create_collection(collection_name)
            return collection.get(where=metadata, include=["metadatas"])
        except Exception as e:
            logger.error(f"Error getting document by metadata: {e}")
            return None

    def get_document_by_id(client: ClientAPI, collection_name: str, document_uuid: str) -> Optional[VectoreStoreCollection]:
        """
        Retrieves a document from a specified collection based on its ID.

        Args:
        - client (ClientAPI): The client interface to interact with the database.
        - collection_name (str): The name of the collection to query.
        - document_uuid (str): The UUID of the document to retrieve.

        Returns:
        - Optional[VectoreStoreCollection]: The document with the specified ID, or None if an error occurs.
        """
        try:
            collection = client.get_or_create_collection(collection_name)
            return collection.get(ids=[document_uuid])
        except Exception as e:
            logger.error(f"Error getting document by ID: {e}")
            return None

    def get_all_documents(client: ClientAPI, collection_name: str) -> list[VectoreStoreCollection]:
        """
        Retrieves all documents from a specified collection.

        Args:
        - client (ClientAPI): The client interface to interact with the database.
        - collection_name (str): The name of the collection from which to retrieve documents.

        Returns:
        - List[VectoreStoreCollection]: A list of all documents in the collection.
        """
        collection = client.get_or_create_collection(collection_name)
        return collection.get(include=['documents', 'metadatas'])

    def query(client: ClientAPI, collection_name: str, query: str, num_results: int):
        collection = client.get_or_create_collection(collection_name)
        results = collection.query(
            query_texts=[query],
            n_results=num_results
        )
        return results


import os
import logging
import weaviate
from weaviate.util import generate_uuid5
from weaviate.auth import AuthApiKey
from weaviate.classes.query import Filter
from typing import Optional
from .base_handler import BaseVDBHandler
from ..utils.document_processor import DocumentChunkLoader
from pydantic import BaseModel


def search_only(func):
    """
    A decorator that ensures the function returns only search results.

    Usage:
        @search_only
        def some_search_function(...):
            ...
    """
    def wrapper(*args, **kwargs):
        # Call the original function
        return func(*args, **kwargs)
    return wrapper


def search_grouped(func):
    """
    A decorator that modifies a search function to return results grouped by document and source.

    Usage:
        @grouped_search
        def some_search_function(...):
            ...
    """
    def wrapper(*args, **kwargs):
        # Call the original function
        response = func(*args, **kwargs)
        # Call the grouping function on the response
        self = args[0]  # Assuming the first argument to the function is 'self'
        return self._group_by_document_and_source(response)
    return wrapper


class Chunk(BaseModel):
    """
    Represents a chunk of a document with metadata for insertion into a Weaviate database.

    Attributes:
        project_name: The name of the project the document belongs to.
        document_name: The name of the document.
        document_type: The type of the document, e.g., 'txt', 'pdf'.
        content: The actual content of the chunk.
        source: The source path of the document.
        document_num_char: The number of characters in the original document.
        chunk_num_char: The number of characters in the chunk.
    """
    project_name: str = None
    document_name: str = None
    document_type: Optional[str] = None
    content: str = None
    source: str
    document_num_char: int
    chunk_num_char: int


class WeaviateHandler(BaseVDBHandler):
    """
    A class for interacting with a Weaviate vector database, including loading documents and performing searches.
    """

    def __init__(self, params):
        """
        Initializes a new instance of the class, setting up a connection to a Weaviate cluster and ensuring
        a collection with the specified name exists within that cluster.
        """
        super().__init__(params)
        if not self.try_connect():
            self.connected = False
        self.collection = None

    def connect(self):
        """
        Connect to the Weaviate database.
        """
        self.client = weaviate.connect_to_wcs(
            cluster_url=self.params['host'], auth_credentials=AuthApiKey(self.params['api_key'])
        )

        if not self.client.collections.exists(self.project_name):
            self.client.collections.create(self.project_name)
            logging.info(f"Collection created {self.project_name}")
        self.collection = self.client.collections.get(self.project_name)
        logging.info(f"Vector DB Collection name: {self.project_name}")

    def close(self):
        """
        Close the Weaviate client connection.
        """
        self.client.close()

    def _chunk_load_file_or_directory(self, path: str, extension: Optional[str] = None, chunk_size: int = 2000, chunk_overlap: int = 200):
        """
        Load files from a directory or a single file, split them into chunks, and insert them into Weaviate.
        """
        documents_chunks, doc_lengths = self.chunk_processor.load_and_chunk_documents(path, extension, chunk_size, chunk_overlap)

        chunks = [
            Chunk(
                project_name=self.project_name,
                content=chunk.page_content,
                source=chunk.metadata['source'],
                document_type=extension,
                document_name=os.path.basename(chunk.metadata['source']),
                document_num_char=doc_lengths[chunk.metadata['source']],
                chunk_num_char=len(chunk.page_content)
            ) for chunk in documents_chunks
            ]
        return chunks

        chunks_loaded = 0
        with self.collection.batch.dynamic() as batch:
            for chunk in chunks:
                uuid = generate_uuid5(chunk.dict())
                batch.add_object(properties=chunk.dict(), uuid=uuid)
                chunks_loaded += 1

        self.close()
        print(f"Loaded chunks: {chunks_loaded}")

    def load(self, _path: str, file_ext: str = None):
        """
        Loads a file or directory into Weaviate.
        """
        allowed_extensions = ['py', 'yaml', 'yml', 'sql', 'txt', 'md', 'pdf']  # List of allowed file extensions

        if not os.path.exists(_path):
            raise FileNotFoundError(f"The path {_path} does not exist.")

        if os.path.isdir(_path):
            if file_ext not in allowed_extensions:
                raise ValueError(f"The file extension .{file_ext} is not allowed. Allowed extensions: {allowed_extensions}")
        else:
            file_ext = os.path.splitext(_path)[1][1:]  # Extract the file extension without the dot
            if file_ext not in allowed_extensions:
                raise ValueError(f"The file extension .{file_ext} is not allowed. Allowed extensions: {allowed_extensions}")

        self._chunk_load_file_or_directory(_path, file_ext)

    def _group_by_document_and_source(self, response):
        """
        Groups a list of dictionaries (chunks of data) by their 'document_name' and 'source'.
        """
        grouped_data = {}
        for item in response.objects:
            key = (item.properties['document_name'], item.properties['source'])
            if key in grouped_data:
                grouped_data[key].append(item.properties['content'])
            else:
                grouped_data[key] = [item.properties['content']]

        return grouped_data

    @search_only
    def kw_search(self, query: str, limit: int = 3) -> dict:
        """
        Perform a keyword search in the Weaviate database.
        """
        response = {}
        try:
            response = self.collection.query.bm25(
                query=query,
                query_properties=["content"],
                limit=limit,
                filters=Filter.by_property("project_name").equal(self.project_name)
            )
        except Exception as e:
            logging.error(f"Weaviate error {e}")
        finally:
            self.close()

        logging.info(f"Weaviate search result: {response}")
        return response

    def delete_many_like(self, property_name: str, property_value: str):
        """
        Delete multiple documents from the collection where the given property value is similar.

        :param property_name: The name of the property to filter by.
        :param property_value: The value of the property to match.
        :return: True if the documents are successfully deleted, False otherwise.
        """
        try:
            self.collection.data.delete_many(
                where=Filter.by_property(property_name).like(f"{property_value}*")
            )
            return True
        except Exception as e:
            logging.error(f"Error deleting documents: {e}")
            return False
        finally:
            self.close()

    def get_many_like(self, property_name: str, property_value: str):
        """
        Retrieve objects from the collection that have a property whose value matches the given pattern.
        Example:
        response = vector_db_client.get_many_like("document_name", "schema")

        :param property_name: The name of the property used for filtering.
        :param property_value: The value used as a pattern to match against the property value.
        :return: A list of objects that have a property matching the pattern.
        :rtype: list or None
        """
        try:
            response = self.collection.query.fetch_objects(
                filters=Filter.by_property("source").like(f"*{property_value}*")
            )
            return response
        except Exception as e:
            logging.error(f"Error retrieving documents: {e}")
            return None
        finally:
            self.close()

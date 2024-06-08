import os
from ..logger import logger
import weaviate
from weaviate.util import generate_uuid5
from weaviate.auth import AuthApiKey
from weaviate.classes.query import Filter
from weaviate.classes.config import Configure
from weaviate.classes.tenants import Tenant
from typing import Optional
from .base_handler import BaseVDBHandler
from ..utils.document_processor import DocumentChunkLoader
from pydantic import BaseModel


def search_only(func):
    """
    :param func: the function to be wrapped
    :return: the result of the original function

    This method wraps the given function and returns a wrapper function. The wrapper function calls the original function with the given parameters and returns the result.
    """
    def wrapper(*args, **kwargs):
        # Call the original function
        return func(*args, **kwargs)
    return wrapper


def search_grouped(func):
    """
    :param func: The function to be wrapped and executed.
    :return: The result of calling the original function after grouping the response.
    """
    def wrapper(*args, **kwargs):
        # Call the original function
        response = func(*args, **kwargs)
        # Call the grouping function on the response
        self = args[0]  # Assuming the first argument to the function is 'self'
        return self._group_by_document_and_source(response)
    return wrapper


class Chunk(BaseModel):
    """Represents a chunk of text in a document.

    :param project_name: The name of the project the chunk belongs to.
    :type project_name: str
    :param document_name: The name of the document the chunk belongs to.
    :type document_name: str
    :param document_type: The type of the document. (optional)
    :type document_type: str, optional
    :param content: The content of the chunk.
    :type content: str
    :param source: The source of the chunk.
    :type source: str
    :param document_num_char: The number of characters in the document.
    :type document_num_char: int
    :param chunk_num_char: The number of characters in the chunk.
    :type chunk_num_char: int
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
    :class: WeaviateHandler(BaseVDBHandler)

    Class for handling interactions with a Weaviate cluster and managing a collection within the cluster.

    .. automethod:: __init__
    .. automethod:: connect
    .. automethod:: create_collection
    .. automethod:: close
    .. automethod:: _chunk_load_file_or_directory
    .. automethod:: load
    .. automethod:: _group_by_document_and_source
    .. automethod:: kw_search
    .. automethod:: delete_many_like
    .. automethod:: get_many_like
    .. automethod:: delete_collection
    """

    def __init__(self, params):
        """
        Initializes a new instance of the class, setting up a connection to a Weaviate cluster and ensuring
        a collection with the specified name exists within that cluster.
        """
        super().__init__(params)
        self.logger = logger
        if not self.try_connect():
            self.connected = False
            self.collection = None
        else:
            multi_collection = self.client.collections.get(self.collection_name)
            # Get collection specific to the required tenant
            self.collection = multi_collection.with_tenant(self.collection_name)

        self.chunk_processor = DocumentChunkLoader(self.collection_name)

    def connect(self):
        """
        Connect to the Weaviate database.
        """
        self.client = weaviate.connect_to_wcs(
            cluster_url=self.params['host'], auth_credentials=AuthApiKey(self.params['api_key'])
        )

        if not self.client.collections.exists(self.collection_name):
            self.create_collection()
            logger.info(f"Collection created {self.collection_name}")
        else:
            logger.info(f"Existing VDB Collection name: {self.collection_name}")

    def create_collection(self):

        self.client.collections.create(self.collection_name,
                                       # Enable multi-tenancy on the new collection
                                       multi_tenancy_config=Configure.multi_tenancy(enabled=True))

        self.collection = self.client.collections.get(self.collection_name)

        # Add a tenant to the collection. Right now the tenant is the same as the collection. In the future, this could be users
        self.collection.tenants.create(
            tenants=[
                Tenant(name=self.collection_name)
            ]
        )

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
                content=chunk.page_content,
                source=chunk.metadata['source'],
                document_type=extension,
                document_name=os.path.basename(chunk.metadata['source']),
                document_num_char=doc_lengths[chunk.metadata['source']],
                chunk_num_char=len(chunk.page_content)
            ) for chunk in documents_chunks
            ]

        chunks_loaded = 0

        with self.collection.batch.dynamic() as batch:
            for chunk in chunks:
                uuid = generate_uuid5(chunk.model_dump())
                batch.add_object(properties=chunk.model_dump(), uuid=uuid)
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
                limit=limit
            )
        except Exception as e:
            logger.error(f"Weaviate error {e}")
        finally:
            self.close()

        logger.info(f"Weaviate search result: {response}")
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
            logger.error(f"Error deleting documents: {e}")
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
            logger.error(f"Error retrieving documents: {e}")
            return None
        finally:
            self.close()

    def delete_collection(self, collection_name: str):
        # delete collection - THIS WILL DELETE THE COLLECTION AND ALL ITS DATA
        try:
            self.client.collections.delete(collection_name)
            return True
        except Exception:
            return False
        finally:
            self.close()

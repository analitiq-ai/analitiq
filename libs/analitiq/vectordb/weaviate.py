from typing import Optional, List, Tuple

import os
from ..logger import logger
import weaviate
from weaviate.util import generate_uuid5
from weaviate.auth import AuthApiKey
from weaviate.classes.query import Filter, MetadataQuery
from weaviate.classes.config import Configure
from weaviate.classes.tenants import Tenant
from weaviate.collections.classes.internal import QueryReturn

from .base_handler import BaseVDBHandler
from ..utils.document_processor import DocumentChunkLoader
from ..schemas.vector_store import DocChunk

from analitiq.vectordb import vectorizer

ALLOWED_EXTENSIONS = ['py', 'yaml', 'yml', 'sql', 'txt', 'md', 'pdf']
LOAD_DOC_CHUNK_SIZE = 2000
LOAD_DOC_CHUNK_OVERLAP = 200
VECTOR_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

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
        if not self.try_connect():
            self.connected = False
            self.collection = None
        else:
            multi_collection = self.client.collections.get(self.collection_name)
            # Get collection specific to the required tenant
            self.collection = multi_collection.with_tenant(self.collection_name)

        self.vectorizer = vectorizer.AnalitiqVectorizer(VECTOR_MODEL_NAME)

        self.chunk_processor = DocumentChunkLoader(self.collection_name)

    def connect(self):
        """
        Connect to the Weaviate database.
        """
        self.client: weaviate.classes = weaviate.connect_to_wcs(
            cluster_url=self.params['host'], auth_credentials=AuthApiKey(self.params['api_key'])
        )

        if not self.client.collections.exists(self.collection_name):
            self.create_collection()
            logger.info(f"Collection created {self.collection_name}")
        else:
            logger.info(f"Existing VDB Collection name: {self.collection_name}")

    def create_collection(self):
        """Create a collection if not existing."""
        self.client.collections.create(self.collection_name,
                                       # enable multi_tenancy_config                                       
                                       multi_tenancy_config=Configure.multi_tenancy(enabled=True),
                                       # vectorizer_config=Configure.Vectorizer.text2vec_cohere(),
        )

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

    def _chunk_load_file_or_directory(self, path: str, extension: Optional[str] = None, chunk_size: int = LOAD_DOC_CHUNK_SIZE, chunk_overlap: int = LOAD_DOC_CHUNK_OVERLAP):
        """
        Load files from a directory or a single file, split them into chunks, and insert them into Weaviate.
        """
        documents_chunks, doc_lengths = self.chunk_processor.load_and_chunk_documents(path, extension, chunk_size, chunk_overlap)

        chunks = [
            DocChunk(
                content=chunk.page_content,
                source=chunk.metadata['source'],
                document_type=extension,
                document_name=os.path.basename(chunk.metadata['source']),
                document_num_char=doc_lengths[chunk.metadata['source']],
                chunk_num_char=len(chunk.page_content),
            ) for chunk in documents_chunks
            ]

        chunks_loaded = 0

        with self.collection.batch.dynamic() as batch:
            for chunk in chunks:
                uuid = generate_uuid5(chunk.model_dump())
                hf_vector = self.vectorizer.vectorize(chunk.content)
                batch.add_object(properties=chunk.model_dump(), uuid=uuid, vector=hf_vector)
                chunks_loaded += 1

        self.close()
        print(f"Loaded chunks: {chunks_loaded}")

    def load(self, _path: str, file_ext: str = None):
        """
        Load method

        Loads a file or directory into Weaviate.

        :param _path: The path of the file or directory to be loaded.
        :param file_ext: The file extension of the files to be loaded. If None, all files in the directory will be loaded.
        :return: None

        Raises:
            FileNotFoundError: If the specified path does not exist.
            ValueError: If the file extension is not allowed.

        """

        if not os.path.exists(_path):
            raise FileNotFoundError(f"The path {_path} does not exist.")

        error_msg = f"The file extension .{file_ext} is not allowed. Allowed extensions: {ALLOWED_EXTENSIONS}"

        if os.path.isdir(_path):
            if file_ext not in ALLOWED_EXTENSIONS:
                raise ValueError(error_msg)
        else:
            file_ext = os.path.splitext(_path)[1][1:]  # Extract the file extension without the dot
            if file_ext not in ALLOWED_EXTENSIONS:
                raise ValueError(error_msg)

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
    def kw_search(self, query: str, limit: int = 3) -> QueryReturn:
        """
        Perform a keyword search in the Weaviate database.
        """
        response = QueryReturn(objects=[])
        try:
            response: QueryReturn = self.collection.query.bm25(
                query=query,
                query_properties=["content"],
                return_metadata=MetadataQuery(score=True, distance=True),
                limit=limit
            )
        except Exception as e:
            logger.error(f"Weaviate error {e}")
        finally:
            self.close()

        logger.info(f"Weaviate search result: {response}")
        return response
    
    @search_only
    def hybrid_search(self, query: str, limit: int = 3) -> QueryReturn:
        """
        Perform a hybrid search by combining keyword-based search and vector-based search.

        :param query: The query string used for searching.
        :param limit: The maximum number of results to return. Default is 3.
        :return: A dictionary containing the search results.

        :raises Exception: If there is an error during the search.

        """
        response = QueryReturn(objects=[])
        try:
            kw_results = self.kw_search(query, limit)
            self.client.connect()
            vector_results = self.vector_search(query, limit)
            
            response = self.combine_and_rerank_results(kw_results, vector_results)
        except Exception as e:
            logger.error(f"Weaviate error {e}")
            raise e
        finally:
            self.close()

        logger.info(f"Weaviate search result: {response}")
        return response
    
    def vector_search(self, query: str, limit: int = 3) -> QueryReturn:
        """
        :param query: A string representing the query to be performed.
        :param limit: An optional integer representing the maximum number of results to return. Default value is 3.
        :return: A QueryReturn object containing the search results.

        This method performs a vector search using the Weaviate API. It takes a query string and an optional limit parameter to specify the maximum number of results to return. The method returns
        * a QueryReturn object which contains the search results.

        Example usage:
        ```
        # create an instance of the class
        search_engine = SearchEngine()

        # perform a vector search with a limit of 5 results
        results = search_engine.vector_search("example query", limit=5)

        # process the search results
        for result in results:
            print(result)
        ```
        """
        response = QueryReturn(objects=[])
        try:
            query_vector = self.vectorizer.vectorize(query)
            response: QueryReturn = self.collection.query.near_vector(
                    near_vector=query_vector,
                    limit=limit,
                    return_metadata=MetadataQuery(distance=True, score=True)
            )
        except Exception as e:
            logger.error(f"Weaviate error {e}")
        finally:
            self.close()

        logger.info(f"Weaviate search result: {response}")
        return response

    def combine_and_rerank_results(self, kw_results: QueryReturn, vector_results: QueryReturn, limit: int = 3,
                                    kw_vector_weights: Tuple[float, float] =[0.3, 0.7]) -> List[dict]:
        """
        Combine and rerank keyword search and vector search results.

        :param kw_results: Keyword search results.
        :type kw_results: QueryReturn
        :param vector_results: Vector search results.
        :type vector_results: QueryReturn
        :param limit: Number of results to return.
        :type limit: int, optional
        :param kw_vector_weights: Weights for keyword and vector search results, default is [0.3, 0.7].
        :type kw_vector_weights: Tuple[float, float], optional
        :return: Reranked results.
        :rtype: List[dict]
        """
        combined = {}

        vector_weight = kw_vector_weights[1]
        kw_weight = kw_vector_weights[0]

        # Assign ranks to keyword search results
        for rank, result in enumerate(kw_results.objects, start=1):
            uuid = result.uuid
            if uuid not in combined:
                combined[uuid] = {"result": result, "score": 0}
            combined[uuid]["score"] += kw_weight * (1 / (60 + rank))
        # Assign ranks to vector search results
        for rank, result in enumerate(vector_results.objects, start=1):
            uuid = result.uuid
            if uuid not in combined:
                combined[uuid] = {"result": result, "score": 0}
            combined[uuid]["score"] += vector_weight * (1 / (60 + rank))

        # Convert the combined dictionary to a list and sort by score
        combined_list = sorted(combined.values(), key=lambda x: x["score"], reverse=True)

        # Extract only the results (up to the specified limit)
        reranked_results = [item["result"] for item in combined_list[:limit]]
        
        return QueryReturn(objects=reranked_results)

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

    def update_vectors(self):
        """Update the Vectors in your database for existing entries."""
        updated_count = 0
        try:
            all_objects = self.collection.query.fetch_objects(
                filters=None  # Fetch all objects without any filters
            )

            # Iterate over all objects and update vectors
            for obj in all_objects.objects:
                content = obj.properties['content']
                uuid = obj.uuid

                # Re-vectorize the content
                new_vector = self.vectorizer.vectorize(content)

                # Update the object in the collection with the new vector
                self.collection.data.update(
                    uuid=uuid,
                    vector=new_vector
                )
            updated_count += 1

            logger.info(f"Successfully updated vectors for {updated_count} entries.")
        except Exception as e:
            logger.error(f"Error updating vectors: {e}")
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

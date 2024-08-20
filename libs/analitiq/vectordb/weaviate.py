from typing import Optional, List, Tuple, Dict, Any
import os
import pathlib
from functools import reduce
from datetime import datetime, timezone

from pydantic import BaseModel

import weaviate
import weaviate.util
from weaviate.util import generate_uuid5
from weaviate.auth import AuthApiKey
from weaviate.classes.query import Filter, MetadataQuery
from weaviate.classes.config import Configure
from weaviate.classes.tenants import Tenant
from weaviate.classes.aggregate import GroupByAggregate
from weaviate.collections.classes.internal import QueryReturn

from analitiq.logger.logger import logger
from analitiq.vectordb import keyword_extractions
from analitiq.vectordb.base_handler import BaseVDBHandler
from analitiq.utils.document_processor import DocumentChunkLoader


from analitiq.vectordb import vectorizer

ALLOWED_EXTENSIONS = ["py", "yaml", "yml", "sql", "txt", "md", "pdf"]
LOAD_DOC_CHUNK_SIZE = 2000
LOAD_DOC_CHUNK_OVERLAP = 200
VECTOR_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
QUERY_PROPERTIES = ["content"]  # OR content_kw


def search_only(func):
    """Search Only functions.

    This method wraps the given function and returns a wrapper function.
    The wrapper function calls the original function with the given parameters and returns the result.
    """

    def wrapper(*args, **kwargs):
        # Call the original function
        return func(*args, **kwargs)

    return wrapper


def search_grouped(func):
    """Search a Batch function."""

    def wrapper(*args, **kwargs):
        """Wrap the function."""
        response = func(*args, **kwargs)
        self = args[0]
        return self._group_results_by_properties(response, ["document_name", "source"])

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
    :param content_kw: the keywords for keyword search in the chunks
    :type content_kw: str
    """

    project_name: str
    document_name: str
    document_type: Optional[str] = None
    content: str
    source: str
    date_loaded: Optional[datetime] = None
    document_num_char: int
    chunk_num_char: int
    content_kw: str


class WeaviateHandler(BaseVDBHandler):
    """The WeaviateHandler Class manages interactions with a Weaviate Vector Database.

    This class provides methods to connect to a Weaviate cluster, manage collections,
    load and chunk documents, and perform various types of searches and data manipulations.
    """

    def __init__(self, params):
        """Initialize a new instance of class."""
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
        """Connect to the Weaviate database."""
        self.client: weaviate.WeaviateClient = weaviate.connect_to_wcs(
            cluster_url=self.params["host"], auth_credentials=AuthApiKey(self.params["api_key"])
        )

        if not self.client.collections.exists(self.collection_name):
            self.create_collection()
            logger.info(f"Collection created {self.collection_name}")
        else:
            logger.info(f"Existing VDB Collection name: {self.collection_name}")

    def create_collection(self):
        """Create a collection if not existing."""
        self.client.collections.create(
            self.collection_name,
            # enable multi_tenancy_config
            multi_tenancy_config=Configure.multi_tenancy(enabled=True),
        )

        self.collection = self.client.collections.get(self.collection_name)

        # Add a tenant to the collection. Right now the tenant is the same as the collection.
        # In the future, this could be users
        self.collection.tenants.create(tenants=[Tenant(name=self.collection_name)])

    def close(self):
        """Close the Weaviate client connection."""
        self.client.close()

    def _chunk_load_file_or_directory(
        self,
        path: str,
        extension: Optional[str] = None,
        chunk_size: int = LOAD_DOC_CHUNK_SIZE,
        chunk_overlap: int = LOAD_DOC_CHUNK_OVERLAP,
    ):
        """Chunk the data from file or directory.

        Load files from a directory or a single file,
        split them into chunks, and insert them into Weaviate.
        """
        documents_chunks, doc_lengths = self.chunk_processor.load_and_chunk_documents(
            path, extension, chunk_size, chunk_overlap
        )

        chunks = [
            Chunk(
                content=chunk.page_content,
                source=chunk.metadata["source"],
                document_type=extension,
                document_name=pathlib.Path(chunk.metadata["source"]).name,
                document_num_char=doc_lengths[chunk.metadata["source"]],
                chunk_num_char=len(chunk.page_content),
                date_loaded=datetime.now(timezone.utc),
                content_kw=keyword_extractions.extract_keywords(chunk.page_content),
            )
            for chunk in documents_chunks
        ]

        self.load_chunks_to_weaviate(chunks)

    def _chunk_text(
        self,
        text,
        document_name,
        document_type: str = "txt",
        chunk_size: int = LOAD_DOC_CHUNK_SIZE,
        chunk_overlap: int = LOAD_DOC_CHUNK_OVERLAP,
    ):
        """Chunk the given text into smaller chunks and load them to Weaviate.

        :param text: The text to be chunked.
        :param document_name: The name of the document.
        :param document_type: The type of the document. Default is 'txt'.
        :return: None
        """
        documents_chunks = self.chunk_processor.chunk_text(text, chunk_size, chunk_overlap)

        chunks = [
            Chunk(
                content=chunk,
                source="loaded_text",
                document_type=document_type,
                document_name=document_name,
                document_num_char=len(text),
                chunk_num_char=len(chunk),
                date_loaded=datetime.now(timezone.utc),
                content_kw=keyword_extractions.extract_keywords(chunk.page_content),
            )
            for chunk in documents_chunks
        ]

        self.load_chunks_to_weaviate(chunks)

    @staticmethod
    def load_list_to_chunk(chunk: str, metadata: dict):
        """Load a list to chunks."""
        return Chunk(
            content=chunk,
            source=metadata["source"],
            document_type=metadata["document_type"],
            document_name=metadata["document_name"],
            document_num_char=len(chunk),
            chunk_num_char=len(chunk),
            date_loaded=datetime.now(timezone.utc),
            content_kw=keyword_extractions.extract_keywords(chunk),
        )

    def load_chunks_to_weaviate(self, chunks):
        """Load chunks into weaviate."""
        chunks_loaded = 0

        try:
            self.client.connect()
        except Exception as e:
            logger.error(e)

        with self.collection.batch.dynamic() as batch:
            for chunk in chunks:
                uuid = generate_uuid5(chunk.model_dump())
                hf_vector = self.vectorizer.vectorize(chunk.content)
                response = batch.add_object(properties=chunk.model_dump(), uuid=uuid, vector=hf_vector)
                logger.info(response)
                chunks_loaded += 1

        self.close()
        logger.info("Loaded chunks: %s", chunks_loaded)

    def load(self, _path: str, file_ext: Optional[str] = None):
        """Load method.

        :param _path: The path of the file or directory to be loaded.
        :param file_ext: The file extension of the files to be loaded.
        If None, all files in the directory will be loaded.

        Raises
        ------
            FileNotFoundError: If the specified path does not exist.
            ValueError: If the file extension is not allowed.

        """
        if not os.path.exists(_path):
            msg = f"The path {_path} does not exist."
            raise FileNotFoundError(msg)

        error_msg = f"The file extension .{file_ext} is not allowed. Allowed extensions: {ALLOWED_EXTENSIONS}"

        if os.path.isdir(_path):
            if file_ext not in ALLOWED_EXTENSIONS:
                raise ValueError(error_msg)
        else:
            file_ext = os.path.splitext(_path)[1][1:]  # Extract the file extension without the dot
            if file_ext not in ALLOWED_EXTENSIONS:
                raise ValueError(error_msg)

        self._chunk_load_file_or_directory(_path, file_ext)

    @staticmethod
    def _group_results_by_properties(results: QueryReturn, group_by_properties: list) -> list:
        """Groups a list of dictionaries (chunks of data) by given keys and return the grouped data as a list of dictionaries.

        Each dictionary in the returned list corresponds to a unique group as determined by `group_by_properties`. The keys of the
        dictionaries are the group properties and a special key 'document_chunks' which stores the associated chunks of data.

        Args:
        ----
            results (Response): The original response object that includes 'objects' which is
                a list of items, each having properties from which keys values are extracted.
            group_by_properties (list[str]): List of properties which are used to group data.

        Raises:
        ------
            ValueError: If any key in `group_keys` is not in `allowed_keys`.

        Returns:
        -------
            list[dict] : List of dictionaries. Each dictionary corresponds to a unique group.
            The keys of the dictionaries are the group keys and 'document_chunks' which stores
            the associated chunks of data.

        Example:
        -------
            Given group_keys=['document_name', 'source'] and this item in `response.objects`:

            { 'properties' :
               { 'document_name': 'doc1', 'source' : 'src1', 'content': 'content1' }
            } ...

            The output will be:

            [
                {
                   "document_name": "doc1",
                   "source": "src1",
                   "document_chunks": ['content1', ...]
                },
               ...
            ]

        """
        if not results.objects:
            return None

        allowed_keys = list(Chunk.__annotations__.keys())

        if not set(group_by_properties).issubset(set(allowed_keys)):
            msg = f"The provided keys for grouping are not allowed. Allowed keys are: {allowed_keys}"
            raise ValueError(msg)

        grouped_data = {}
        # put all chunks into the same key.
        for item in results.objects:
            key = tuple(item.properties[k] for k in group_by_properties)
            if key in grouped_data:
                grouped_data[key].append(item.properties["content"])
            else:
                grouped_data[key] = [item.properties["content"]]

        # format the data into more explicit dictionary
        reformatted_data = []
        for key, value in grouped_data.items():
            data_dict = {"document_chunks": value}
            # key is a tuple, so we use enumerate to get indexes and use them to fetch property names
            for idx, item in enumerate(key):
                data_dict[group_by_properties[idx]] = item
            reformatted_data.append(data_dict)
        return reformatted_data

    @search_only
    def kw_search(self, query: str, limit: int = 3) -> QueryReturn:
        """Perform a keyword search in the Weaviate database."""
        search_kw = keyword_extractions.extract_keywords(query)
        logger.info("Extracted keywords to search for: %s", search_kw)
        response = QueryReturn(objects=[])
        try:
            response: QueryReturn = self.collection.query.bm25(
                query=search_kw,
                query_properties=QUERY_PROPERTIES,
                return_metadata=MetadataQuery(score=True, distance=True),
                limit=limit,
            )

        except Exception as e:
            logger.error(f"Weaviate error {e}")
        finally:
            self.close()
        # logger.info(f"Weaviate Keyword search result: {response}")
        return response

    @search_only
    def hybrid_search(self, query: str, limit: int = 3) -> QueryReturn:
        """Use Hybrid Search for document retrieval from Weaviate Database.

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

        # logger.info(f"Weaviate Hybrid search result: {response}")
        return response

    def vector_search(self, query: str, limit: int = 3) -> QueryReturn:
        """Use Vector Search for document retrieval from Weaviate Database.

        :param query: A string representing the query to be performed.
        :param limit: An optional integer representing the maximum number of results to return.
        Default value is 3.
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
                return_metadata=MetadataQuery(distance=True, score=True),
            )
        except Exception as e:
            logger.error(f"Weaviate error {e}")
        finally:
            self.close()

        # logger.info(f"Weaviate vector search result: {response}")
        return response

    @staticmethod
    def combine_and_rerank_results(
        kw_results: QueryReturn,
        vector_results: QueryReturn,
        limit: int = 3,
        kw_vector_weights: Tuple[float, float] = [0.3, 0.7],
    ) -> List[dict]:
        """Combine and rerank keyword search and vector search results.

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
        if not kw_results.objects:
            return None

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

    def delete_many_like(self, properties: Dict[str, Any], match_type: str = "like"):
        """Delete multiple documents from the collection where the given property value is similar.

        :param properties: The name of the property to filter by.
        :param match_type: The type of match for properties
        :return: True if the documents are successfully deleted, False otherwise.
        """
        filters = self._create_filters(properties, match_type)

        try:
            self.collection.data.delete_many(
                where=(filters[0] if len(filters) == 1 else reduce(lambda a, b: a & b, filters)),
            )
            return True
        except Exception as e:
            logger.error(f"Error deleting documents: {e}")
            return False
        finally:
            self.close()

    def search_vdb_ddl(self, query: str, schemas: list):
        """Retrieve matches to the query string for DDl definition from VDB.

        Example:
        -------
        response = vector_db_client.get_many_like("document_name", "schema")

        :param query: The search string.
        :param properties: The name of the property used for filtering.
        :param match_type: the type of match to use for properties
        :return: A list of objects that have a property matching the pattern.
        :rtype: list or None

        """
        try:
            self.client.connect()
        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")

        try:
            query_vector = self.vectorizer.vectorize(query)

            response: QueryReturn = self.collection.query.near_vector(
                near_vector=query_vector,
                filters=(
                    Filter.any_of([Filter.by_property("document_name").like(schema) for schema in schemas])
                    & Filter.by_property("document_type").equal("ddl")
                ),
                limit=10,
                return_metadata=MetadataQuery(distance=True, score=True),
            )

        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")
            return None
        finally:
            self.close()

        if not response.objects:
            return None
        else:
            return self._group_results_by_properties(response, ["document_name"])

    def search_vdb_with_filter(self, query: str, properties: Dict[str, Any], match_type: str = "like"):
        """Retrieve objects from the collection that have a property whose value matches the given pattern.

        Example:
        -------
        response = vector_db_client.get_many_like("document_name", "schema")

        :param query: The search string.
        :param properties: The name of the property used for filtering.
        :param match_type: the type of match to use for properties
        :return: A list of objects that have a property matching the pattern.
        :rtype: list or None

        """
        try:
            self.client.connect()
        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")

        try:
            query_vector = self.vectorizer.vectorize(query)

            filters = self._create_filters(properties, match_type)

            response: QueryReturn = self.collection.query.near_vector(
                near_vector=query_vector,
                filters=(filters[0] if len(filters) == 1 else reduce(lambda a, b: a & b, filters)),
                limit=10,
                return_metadata=MetadataQuery(distance=True, score=True),
            )

        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")
            return None
        finally:
            self.close()

        if not response.objects:
            return None
        return self._group_results_by_properties(response, ["document_name", "document_type"])

    def fetch_objects_by_properties(self, properties: Dict[str, Any], match_type: str = "like"):
        """Fetch objects with given properties."""
        response = None

        try:
            self.client.connect()
        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")

        filters = self._create_filters(properties, match_type)

        response = self.collection.query.fetch_objects(
            filters=(filters[0] if len(filters) == 1 else reduce(lambda a, b: a & b, filters)), limit=5
        )

        self.close()
        return response

    def count_objects_by_properties(self, properties: Dict[str, Any], match_type: str = "like"):
        """Count objects by properties."""
        try:
            self.client.connect()
        except Exception as e:
            logger.error(f"Error connecting to Weaviate: {e}")
            return None

        filters = self._create_filters(properties, match_type)

        response = self.collection.aggregate.over_all(
            total_count=True,
            filters=(filters[0] if len(filters) == 1 else reduce(lambda a, b: a & b, filters)),
        )

        self.close()

        return response

    def get_by_uuid(self, uuid: str):
        """Get entrys by uuid."""
        return self.collection.query.fetch_object_by_id(uuid=uuid)

    def delete_objects(self, properties: Dict[str, Any], match_type: str = "like"):
        """Delete objects from the collection based on specified meta parameters.

        :param properties: The properties used to filter the objects to be deleted.
        :param match_type: The type of matching to perform. Defaults to 'like'.
        :type match_type: str Can be either 'like' or 'strict'
        """
        try:
            filters = self._create_filters(properties, match_type)

            self.collection.data.delete_many(
                where=(filters[0] if len(filters) == 1 else reduce(lambda a, b: a & b, filters)),
                verbose=True,
                dry_run=False,
            )

        finally:
            self.client.close()

    def delete_collection(self, collection_name: str):
        """Delete collection.

        THIS WILL DELETE THE COLLECTION AND ALL ITS DATA.
        """
        try:
            self.client.collections.delete(collection_name)
            return True
        except Exception:
            return False
        finally:
            self.close()

    @staticmethod
    def _create_filters(properties: Dict[str, Any], match_type: str):
        """Create filter for filtering the datasets."""
        if match_type == "like":
            filters = [Filter.by_property(name).like(value) for name, value in properties.items()]
        else:
            filters = [Filter.by_property(name).equal(value) for name, value in properties]

        return filters

    def get_all_objects(self) -> dict:
        """Retrieve all objects from the collection.

        :return: A list of dictionaries representing the objects.
        :rtype: dict
        """
        try:
            self.client.connect()
        except Exception as e:
            logger.error(f"Error connecting to Weaviate: {e}")
            return None

        docs = {}

        try:
            for item in self.collection.iterator():
                docs[item.uuid] = item.properties
            self.collection.iterator()
        finally:
            self.client.close()

        return docs

    def count_objects_grouped_by(self, group_by_property: str) -> List[dict]:
        """Count objects in Weaviate and group them by the specified property.

        :param group_by_property: The property to group by.
        :return: A list of dictionaries with the group property and count.
        """
        try:
            self.client.connect()
        except Exception as e:
            logger.error(f"Error connecting to Weaviate: {e}")
            return None

        try:
            response = self.collection.aggregate.over_all(
                group_by=GroupByAggregate(prop=group_by_property), total_count=True
            )

        finally:
            self.client.close()

        return response

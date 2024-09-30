# File: databases/vector/weaviate/weaviate_connector.py

import logging
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta, timezone
import weaviate
from weaviate.auth import AuthApiKey
from weaviate.util import generate_uuid5
from weaviate.collections.classes.tenants import Tenant
from weaviate.collections.classes.aggregate import AggregateGroupByReturn
from weaviate.classes.config import Configure
from weaviate.classes.query import MetadataQuery
from weaviate.classes.aggregate import GroupByAggregate
from analitiq.base.base_vector_database import BaseVectorDatabase
from analitiq.databases.vector.weaviate.query_builder import QueryBuilder
from analitiq.utils.document_processor import (
    DocumentProcessor,
    group_results_by_properties,
)
from analitiq.utils.keyword_extractions import extract_keywords
from analitiq.utils.document_processor import string_to_chunk
from analitiq.databases.vector.utils.analitiq_vectorizer import AnalitiqVectorizer
from weaviate.collections.classes.internal import QueryReturn

logger = logging.getLogger(__name__)

VECTOR_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
QUERY_PROPERTIES = ["content"]  # Adjust as needed


def search_only(func):
    """A decorator for wrapping database search functions.

    This function takes as input another function ('func') and returns a new function that wraps the original one.
    The main purpose of this decorator is to apply some before and/or after processing to the function that it is decorating.

    It can be used to encapsulate operations that need to be performed before a search is made to the database,
    like opening a connection or logging, as well as operations that should be executed once the database search is completed
    (like closing the connection to the database).

    Parameters
    ----------
    func : callable
        The function to be wrapped. This is typically a database search function.

    Returns
    -------
    callable
        A new function that wraps the original one. This new function takes the same
        parameters as the original one and returns its result.

    Note
    ----
    - The output function (wrapper) applies the original function (func) to the provided arguments ('args' tuple and 'kwargs' dictionary),
      which means every single positional and keyword argument passed to it will actually be passed to the function being decorated.

    Examples
    --------
    >>> @search_only
    ... def my_search_function(query):
    ...     # Perform database search
    ...     # And return result.
    ...     pass

    Here, the function `my_search_function` is decorated with `search_only` function which will add pre-processing
    and/or post-processing steps to the execution of `my_search_function` when it's called.

    """

    def wrapper(*args, **kwargs):
        # Call the original function
        return func(*args, **kwargs)

    return wrapper


# Define a reusable search method that encapsulates the common logic
def search_and_handle_errors(search_func, *args, logger, **kwargs):
    """
    Executes the given search function, handles any errors that occur, and logs them.

    :param search_func: The search function to execute.
    :param args: Additional positional arguments to pass to the search function.
    :param logger: The logger to use for logging any errors.
    :param kwargs: Additional keyword arguments to pass to the search function.
    :return: The result of the search function.
    :raises: Any exception that occurs during the search.
    """
    try:
        return search_func(*args, **kwargs)
    except weaviate.exceptions.WeaviateQueryError as e:
        if 'tenant not found' in str(e) or 'no such prop' in str(e) :
            logger.warning(str(e))
            return QueryReturn(objects=[])
        else:
            raise e
    except Exception as e:
        logger.error(f"Error during search: {e}")
        raise e


class WeaviateConnector(BaseVectorDatabase):
    """The WeaviateConnector Class manages interactions with a Weaviate Vector Database.

    This class provides methods to connect to a Weaviate cluster, manage collections,
    load and chunk documents, and perform various types of searches and data manipulations,
    including multi-tenancy support.
    """

    def __init__(self, params):
        """Initialize a new instance of WeaviateConnector.

        Parameters
        ----------
        **kwargs : dict
            Dictionary of parameters including 'host', 'api_key', 'collection_name', and 'tenant_name'.

        """
        super().__init__(params)
        self.params = params
        self.collection_name = self.params.get("collection_name", "default_collection")
        self.connected = False
        self.client = None
        self.vectorizer = AnalitiqVectorizer(VECTOR_MODEL_NAME)
        self.connect()

    def __enter__(self):
        """Context manager entry: establish connection to Weaviate.
        """
        if not self.connected:
            self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Context manager exit: ensure the connection is closed.
        """
        self.close()

    def connect(self):
        """Connect to the Weaviate database.

        Establishes a connection to the Weaviate client using the provided host and API key.
        If the specified collection does not exist, it creates one with multi-tenancy enabled.
        It also ensures that the specified tenant exists within the collection.

        Raises
        ------
        Exception
            If connection to Weaviate fails.

        """
        try:
            self.client = weaviate.connect_to_weaviate_cloud(
                cluster_url=self.params["host"],
                auth_credentials=AuthApiKey(self.params["api_key"]),
            )
            self.connected = True

        except Exception as e:
            logger.error(f"Failed to connect to Weaviate: {e}")
            self.connected = False
            raise

    def close(self):
        """Close the connection to the Weaviate database.

        Sets the client to None and updates the connection status.
        """
        if self.connected and self.client:
            self.client.close()
            self.connected = False
            logger.info("Closed connection to Weaviate")

    def __get_tenant_collection_object(self) -> object:
        """Returns the tenant-specific collection object for multi-tenancy.

        Parameters
        ----------
        collection_name : str
            The name of the collection.
        tenant_name : str
            The tenant name within the collection.

        Returns
        -------
        object
            The collection object specific to the tenant.

        """
        tenant_name = self.params.get("tenant_name")
        collection_name = self.params.get("collection_name", "default_collection")
        logger.info(f"Existing VDB Collection name: {collection_name} with tenant: {tenant_name}")

        return self.client.collections.get(collection_name).with_tenant(tenant_name)

    def create_collection(self, collection_name: str) -> str:
        """Create a collection in a Weaviate database.

        This method creates a collection in the client's Weaviate database if it does not already exist. The name of the
        collection is passed in as `collection_name`. The method also enables multi-tenancy config for the collection.

        Once the collection is created, it is stored in the instance variable `self.collection`. A tenant is also created,
        and added to the collection. Currently, the tenant has the same name as the collection.

        The method returns the name of the created (or already existing) collection.

        Note:
            In some future implementation, the tenant might not be equivalent to the collection, and could represent users.

        Parameters
        ----------
        collection_name : str
            The name of the collection to be created in the Weaviate database.

        Returns
        -------
        str
            The name of the created (or already existing) collection.

        Examples
        --------
        >>> params = {...}
        >>> weaviate_handler = WeaviateConnector(params)
        >>> weaviate_handler.create_collection("MyCollection")
        "MyCollection"

        """
        with self:
            check = self.client.collections.exists(collection_name)

        if check:
            logger.info(f"Collection exists: {collection_name}")
            return collection_name

        with self:
            result = self.client.collections.create(
                collection_name,
                multi_tenancy_config=Configure.multi_tenancy(
                    enabled=True,
                    auto_tenant_creation=True
                )
            )

        logger.info(f"Collection created {collection_name}")

        return result

    def collection_add_tenant(self, tenant_name: str) -> bool:
        """
        Add a tenant to Weaviate collection

        :param tenant_name: The name of the tenant to be added to the collection.
        :return: The result of adding the tenant to the collection.
        """
        tenants = [Tenant(name=tenant_name)]

        collection_name = self.params.get("collection_name")
        multi_collection = self.client.collections.get(collection_name)
        multi_collection.tenants.create(tenants=tenants)

        return True

    def load_chunks(self, chunks: List[Dict[str, Any]]) -> int:
        """Load chunks into Weaviate.

        This method loads a list of chunks into the Weaviate Vector Database. Each chunk is expected
        to be a dictionary containing at least a 'content' key. A UUID is generated for each chunk,
        and the content is vectorized using the vectorizer.

        Parameters
        ----------
        chunks : List[Dict[str, Any]]
            A list of chunks to load into the database.

        Returns
        -------
        int
            The number of chunks successfully loaded.

        Raises
        ------
        Exception
            If there is an error during the loading process.

        """

        collection = self.__get_tenant_collection_object()

        with collection.batch.dynamic() as batch:

            for chunk in chunks:
                chunk_model_json = chunk.model_dump()
                uuid = generate_uuid5(chunk_model_json)
                hf_vector = self.vectorizer.vectorize(chunk.content)
                try:
                    response = batch.add_object(
                        properties=chunk_model_json,
                        uuid=uuid,
                        vector=hf_vector,
                    )
                    logger.info(response)
                except Exception as e:
                    raise e

        # Check for failed objects
        if len(collection.batch.failed_objects) > 0:
            logger.warning(f"Failed to import {len(collection.batch.failed_objects)} objects. {collection.batch.failed_objects[0].message}")

        return len(chunks) - len(collection.batch.failed_objects)

    def load_file(self, path: str) -> int:
        """Load a file into Weaviate.

        Reads the file at the given path, processes it into chunks, and loads the chunks into Weaviate.

        Parameters
        ----------
        path : str
            The file path to load.

        Returns
        -------
        int
            The number of chunks loaded.

        Raises
        ------
        Exception
            If there is an error during file processing or loading.

        """
        chunk_processor = DocumentProcessor(self.collection_name)
        chunks = chunk_processor.chunk_documents(path)

        return self.load_chunks(chunks)

    def load_dir(self, path: str, extension: str) -> int:
        """Load files from a directory into Weaviate.

        Processes all files with the given extension in the directory and loads them into Weaviate.

        Parameters
        ----------
        path : str
            The directory path containing files to load.
        extension : str
            The file extension to filter by (e.g., 'txt').

        Returns
        -------
        int
            The number of chunks loaded.

        Raises
        ------
        Exception
            If there is an error during directory processing or loading.

        """
        chunk_processor = DocumentProcessor(self.collection_name)
        chunks = chunk_processor.chunk_documents(path, extension)

        return self.load_chunks(chunks)

    def load_text(self, text: str, metadata: dict = None) -> int:
        """
        Load a text chunk into the Vector Database.
        metadata = {
            "document_name": "",
            "document_type": "",
            "source": ""
        }

        :param text: The text to be loaded.
        :param metadata: Optional metadata related to the text. Default is None.
        :return: The number of chunks that were loaded (always returns 1).
        """
        chunk = string_to_chunk(text, metadata)

        with self:
            chunks_loaded = self.load_chunks([chunk])

        return chunks_loaded  # returning number of chunks that were loaded


    @search_only
    def kw_search(self, query: str, limit: int = 3) -> QueryReturn:
        """Perform a keyword search in the Weaviate database.

        This function uses the decorator @search_only. It extracts keywords from the query
        to perform a search using the bm25 algorithm from Weaviate's collection query method,
        returning the results as a QueryReturn object. If an exception arises during the
        execution of the query, a log with the exception is generated.

        Parameters
        ----------
        query : str
            The search query as string to be used for the keyword search on the Weaviate database.
        limit : int, optional
            The maximum number of search results to return, by default 3.

        Returns
        -------
        QueryReturn
            The result of the search query. Returns an object of type QueryReturn even if
            an exception occurred during search (empty QueryReturn in such cases).

        Examples
        --------
        >>> kw_search("cat", 5)
        QueryReturn(objects=[...]) # output truncated for brevity

        Note:
        ----
        The method and its inner workings can be better understood from the perspective of the WeaviateConnector class,
        which manages interactions with a Weaviate Vector database. This method belongs to said class providing ways
        to connect to a Weaviate cluster, manage collections, load and chunk documents, and perform various types of
        searches and data manipulations. Furthermore, the use of the decorator @search_only, whose specifics are not
        provided, but should be designed to only enable search operations in the database (reading data), is present
        in this function as well in order to control the operations allowed by this method.

        """
        search_kw = extract_keywords(query)
        logger.info("Extracted keywords to search for: %s", search_kw)
        response = QueryReturn(objects=[])

        def ksearch():
            collection = self.__get_tenant_collection_object()
            return collection.query.bm25(
                query=search_kw,
                query_properties=QUERY_PROPERTIES,
                return_metadata=MetadataQuery(score=True, distance=True),
                limit=limit,
            )

        return search_and_handle_errors(ksearch, logger=logger)

    @search_only
    def vector_search(self, query: str, limit: int = 3) -> QueryReturn:
        """Use Vector Search for document retrieval from Weaviate Database.

        Parameters
        ----------
        query : str
            The query string for vector search.
        limit : int, optional
            Maximum number of results to return (default is 3).

        Returns
        -------
        QueryReturn
            The search results.

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

        def vsearch() -> QueryReturn:
            query_vector = self.vectorizer.vectorize(query)
            collection = self.__get_tenant_collection_object()
            return collection.query.near_vector(
                near_vector=query_vector,
                limit=limit,
                return_metadata=MetadataQuery(distance=True, score=True),
            )

        return search_and_handle_errors(vsearch, logger=logger)

    def search(self, query: str, limit: int = 3) -> QueryReturn:
        return self.hybrid_search(query, limit)

    @search_only
    def hybrid_search(self, query: str, limit: int = 3) -> QueryReturn:
        """Use Hybrid Search for document retrieval from Weaviate Database.

        Perform a hybrid search by combining keyword-based search and vector-based search.

        Parameters
        ----------
        query : str
            The search query.
        limit : int, optional
            The maximum number of results to return (default is 3).

        Returns
        -------
        QueryReturn
            The hybrid search results.

        :raises Exception: If there is an error during the search.

        """
        response = QueryReturn(objects=[])

        def search():
            kw_results = self.kw_search(query, limit)
            vector_results = self.vector_search(query, limit)

            return self.__combine_and_rerank_results(kw_results, vector_results)

        return search_and_handle_errors(search, logger=logger)

    @staticmethod
    def __combine_and_rerank_results(
        kw_results: QueryReturn,
        vector_results: QueryReturn,
        limit: int = 3,
        kw_vector_weights: Tuple[float, float] = [0.3, 0.7],
    ) -> List[dict]:
        """Combine and rerank keyword search and vector search results.

        Parameters
        ----------
        kw_results : QueryReturn
            Keyword search results.
        vector_results : QueryReturn
            Vector search results.
        limit : int, optional
            The maximum number of combined results to return (default is 3).
        kw_vector_weights : Tuple[float, float], optional
            Weights for keyword and vector results (default is (0.3, 0.7)).

        Returns
        -------
        List[dict]
            The combined and reranked search results.

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

    def search_filter(self, query: str, filter_expression: dict = None, group_properties: list = None):
        """Retrieve objects from the collection that have a property whose value matches the given pattern.

        Parameters
        ----------
        query : str
            The search query.
        filter_expression : dict, optional
            A filter expression to apply to the query (default is None).
        group_properties : list, optional
            A list of properties to group results by (default is None).

        Returns
        -------
        list or None
            Filtered and grouped search results, or None if no results found.

        Examples
        --------
            >>> handler = WeaviateConnector(params)
            >>> filter_expression = {
                    "or": [
                        {
                            "and": [
                                {"property": "param1", "operator": "like", "value": "hello"},
                                {"property": "param4", "operator": "not like", "value": "Good Day"}
                            ]
                        },
                        {
                            "and": [
                                {"property": "param2", "operator": "=", "value": "ola"},
                                {"property": "param3", "operator": "=", "value": 1}
                            ]
                        }
                    ]
                }

        """
        query_builder = QueryBuilder()
        filters = query_builder.construct_query(filter_expression)

        collection = self.__get_tenant_collection_object()
        try:
            query_vector = self.vectorizer.vectorize(query)

            response: QueryReturn = collection.query.near_vector(
                near_vector=query_vector,
                filters=filters,
                limit=10,
                return_metadata=MetadataQuery(distance=True, score=True),
            )

        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")
            return None

        if not response.objects:
            return None

        if group_properties:
            return group_results_by_properties(response, group_properties)
        else:
            return response

    def filter(self, filter_expression: dict) -> QueryReturn:
        """
        Query objects from the tenant-specific database collection based on a filter expression.

        This method establishes a connection to the appropriate database collection
        specific to the tenant. It then builds a query from the provided filter expression
        using the QueryBuilder. The fetched objects are returned along with their creation
        and last update time.

        Parameters:
        ----------
        filter_expression : dict
            The expression used to filter which objects will be queried. The expressed
            conditions must be in the form of a dictionary where the keys represent
            the property fields of the objects and the values specify the conditions
            for filtering. The conditions could include operators such as "=", ">=",
            "<=", etc. Nested conditions can be expressed using logical operators such as "and" and "or".

        Returns:
        -------
        QueryReturn
            An instance of QueryReturn which contains the fetched objects and their metadata.

        Examples:
        --------
        >>> filter(self, {"property": "name", "operator": "=", "value": "John"})

        This example shows how to use the method to fetch objects whose 'name' property is 'John'.

        Note:
        ----
        The actual structure and content of the returned QueryReturn depend on the schema and data in the specific collection.

        """

        collection = self.__get_tenant_collection_object()
        query_builder = QueryBuilder()
        filters = query_builder.construct_query(filter_expression)

        response: QueryReturn = collection.query.fetch_objects(
            filters=filters,
            return_metadata=MetadataQuery(
                creation_time=True,
                last_update_time=True
            )
        )

        return response

    def filter_count(self, filter_expression: dict):
        """Count the number of objects in a Weaviate collection by applying filters based on the given filter expression.

        Opens a connection to the Weaviate client and count the objects using passed properties as filters.

        Parameters
        ----------
        properties : Iterable (list, tuple, etc.)
            The list of tuples where each tuple consists of a string key representing property
            and the corresponding value to filter the Weaviate collection objects.
            e.g. [("document_type", "test_type"), ("source", "host/database")]

        match_type : str, optional (default = "like")
            The matching type to be used with the properties for filtering.
            It can hold following values:
            - "like": Provides a case-insensitive partial match for string throughout the filtered objects.

        Returns
        -------
        WeaviateObjectsHandler
            The result object that contains an aggregated count over all objects in
            the collection that match the applied filter.

        Raises
        ------
        ConnectionError
            If there is an error in connecting to Weaviate.

        Notes
        -----
        - Filters are created in the form suitable for the Weaviate client SDK.
        - If there are multiple filters, they are combined using logical "AND".

        Examples
        --------
        >>> handler = VectorDatabaseFactory.create_database(vdb_params)
        >>> filter_expression = {
                "or": [
                    {
                        "and": [
                            {"property": "param1", "operator": "like", "value": "hello"},
                            {"property": "param4", "operator": "not like", "value": "Good Day"}
                        ]
                    },
                    {
                        "and": [
                            {"property": "param2", "operator": "=", "value": "ola"},
                            {"property": "param3", "operator": "=", "value": 1}
                        ]
                    }
                ]
            }
        >>> handler.count_objects_by_properties(filter_expression)
            WeaviateObjectsBatchGetResponse({"totalCount": 100})

        >>> handler.count_objects_by_properties([], "like")
            WeaviateObjectsBatchGetResponse({"totalCount": 0})

        """
        query_builder = QueryBuilder()
        filters = query_builder.construct_query(filter_expression)

        collection = self.__get_tenant_collection_object()

        def aggregation():
            return collection.aggregate.over_all(total_count=True, filters=filters)

        return search_and_handle_errors(aggregation, logger=logger)

    def filter_group_count(self, filter_expression: dict, group_by_prop: str) -> AggregateGroupByReturn:
        """Example response:
        AggregateGroupByReturn(groups=[AggregateGroup(grouped_by=GroupedBy(prop='date_loaded', value='2024-09-24T07:11:53.068792Z'), properties={}, total_count=1), AggregateGroup(grouped_by=GroupedBy(prop='date_loaded', value='2024-09-24T07:11:53.067935Z'), properties={}, total_count=1), AggregateGroup(grouped_by=GroupedBy(prop='date_loaded', value='2024-09-24T07:11:53.06836Z'), properties={}, total_count=1)])

        Parameters
        ----------
        filter_expression : dict
            A filter expression to apply to the query.
        group_by_prop : str
            The property to group results by.

        Returns
        -------
        AggregateGroupByReturn
            The grouped count results.

        """
        query_builder = QueryBuilder()
        filters = query_builder.construct_query(filter_expression)

        collection = self.__get_tenant_collection_object()

        response = collection.aggregate.over_all(
            total_count=True,
            filters=filters,
            group_by=GroupByAggregate(prop=group_by_prop),
        )

        return response

    def delete_on_metadata(self, metadata: Dict):
        filters = {
            "operator": "And",
            "operands": [
                {
                    "path": [key],
                    "operator": "Equal",
                    "valueString": value
                } for key, value in metadata.items()
            ]
        }

        collection = self.__get_tenant_collection_object()

        response = collection.data.delete_many(
            where=filters
        )

        return response

    def delete_collection(self, collection_name: str):
        """Deletes a collection from the Weaviate Vector Database.

        This method attempts to delete a collection and all its data from the Weaviate Vector Database. It
        makes a call to the delete method of the Weaviate client collections object with the provided
        collection name as the argument. If the operation is successful, it returns True. If an exception occurs
        during the execution of the operation, it returns False.

        Parameters
        ----------
        collection_name : str
            The name of the collection to be deleted. It is expected to be a string representing a valid
            collection name.

        Returns
        -------
        bool
            A boolean indicating the success of the operation. It returns True if the collection was
            successfully deleted and False otherwise.

        Notes
        -----
        The operation of deleting a collection is destructive and cannot be undone. It will delete the
        collection and all its data permanently.

        Using this method will close the connection to the Weaviate client after the operation. This is done
        in a finally, block to ensure the connection is closed even if an exception occurs.

        Example:
        --------
        >>> handler = WeaviateConnector()
        >>> handler.delete_collection("collection_name")
        True

        """
        try:
            self.client.collections.delete(collection_name)
            logger.info(f"Deleted collection '{collection_name}'")
            return True
        except Exception:
            logger.error(f"Error deleting collection: {e}")
            return False

    def check_and_update_document(self,
                                  text: Dict[str, Dict[str, str]],
                                  metadata: dict,
                                  lookback_days: int = 5
                                  ) -> bool:
        """
        Check if the document already exists in Weaviate. If it does, check the dates of the chunks.
        If any chunk is older than 5 days, delete all chunks belonging to this document and reload the document.

        Parameters
        ----------
        document : Dict[str, Dict[str, str]]
            The document to check and update.
        """
        filter_expression = {
            "and": [
                {"property": "document_name", "operator": "=", "value": metadata["document_name"]},
                {"property": "document_type", "operator": "=", "value": metadata["document_type"]},
                {"property": "source", "operator": "=", "value": metadata["source"]}
            ]
        }

        # Search for existing chunks
        existing_chunks = self.filter(filter_expression=filter_expression)

        if existing_chunks and existing_chunks.objects:
            # Check the dates of the chunks
            fresh_from_date = datetime.now(timezone.utc) - timedelta(days=lookback_days)
            for chunk in existing_chunks.objects:
                if chunk.metadata.last_update_time < fresh_from_date:
                    # Delete all chunks belonging to this document
                    result = self.delete_on_metadata(metadata)
                    print(result)
                    # If deletion was successful, reload the document
                    #self.load_text(text)
                    break

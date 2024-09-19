from typing import List, Tuple
import weaviate
import weaviate.util
from weaviate.util import generate_uuid5
from weaviate.auth import AuthApiKey
from weaviate.classes.query import Filter, MetadataQuery
from weaviate.classes.config import Configure
from weaviate.classes.tenants import Tenant
from analitiq.vectordb.weaviate.query_builder import QueryBuilder
from weaviate.collections.classes.internal import QueryReturn

from analitiq.logger.logger import logger
from analitiq.utils import keyword_extractions
from analitiq.vectordb.base_handler import BaseVDBHandler
from analitiq.utils.document_processor import (
    DocumentProcessor,
    group_results_by_properties,
)
from analitiq.vectordb.schema import Chunk

from analitiq.vectordb import analitiq_vectorizer

VECTOR_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
QUERY_PROPERTIES = ["content"]  # OR content_kw


def search_only(func):
    """
    A decorator for wrapping database search functions.

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


def search_grouped(func):
    """
    This decorator function enhances the functionality of a Batch function by grouping its resultant data.

    Given a Batch function, this function not only invokes the Batch function but also groups the
    results according to certain properties.

    Parameters:
    ----------
    func : callable
        The batch function whose results are to be grouped. It's expected to return a list of dictionaries,
        where each dictionary contains keys representing various properties.

    Returns:
    -------
    callable
        A function wrapper that, when called, executes the provided Batch function and groups its results.

    Inner Function Parameters (wrapper):
    ----------
    *args
        Variable length argument list of the Batch function.
    **kwargs
        Arbitrary keyword arguments of the Batch function.

    Inner Function Returns:
    -----------
    dict
        A dictionary where the keys are tuples representing the unique combinations of property values,
        and the values are lists containing the corresponding results from the Batch function.

    For example, if the Batch function was to return:
        [
            {"document_name": "doc1", "source": "src1", "text": "Hello"},
            {"document_name": "doc1", "source": "src1", "text": "Hi"},
            {"document_name": "doc2", "source": "src2", "text": "Hello"}
        ]

    The returned result from the decorated function would be:
        {
            ("doc1", "src1"): [{"document_name": "doc1", "source": "src1", "text": "Hello"}, {"document_name": "doc1", "source": "src1", "text": "Hi"}],
            ("doc2", "src2"): [{"document_name": "doc2", "source": "src2", "text": "Hello"}]
        }

    Notes:
    -----
    The grouping of results is done based on "document_name" and "source" property values.
    """

    def wrapper(*args, **kwargs):
        """Wrap the function."""
        response = func(*args, **kwargs)
        self = args[0]
        return group_results_by_properties(response, ["document_name", "source"])

    return wrapper


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

        self.vectorizer = analitiq_vectorizer.AnalitiqVectorizer(VECTOR_MODEL_NAME)

    def connect(self):
        """Connect to the Weaviate database."""
        self.client: weaviate.WeaviateClient = weaviate.connect_to_wcs(
            cluster_url=self.params["host"],
            auth_credentials=AuthApiKey(self.params["api_key"]),
        )

        if not self.client.collections.exists(self.collection_name):
            self.create_collection(self.collection_name)
            logger.info(f"Collection created {self.collection_name}")
        else:
            logger.info(f"Existing VDB Collection name: {self.collection_name}")

    def __get_tenant_collection_object(
        self, collection_name: str, tenant_name: str
    ) -> object:
        """
        Returns the collection object for multi tenancy collection

        :param collection_name: The name of the collection to retrieve the collection object from.
        :param tenant_name: The name of the tenant for which the collection object is being retrieved.
        :return: The collection object specific to the required tenant.
        """
        multi_collection = self.client.collections.get(collection_name)

        # Get collection specific to the required tenant
        return multi_collection.with_tenant(tenant_name)

    def create_collection(self, collection_name: str) -> str:
        """
        Create a collection in a Weaviate database.

        This method creates a collection in the client's Weaviate database if it does not already exist. The name of the
        collection is passed in as `collection_name`. The method also enables multi-tenancy config for the collection.

        Once the collection is created, it is stored in the instance variable `self.collection`. A tenant is also created,
        and added to the collection. Currently, the tenant has the same name as the collection.

        The method returns the name of the created (or already existing) collection.

        Note:
            In some future implementation, the tenant might not be equivalent to the collection, and could represent users.

        Parameters:
        ----------
        collection_name : str
            The name of the collection to be created in the Weaviate database.

        Returns:
        -------
        str
            The name of the created (or already existing) collection.

        Examples:
        --------
        >>> params = {...}
        >>> weaviate_handler = WeaviateHandler(params)
        >>> weaviate_handler.create_collection("MyCollection")
        "MyCollection"
        """

        check = self.client.collections.exists(collection_name)

        if check:
            return collection_name

        self.client.collections.create(
            collection_name,
            # enable multi_tenancy_config
            multi_tenancy_config=Configure.multi_tenancy(enabled=True),
        )

        self.collection = self.client.collections.get(collection_name)

        # Add a tenant to the collection. Right now the tenant is the same as the collection.
        # In the future, this could be users
        self.collection.tenants.create(tenants=[Tenant(name=collection_name)])

        return collection_name

    def close(self):
        """
        Closes the client connection.

        :return: None
        """
        self.client.close()

    def load_chunks(self, chunks: List[Chunk]) -> int:
        """
        Load chunks into Weaviate.

        This method aims to load a list of chunks into the Weaviate Vector Database. The chunks are represented
        as dictionaries. An UUID is generated for each chunk using the chunk's `model_dump` method. This UUID is used
        while loading each chunk into Weaviate. The resulting UUIDs are in UUID5 format. Additionally, the content of each chunk
        is vectorized using `vectorize` method of the vectorizer. This vector represents the document in the vector space and
        is stored alongside the document in Weaviate. Once a chunk is loaded successfully, the counter for loaded chunks is
        incremented. After all the chunks have been loaded, the Weaviate client connection is closed and the number of loaded chunks is logged.

        Parameters:
        -----------
        chunks : List[Chunk]
            A list of Chunk instances representing chunks of text extracted from the document(s). Each chunk is one
            unit of text that will be fed into Weaviate as a separate document entry. The Chunk class represents a unit
            of text from a larger document and includes metadata like the project_name, document_name, source, content,
            and other properties.

        Returns:
        --------
        int

        Raises:
        -------
        Any exception raised by the underlying Weaviate client during the loading process will get logged as an error
        using the logger but it will not stop the function from trying to load the remaining chunks. The exact type of
        the exception and its cause will depend on the nature of the error in the loading process.

        Examples:
        ---------
        Assuming `weaviate_handler` is an instance of `WeaviateHandler`,
        and `chunks` is a list of `Chunk` instances:

        ```python
        weaviate_handler.load_chunks(chunks)
        ```

        This will attempt to load all chunks into Weaviate and log any errors encountered during the process. The
        method will also log the total number of chunks that were successfully loaded.

        """
        chunks_loaded = 0

        try:
            self.client.connect()
        except Exception as e:
            logger.error(e)

        collection = self.__get_tenant_collection_object(
            self.collection_name, self.collection_name
        )

        with collection.batch.dynamic() as batch:
            for chunk in chunks:
                uuid = generate_uuid5(chunk.model_dump())
                hf_vector = self.vectorizer.vectorize(chunk.content)
                try:
                    response = batch.add_object(
                        properties=chunk.model_dump(), uuid=uuid, vector=hf_vector
                    )
                    logger.info(response)
                    chunks_loaded += 1
                except Exception as e:
                    raise e

        self.close()
        logger.info("Loaded chunks: %s", chunks_loaded)

        return chunks_loaded

    def load_file(self, path: str) -> int:
        """
        Load a file into the Weaviate Vector Database.

        This method reads and processes file from the specified path. The method applies the
        `chunk_documents` method from the `chunk_processor` attribute of the WeaviateHandler instance
        to partition documents present at the specified path. The result, a sequence of chunks,
        are then loaded into the Weaviate database through the `load_chunks` method.

        Parameters
        ----------
        path : str
            The path of the file to be processed and loaded.

        Raises
        ------
        FileNotFoundError
            If the specified file does not exist.

        ValueError
            If the file extension specified is not allowed. The allowed extensions
            are determined by the configuration of the `chunk_processor`.

        """
        chunk_processor = DocumentProcessor(self.collection_name)
        chunks = chunk_processor.chunk_documents(path)

        return self.load_chunks(chunks)

    def load_dir(self, path: str, extension: str):
        """
        Load files in a directory into the Weaviate Vector Database.

        This method reads and processes files from the specified path with the desired extension.
        The method applies the `chunk_documents` method from the `chunk_processor` attribute of the
        WeaviateHandler instance to partition documents present at the specified path.
        The result, a sequence of chunks, are then loaded into the Weaviate database through the
        `load_chunks` method.

        Parameters
        ----------
        path : str
            The path of the file or directory to be processed and loaded. The path
            must contain either a file or a directory.

        extension : str
            The extension of the files to be loaded. only files
            with matching extension in the directory will be loaded. The file_ext
            should not contain a leading period (For example, use 'txt' instead of '.txt').

        Raises
        ------
        FileNotFoundError
            If the specified path does not exist or does not contain any files
            with the specified extension.

        ValueError
            If the file extension specified is not allowed. The allowed extensions
            are determined by the configuration of the `chunk_processor`.

        """
        chunk_processor = DocumentProcessor(self.collection_name)
        chunks = chunk_processor.chunk_documents(path, extension)

        return self.load_chunks(chunks)

    @search_only
    def kw_search(self, query: str, limit: int = 3) -> QueryReturn:
        """
        Perform a keyword search in the Weaviate database.

        This function uses the decorator @search_only. It extracts keywords from the query
        to perform a search using the bm25 algorithm from Weaviate's collection query method,
        returning the results as a QueryReturn object. If an exception arises during the
        execution of the query, a log with the exception is generated.

        Parameters:
        ----------
        query : str
            The search query as string to be used for the keyword search on the Weaviate database.
        limit : int, optional
            The maximum number of search results to return, by default 3.

        Returns:
        -------
        QueryReturn
            The result of the search query. Returns an object of type QueryReturn even if
            an exception occurred during search (empty QueryReturn in such cases).

        Examples:
        --------
        >>> kw_search("cat", 5)
        QueryReturn(objects=[...]) # output truncated for brevity

        Note:
        ----
        The method and its inner workings can be better understood from the perspective of the WeaviateHandler class,
        which manages interactions with a Weaviate Vector database. This method belongs to said class providing ways
        to connect to a Weaviate cluster, manage collections, load and chunk documents, and perform various types of
        searches and data manipulations. Furthermore, the use of the decorator @search_only, whose specifics are not
        provided, but should be designed to only enable search operations in the database (reading data), is present
        in this function as well in order to control the operations allowed by this method.
        """

        search_kw = keyword_extractions.extract_keywords(query)
        logger.info("Extracted keywords to search for: %s", search_kw)
        response = QueryReturn(objects=[])

        try:
            self.client.connect()
            collection = self.__get_tenant_collection_object(
                self.collection_name, self.collection_name
            )
            response: QueryReturn = collection.query.bm25(
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
        :return: A QueryReturn object containing the search results.

        :raises Exception: If there is an error during the search.

        """
        response = QueryReturn(objects=[])

        try:
            kw_results = self.kw_search(query, limit)
            vector_results = self.vector_search(query, limit)

            response = self.__combine_and_rerank_results(kw_results, vector_results)
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
            self.client.connect()
            collection = self.__get_tenant_collection_object(
                self.collection_name, self.collection_name
            )
            response: QueryReturn = collection.query.near_vector(
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
    def __combine_and_rerank_results(
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
        combined_list = sorted(
            combined.values(), key=lambda x: x["score"], reverse=True
        )

        # Extract only the results (up to the specified limit)
        reranked_results = [item["result"] for item in combined_list[:limit]]

        return QueryReturn(objects=reranked_results)

    def search_with_filter(
        self, query: str, filter_expression: dict = None, group_properties: list = None
    ):
        """Retrieve objects from the collection that have a property whose value matches the given pattern.

        Example:
        -------
        response = vector_db_client.get_many_like("document_name", "schema")

        :param query: The search string.
        :param filter_expression: The name of the property used for filtering.
        :param group_properties: Properties by which to group the results, if needed

        :return: A list of objects that have a property matching the pattern.
        :rtype: list or None
        Examples:
            --------
            >>> handler = WeaviateHandler(params)
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
        try:
            self.client.connect()
        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")

        query_builder = QueryBuilder()
        filters = query_builder.construct_query(filter_expression)
        collection = self.__get_tenant_collection_object(
            self.collection_name, self.collection_name
        )
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
        finally:
            self.close()

        if not response.objects:
            return None

        if group_properties:
            return group_results_by_properties(response, group_properties)
        else:
            return response

    def count_with_filter(self, filter_expression: dict):
        """
        Count the number of objects in a Weaviate collection by applying filters based on the given filter expression.

        Opens a connection to the Weaviate client and count the objects using passed properties as filters.
        The filters are created by invoking the _create_filters() method (static method).

        Parameters:
        ----------
        properties : Iterable (list, tuple, etc.)
            The list of tuples where each tuple consists of a string key representing property
            and the corresponding value to filter the Weaviate collection objects.
            e.g. [("document_type", "test_type"), ("source", "host/database")]

        match_type : str, optional (default = "like")
            The matching type to be used with the properties for filtering.
            It can hold following values:
            - "like": Provides a case-insensitive partial match for string throughout the filtered objects.

        Returns:
        -------
        WeaviateObjectsHandler
            The result object that contains an aggregated count over all objects in
            the collection that match the applied filter.

        Raises:
        ------
        ConnectionError
            If there is an error in connecting to Weaviate.

        Notes:
        -----
        - Filters are created in the form suitable for the Weaviate client SDK.
        - If there are multiple filters, they are combined using logical "AND".

        Examples:
        --------
        >>> handler = WeaviateHandler(params)
        >>> filter_expression = filter_expression = {
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
        >>> handler.count_objects_by_properties(properties, "like")
            WeaviateObjectsBatchGetResponse({"totalCount": 100})

        >>> handler.count_objects_by_properties([], "like")
            WeaviateObjectsBatchGetResponse({"totalCount": 0})

        """
        query_builder = QueryBuilder()
        filters = query_builder.construct_query(filter_expression)

        collection = self.__get_tenant_collection_object(
            self.collection_name, self.collection_name
        )
        try:
            self.client.connect()
        except Exception as e:
            logger.error(f"Error connecting to Weaviate: {e}")
            return None

        # filters = self._create_filters(properties, match_type)

        response = collection.aggregate.over_all(
            total_count=True,
            filters=filters,  # Pass the generated filters directly here
        )

        self.close()

        return response

    def delete_collection(self, collection_name: str):
        """
        Deletes a collection from the Weaviate Vector Database.

        This method attempts to delete a collection and all its data from the Weaviate Vector Database. It
        makes a call to the delete method of the Weaviate client collections object with the provided
        collection name as the argument. If the operation is successful, it returns True. If an exception occurs
        during the execution of the operation, it returns False.

        Parameters:
        ----------
        collection_name : str
            The name of the collection to be deleted. It is expected to be a string representing a valid
            collection name.

        Returns:
        -------
        bool
            A boolean indicating the success of the operation. It returns True if the collection was
            successfully deleted and False otherwise.

        Notes:
        -----
        The operation of deleting a collection is destructive and cannot be undone. It will delete the
        collection and all its data permanently.

        Using this method will close the connection to the Weaviate client after the operation. This is done
        in a finally block to ensure the connection is closed even if an exception occurs.

        Example:
        --------
        >>> handler = WeaviateHandler()
        >>> handler.delete_collection("collection_name")
        True
        """

        try:
            self.client.collections.delete(collection_name)
            return True
        except Exception:
            return False
        finally:
            self.close()

    @staticmethod
    def _create_filters(properties: list, match_type: str):
        if match_type == "like":
            filters = [
                Filter.by_property(name).like(value) for name, value in properties
            ]
        else:
            filters = [
                Filter.by_property(name).equal(value) for name, value in properties
            ]

        return filters

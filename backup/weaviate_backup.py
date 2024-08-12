import os
import logging
import weaviate
from weaviate.util import generate_uuid5  # Used for generating a deterministic UUID based on input
import weaviate.classes as wvc
from weaviate.classes.query import Filter
from typing import Optional
from pydantic import BaseModel
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


def search_only(func):
    """A decorator that ensures the function returns only search results.

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
    """A decorator that modifies a search function to return results grouped by document and source.

    Usage:
        @grouped_search
        def some_search_function(...):
            ...
    """
    def wrapper(*args, **kwargs):
        # Call the original function
        response = func(*args, **kwargs)
        # Call the grouping function on the response
        self = args[0] # Assuming the first argument to the function is 'self'
        return self.group_by_document_and_source(response)
    return wrapper


class Chunk(BaseModel):
    """Represents a chunk of a document with metadata for insertion into a Weaviate database.

    Attributes
    ----------
        project_name: The name of the project the document belongs to.
        document_name: The name of the document.
        document_type: The type of the document, e.g., 'txt', 'pdf'.
        content: The actual content of the chunk.
        source: The source path of the document.

    """

    project_name: str = None
    document_name: str = None
    document_type: Optional[str] = None
    content: str = None
    source: str
    document_num_char: int
    chunk_num_char: int


class WeaviateHandler():
    """A class for interacting with a Weaviate vector database, including loading documents and performing searches."""

    def __init__(self, params):
        """Initializes a new instance of the class, setting up a connection to a Weaviate cluster and ensuring
        a collection with the specified name exists within that cluster.

        This method connects to a Weaviate cluster using the provided URL and API key, then checks if a collection
        named after the `project_name` exists. If the collection does not exist, it creates a new collection with
        that name.

        Parameters
        ----------
        - project_name (str): The name of the collection to either connect to or create within the Weaviate cluster.
                              This name is used to identify the collection uniquely within the cluster.
        - url (str): The URL of the Weaviate cluster to connect to. This should include the protocol (http or https)
                     and the hostname or IP address of the cluster, possibly including the port number if not using
                     the standard ports for http/https.
        - api_key (str): The API key used for authenticating with the Weaviate cluster. This key provides the necessary
                         permissions to access the cluster, manage collections, and perform other operations within
                         the cluster's scope.

        Note:
        - This method requires that the `weaviate` library is installed and correctly configured in the environment
          where this code is run. Specifically, the `weaviate.connect_to_wcs` and `weaviate.auth.AuthApiKey` methods
          are used for connecting to the cluster and authenticating.
        - The method assumes that the provided `api_key` has sufficient permissions to create and manage collections
          within the Weaviate cluster.

        """
        self.client = weaviate.connect_to_wcs(
            cluster_url=params["host"], auth_credentials=weaviate.auth.AuthApiKey(params["api_key"])
        )
        project_name = params["collection_name"]

        # Create collection if it does not exist in Weaviate.
        if not self.client.collections.exists(project_name):
            self.client.collections.create(project_name)
            logging.info(f"Collection created {project_name}")

        self.project_name = project_name
        self.collection = self.client.collections.get(project_name)
        logging.info(f" Vector DB Collection name: {project_name}")

    def chunk_load_file_or_directory(self, path: str, extension: Optional[str] = None, chunk_size: int = 2000, chunk_overlap: int = 200):
        """First we check if we are loading a file or directory.
        For directory, load all files from a directory (matching teh extension if provided), split them into chunks, and return a list of Chunk objects.
        For file, load the file, if it meets the validation criteria. Split it into chunks, and return a list of Chunk objects.

        This method checks if the specified file exists and whether its extension is among the allowed ones.

        Parameters
        ----------
            path: Path to the file or directory containing files to be chunked.
            extension: File extension to filter the files in the directory.
            chunk_size: The size of chunks into which to split the documents
            chunk_overlap: How much the chunks should overlap.

        Returns
        -------
            A list of Chunk objects.

        Raises
        ------
            FileNotFoundError: If the specified file does not exist.
            ValueError: If the file's extension is not among the allowed ones.

        """
        if os.path.isfile(path):
            loader = TextLoader(path)

        elif os.path.isdir(path):
            loader = DirectoryLoader(path, glob=f"**/*.{extension}", loader_cls=TextLoader)

        else:
            return False

        documents = loader.load()
        #print(documents)

        doc_lengths = {doc.metadata["source"]: len(doc.page_content) for doc in documents}

        doc_splitter = RecursiveCharacterTextSplitter(
            chunk_size=int(chunk_size), chunk_overlap=int(chunk_overlap)
        )

        documents_chunks = doc_splitter.split_documents(documents)

        chunks = [
            Chunk(
                project_name=self.project_name,  # Load project name from environment variable
                content=chunk.page_content,
                source=chunk.metadata["source"],
                document_type=extension,
                document_name=os.path.basename(chunk.metadata["source"]),
                document_num_char=doc_lengths[chunk.metadata["source"]],
                chunk_num_char=len(chunk.page_content)
            ) for chunk in documents_chunks
        ]

        chunks_loaded = 0
        with self.collection.batch.dynamic() as batch:
            for chunk in chunks:
                #print(chunk)
                uuid = generate_uuid5(chunk.model_dump())
                batch.add_object(properties=chunk.model_dump(), uuid=uuid)
                chunks_loaded = chunks_loaded+1

        self.client.close()


    def load(self, _path: str, file_ext: Optional[str] = None):
        """Loads a file or directory into Weaviate.

        Example:
        -------
        wc=WeaviateHandler(host, api_key, project_name)
        wc.load('/Users/me/Documents/Projects/hello/test.yml')

        :param _path: The path to the file or directory.
        :param file_ext: (optional) The file extension to filter files when loading a directory. Defaults to None.
        :return: None

        """
        allowed_extensions = ["py", "yaml", "yml", "sql", "txt", "md", "pdf"]  # List of allowed file extensions

        # Check if the file exists
        if not os.path.exists(_path):
            msg = f"The path {_path} does not exist."
            raise FileNotFoundError(msg)

        if os.path.isdir(_path):
            if file_ext not in allowed_extensions:
                msg = f"The file extension .{file_ext} is not allowed. Allowed extensions: {allowed_extensions}"
                raise ValueError(msg)
                return False
        else:
            # Check if the file extension is allowed
            file_ext = os.path.splitext(_path)[1][1:]  # Extract the file extension without the dot
            if file_ext not in allowed_extensions:
                msg = f"The file extension .{file_ext} is not allowed. Allowed extensions: {allowed_extensions}"
                raise ValueError(msg)
                return False

        self.chunk_load_file_or_directory(_path, file_ext)

    def group_by_document_and_source(self, response):
        """Groups a list of dictionaries (chunks of data) by their 'document_name' and 'source'.

        This function takes a list of dictionaries where each dictionary represents a chunk of data
        from a document, and it groups these chunks based on their 'document_name' and 'source'
        fields. It uses these fields to create a unique key for grouping. The result is a dictionary
        where each key is a tuple of ('document_name', 'source'), and the value is a list of
        dictionaries (chunks) that belong to that document and source.

        Parameters
        ----------
        - response (list of dict): A list where each element is a dictionary containing details of a
          chunk of data. Each dictionary must have 'document_name' and 'source' keys among others.

        Returns
        -------
        - dict: A dictionary with keys as tuples of ('document_name', 'source') and values as lists
          of dictionaries representing the grouped chunks of data.

        """
        # Initialize an empty dictionary to hold the grouped data
        grouped_data = {}
        for item in response.objects:
            # Create a unique key for each document_name and source combination
            key = (item.properties["document_name"], item.properties["source"])

            # Check if this key exists in the dictionary
            if key in grouped_data:
                # If it does, append the current item to the existing list
                grouped_data[key].append(item.properties["content"])
            else:
                # If it does not, create a new list with the current item
                grouped_data[key] = [item.properties["content"]]

        return grouped_data

    @search_only
    def kw_search(self, query: str, limit: int = 3) -> dict:
        """Perform a keyword search in the Weaviate database.
        Example:
            response = vector_db_client.kw_search("project_name", "text to search").

        Parameters
        ----------
            query: The search query string.
            limit: The maximum number of search results to return.

        Returns
        -------
            A dictionary containing the search results.

        """
        response = {}
        try:
            response = self.collection.query.bm25(
                query=query,
                query_properties=["content"],
                limit=limit,
                filters=wvc.query.Filter.by_property("project_name").equal(self.project_name)
            )
        except Exception as e:
            logging.error(f"Weaviate error {e}")
        finally:
            self.client.close()  # Close client gracefully

        logging.info(f"Weaviate search result: {response}")
        return response

    def delete_many_like(self, property_name: str, property_value: str):
        """Delete multiple documents from the collection where the given property value is similar.

        :param property_name: The name of the property to filter by.
        :param property_value: The value of the property to match.
        :return: True if the documents are successfully deleted, False otherwise.
        """
        try:
            self.collection.data.delete_many(
                where=Filter.by_property(property_name).like(f"{property_value}*")
            )
            return True
        except:
            return False
        finally:
            self.client.close()  # Close client gracefully

    def get_many_like(self, property_name: str, property_value: str):
        """Retrieve objects from the collection that have a property whose value matches the given pattern.

        Example:
        -------
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
        except Exception:
            return None
        finally:
            self.client.close()  # Close client gracefully

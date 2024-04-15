import os
import logging
import weaviate
from weaviate.util import generate_uuid5  # Used for generating a deterministic UUID based on input
import weaviate.classes as wvc
from typing import List, Optional
from pydantic import BaseModel
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


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
        self = args[0] # Assuming the first argument to the function is 'self'
        return self.group_by_document_and_source(response)
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
    """
    project_name: str = None
    document_name: str = None
    document_type: Optional[str] = None
    content: str = None
    source: str
    document_num_char: int
    chunk_num_char: int


class WeaviateVS():
    """
    A class for interacting with a Weaviate vector database, including loading documents and performing searches.
    """

    def __init__(self, project_name, host, api_key):
        """
        Initializes a new instance of the class, setting up a connection to a Weaviate cluster and ensuring
        a collection with the specified name exists within that cluster.

        This method connects to a Weaviate cluster using the provided URL and API key, then checks if a collection
        named after the `project_name` exists. If the collection does not exist, it creates a new collection with
        that name.

        Parameters:
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
            cluster_url=host, auth_credentials=weaviate.auth.AuthApiKey(api_key)
        )

        # Create collection if it does not exist in Weaviate.
        if not self.client.collections.exists(project_name):
            self.client.collections.create(project_name)
            logging.info(f"Collection created {project_name}")

        self.project_name = project_name
        self.collection = self.client.collections.get(project_name)
        logging.info(f" Vector DB Collection name: {project_name}")

    def chunk_load_file_or_directory(self, path: str, extension: Optional[str] = None, chunk_size: int = 2000, chunk_overlap: int = 200):
        """
        First we check if we are loading a file or directory.
        For directory, load all files from a directory (matching teh extension if provided), split them into chunks, and return a list of Chunk objects.
        For file, load the file, if it meets the validation criteria. Split it into chunks, and return a list of Chunk objects.

        This method checks if the specified file exists and whether its extension is among the allowed ones.

        Parameters:
            path: Path to the file or directory containing files to be chunked.
            extension: File extension to filter the files in the directory.
            chunk_size: The size of chunks into which to split the documents
            chunk_overlap: How much the chunks should overlap.

        Returns:
            A list of Chunk objects.

        Raises:
            FileNotFoundError: If the specified file does not exist.
            ValueError: If the file's extension is not among the allowed ones.
        """
        if os.path.isfile(path):
            print(f"{path} is a file.")
            loader = TextLoader(path)

        elif os.path.isdir(path):
            print(f"{path} is a directory.")
            loader = DirectoryLoader(path, glob=f"**/*.{extension}", loader_cls=TextLoader)

        else:
            print(f"{path} does not exist or is a special file (e.g., socket, device file, etc.).")
            return False

        documents = loader.load()
        #print(documents)
        print(f"Documents: {len(documents)}")

        doc_lengths = {doc.metadata['source']: len(doc.page_content) for doc in documents}

        doc_splitter = RecursiveCharacterTextSplitter(
            chunk_size=int(chunk_size), chunk_overlap=int(chunk_overlap)
        )

        documents_chunks = doc_splitter.split_documents(documents)
        print(f"Chunks: {len(documents_chunks)}")

        chunks = [
            Chunk(
                project_name=self.project_name,  # Load project name from environment variable
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
                #print(chunk)
                uuid = generate_uuid5(chunk.model_dump())
                batch.add_object(properties=chunk.model_dump(), uuid=uuid)
                chunks_loaded = chunks_loaded+1

        self.client.close()

        print(f"Loaded chunks: {chunks_loaded}")

    def load_file(self, file_path: str):
        """


        Parameters:
            file_path: The path to the file to be processed.


        """
        allowed_extensions = ['py','yaml','yml','sql','txt','md','pdf']  # List of allowed file extensions
        # Check if the file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"The file {file_path} does not exist.")

            # Check if the file extension is allowed
        file_ext = os.path.splitext(file_path)[1][1:]  # Extract the file extension without the dot
        if file_ext not in allowed_extensions:
            raise ValueError(f"The file extension .{file_ext} is not allowed. Allowed extensions: {allowed_extensions}")

        self.chunk_load_file_or_directory(file_path, file_ext)


    def load_dir(self, dir_path: str, file_ext: str):
        """
        Load files from a specified directory and process them into chunks for database insertion.

        Parameters:
            dir_path: Path to the directory containing files to be processed.
            file_ext: File extension of the files to be processed.

        Raises:
            ValueError: If the directory path does not exist or is not a directory.
        """
        if not os.path.exists(dir_path) or not os.path.isdir(dir_path):
            raise ValueError(f"The path {dir_path} is not a valid directory.")

        self.chunk_load_file_or_directory(dir_path, file_ext)

    def group_by_document_and_source(self, response):
        """
        Groups a list of dictionaries (chunks of data) by their 'document_name' and 'source'.

        This function takes a list of dictionaries where each dictionary represents a chunk of data
        from a document, and it groups these chunks based on their 'document_name' and 'source'
        fields. It uses these fields to create a unique key for grouping. The result is a dictionary
        where each key is a tuple of ('document_name', 'source'), and the value is a list of
        dictionaries (chunks) that belong to that document and source.

        Parameters:
        - response (list of dict): A list where each element is a dictionary containing details of a
          chunk of data. Each dictionary must have 'document_name' and 'source' keys among others.

        Returns:
        - dict: A dictionary with keys as tuples of ('document_name', 'source') and values as lists
          of dictionaries representing the grouped chunks of data.
        """
        # Initialize an empty dictionary to hold the grouped data
        grouped_data = {}
        for item in response.objects:
            # Create a unique key for each document_name and source combination
            key = (item.properties['document_name'], item.properties['source'])

            # Check if this key exists in the dictionary
            if key in grouped_data:
                # If it does, append the current item to the existing list
                grouped_data[key].append(item.properties['content'])
            else:
                # If it does not, create a new list with the current item
                grouped_data[key] = [item.properties['content']]

        return grouped_data

    @search_only
    def kw_search(self, project_name: str, query: str, limit: int = 3) -> dict:
        """
        Perform a keyword search in the Weaviate database.

        Parameters:
            project_name: the nane of the project. All documents must belong to some project.
            query: The search query string.
            limit: The maximum number of search results to return.

        Returns:
            A dictionary containing the search results.
        """

        response = {}
        try:
            response = self.collection.query.bm25(
                query=query,
                query_properties=["content"],
                limit=limit,
                filters=wvc.query.Filter.by_property("project_name").equal(project_name)
            )
        except Exception as e:
            print(f"Weaviate error {e}")
        finally:
            self.client.close()  # Close client gracefully

        logging.info(f"Weaviate search result: {response}")
        return response
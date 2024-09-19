import os
from typing import List, Optional
import re
import pathlib
import ast
from datetime import datetime, timezone
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language
from analitiq.vectordb.schema import Chunk
from analitiq.utils import sql_recursive_text_splitter
from analitiq.utils import keyword_extractions


ROOT = pathlib.Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "services/search_vdb/examples/example_test_files"
ALLOWED_EXTENSIONS = ["py", "yaml", "yml", "sql", "txt", "md", "pdf"]
LOAD_DOC_CHUNK_SIZE = 2000
LOAD_DOC_CHUNK_OVERLAP = 200


def string_to_chunk(chunk: str, metadata: dict) -> Chunk:
    """
    Converts a given chunk of text into a Chunk object using the provided metadata.

    This function takes in a chunk string and a metadata dictionary as parameters and creates an instance of the Chunk class using the provided data and additional generated attributes.

    Parameters:
    ----------
    chunk : str
        The chunk of text to be converted into a Chunk object.

    metadata : dict
        A dictionary containing the required attributes needed to create a Chunk object. The following keys are expected in the dictionary:

        - "source": The source of the chunk text. (Eg. 'host/database')
        - "document_type": The type of the document that the text chunk is part of. (Eg. 'ddl')
        - "document_name": The name of the document that the text chunk is part of. (Eg. 'schema.table')

    Returns:
    -------
    Chunk
        A Chunk object representing the provided text chunk. The Chunk object includes the original text chunk, the source, the document type, the document name, the number of characters in the chunk, the date it was loaded, and the extracted keywords from the chunk content.

    Example Usage:
    ------------
    >>> metadata = {"source": "host/database", "document_type": "ddl", "document_name": "schema.table"}
    >>> chunk = "CREATE TABLE public.users ( id integer NOT NULL, name text NOT NULL);"
    >>> result = string_to_chunk(chunk, metadata)
    >>> print(type(result))
    <class 'Chunk'>
    >>> print(result.content)
    "CREATE TABLE public.users ( id integer NOT NULL, name text NOT NULL);"
    >>> print(result.source)
    'host/database'
    >>> print(result.document_type)
    'ddl'
    >>> print(result.document_name)
    'schema.table'
    """

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


def group_results_by_properties(results: object, group_by_properties: List[str]) -> List:
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
        list[str] : List of string, which are names of the attributes within the Chunk class.

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


def chunk_text(
    text: str,
    chunk_size: int = LOAD_DOC_CHUNK_SIZE,
    chunk_overlap: int = LOAD_DOC_CHUNK_OVERLAP,
    token: str = ",",
) -> List[str]:
    """
    Split the provided text into chunks based on a token.

    This function divides the input text into chunks of defined size. If the specified chunk end happens to split a part that is essential (defined by the token parameter), the function looks back to the previous token and the chunk is split there. The next chunk begins from the end of previous chunk minus the chunk overlap, so this way some of the text from the previous chunk may repeat in the next chunk.

    Parameters:
    ----------
    text : str
        The input string which needs to be divided into chunks.

    chunk_size : int, optional
        The desired size of each chunk. Default is 2000.

    chunk_overlap : int, optional
        The number of characters that consecutive chunks will overlap on. Default is 200.

    token : str, optional
        The function will refrain from splitting the text at these token points.
        If a token falls within the last 200 characters of a chunk, the chunk will end
        on the last token before the chunk size. Default is ",".

    Returns:
    -------
    List[str]
        A list of str where each str is a chunk of approximately 'chunk_size' characters.

    Examples:
    --------
    Suppose 'text' is a string: "Hello, my name is AI. I am a programmer."

    >>> chunk_text(text, chunk_size=15, chunk_overlap=5, token=" ")
        ['Hello, my name', 'my name is AI.', 'is AI. I am', 'AI. I am a', 'am a programmer.']

    Note:
    ----
    Keep in mind the 'chunk_size' is an approximate measure. If a token is found within the
    last 'chunk_overlap' characters of a chunk, the chunk will end there, so some chunks
    can be slightly smaller than the defined 'chunk_size'. Chunks will never be larger
    than 'chunk_size' unless a token is not found.
    """

    text_length = len(text)
    chunks = []

    start = 0
    while start < text_length:
        # Find the next token after the chunk size
        end = start + chunk_size
        if end < text_length:
            end = text.rfind(token, start, end)
            if end == -1:
                end = min(start + chunk_size, text_length)
        chunks.append(text[start:end])
        start = end + 1 - chunk_overlap

    return chunks


class DocumentProcessor:
    """
    DocumentProcessor is a class that provides utilities to process and handle various types of documents.
    It allows you to perform tasks such as checking if a given text is valid Python code or contains SQL statements,
    and chunk documents through the contents while classifying them based on their content.

    Attributes:
    ----------
    project_name : str
        The name of the project.

    Methods:
    --------
    is_python_code(text: str) -> bool:
        Static method that checks if the provided text is a valid Python code.

    is_sql_statements(text: str) -> bool:
        Static method that checks if the provided text contains SQL statements.

    chunk_documents(path: str, extension: Optional[str] = None, chunk_size: int = LOAD_DOC_CHUNK_SIZE,
                    chunk_overlap: int = LOAD_DOC_CHUNK_OVERLAP) -> Tuple[List[Chunk], Dict[str, int]]:
        Instance method that loads documents from a given path, chunks them according to the specified
        parameters, and classifies them based on their content.
    """

    def __init__(self, project_name: str):
        """
        This method is the constructor for the class. It initializes the project_name attribute
        of the object with the provided value.

        Parameters:
        ----------
        project_name : str
            The name of the project.
        """
        self.project_name = project_name

    @staticmethod
    def is_python_code(text: str) -> bool:
        """
        Check if the given text is valid Python code.

        Parameters:
        ----------
        text : str
            The Python code to be checked.

        Returns:
        -------
        bool
            Returns True if the text is valid Python code, False otherwise.
        """
        try:
            ast.parse(text)
            return True
        except SyntaxError:
            pass
        return False

    @staticmethod
    def is_sql_statements(text: str) -> bool:
        """
        Check if the given text contains SQL statements.

        The function uses regular expressions to search for patterns that match to SQL keywords in the given text.

        Parameters:
        ----------
        text : str
            The text to check.

        Returns:
        -------
        bool
            Returns True if the text contains SQL statements, False otherwise.
        """
        # Patterns for SQL code
        sql_patterns = [
            r"\bSELECT\b",  # SELECT statement
            r"\bINSERT\b",  # INSERT statement
            r"\bUPDATE\b",  # UPDATE statement
            r"\bDELETE\b",  # DELETE statement
            r"\bFROM\b",  # FROM clause
            r"\bWHERE\b",  # WHERE clause
            r"\bJOIN\b",  # JOIN clause
            r"--[^\n]*",  # Comments
            r"/\*[\s\S]*?\*/",  # Multiline comments
        ]

        # Check for SQL code patterns
        return any(re.search(pattern, text) for pattern in sql_patterns)

    def chunk_documents(
        self,
        path: str,
        extension: Optional[str] = None,
        chunk_size: int = LOAD_DOC_CHUNK_SIZE,
        chunk_overlap: int = LOAD_DOC_CHUNK_OVERLAP,
    ):
        """
        Loads documents from a given path and chunks them according to the specified parameters.

        This method takes in a path to a directory or a single file, loads the documents found
        (filtered by the provided extension if any), and splits them into chunks using the specified
        chunk size and overlap.

        It categorizes the loaded documents into three distinct groups based on their content: Python code documents,
        SQL statements documents and text documents. Each group of documents is then split into chunks using different
        splitters tailored to the content of each group.

        This method returns a list of these chunk objects, along with a dictionary of the original documents' lengths.

        Parameters:
        ----------
        path : str
            Path to the file or directory containing files to be chunked.

        extension : Optional[str] = None
            File extension to filter the files in the directory. If not provided, all files in the directory will be loaded.

        chunk_size : int = 2000
            The size of chunks in characters into which to split the documents. Default is 2000 characters.

        chunk_overlap : int = 200
            The size in characters of the overlap between consecutive chunks. Default is 200 characters.

        Returns:
        -------
        list of Chunk objects, dict
            A list containing Chunk objects produced from the chunking process, and a dictionary where each entry is
            a source document's name and its corresponding length in characters.

        Raises:
        ------
        FileNotFoundError
            If the specified path does not exist or refers to a special file (e.g., socket, device file, etc.)

        Usage:
        ------
        The method is generally used as part of a document processing pipeline, prior to further text processing tasks or
        storage of chunked documents in a database or filesystem.

        Examples:
        --------
        >>> chunk_documents("./documents", extension=".txt", chunk_size=1000, chunk_overlap=100)
        ([<Chunk object>, <Chunk object>, ...], {"document1": 5000, "document2": 4000, ...})
        """
        if not os.path.exists(path):
            msg = f"The path {path} does not exist."
            raise FileNotFoundError(msg)

        if os.path.isfile(path):
            loader = TextLoader(path)
            extension = os.path.splitext(path)[1][1:]  # Extract the file extension without the dot
        elif os.path.isdir(path):
            loader = DirectoryLoader(path, glob=f"**/*.{extension}", loader_cls=TextLoader)

        else:
            msg = f"{path} does not exist or is a special file (e.g., socket, device file, etc.)."
            raise FileNotFoundError(msg)

        if extension not in ALLOWED_EXTENSIONS:
            error_msg = (
                f"The file extension .{extension} is not allowed. Allowed extensions: {ALLOWED_EXTENSIONS}"
            )
            raise ValueError(error_msg)

        documents = loader.load()
        doc_lengths = {doc.metadata["source"]: len(doc.page_content) for doc in documents}

        python_documents = [
            doc
            for doc in documents
            if self.is_python_code(doc.page_content) and not self.is_sql_statements(doc.page_content)
        ]
        sql_documents = [
            doc
            for doc in documents
            if not self.is_python_code(doc.page_content) and self.is_sql_statements(doc.page_content)
        ]
        text_documents = [
            doc
            for doc in documents
            if not self.is_python_code(doc.page_content) and not self.is_sql_statements(doc.page_content)
        ]

        python_splitter = RecursiveCharacterTextSplitter.from_language(
            language=Language.PYTHON, chunk_size=int(chunk_size), chunk_overlap=int(chunk_overlap)
        )
        python_chunks = python_splitter.split_documents(python_documents)

        sql_splitter = sql_recursive_text_splitter.SQLRecursiveCharacterTextSplitter.from_language(
            language="SQL", chunk_size=int(chunk_size), chunk_overlap=int(chunk_overlap)
        )
        sql_chunks = sql_splitter.split_documents(sql_documents)

        doc_splitter = RecursiveCharacterTextSplitter(
            chunk_size=int(chunk_size), chunk_overlap=int(chunk_overlap)
        )
        documents_chunks = doc_splitter.split_documents(text_documents)

        documents_chunks.extend(python_chunks)
        documents_chunks.extend(sql_chunks)

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

        return chunks

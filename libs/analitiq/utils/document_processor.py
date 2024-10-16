from typing import List, Optional, Tuple
from typing import List, Optional, Tuple
import re
import pathlib
import ast
from datetime import datetime, timezone

from langchain_core.documents.base import Document
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language
from analitiq.databases.vector.schema import Chunk
from analitiq.utils import (
    sql_recursive_text_splitter,
    custom_recursive_json_splitter,
    custom_directory_loader,
    string_loader,
    yaml_loader,
    keyword_extractions,
)
from analitiq.databases.vector.schema import DocumentSchema

ROOT = pathlib.Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "services/search_vdb/examples/example_test_files"
ALLOWED_EXTENSIONS = [".py", ".yaml", ".yml", ".sql", ".txt", ".md", ".pdf"]

LOAD_DOC_CHUNK_SIZE = 2000
LOAD_DOC_CHUNK_OVERLAP = 200

def string_to_chunk(document: DocumentSchema) -> Chunk:
    document_tags = document.document_tags if hasattr(document, "document_tags") else None

    return Chunk(
        content=document.document_content,
        document_uuid=document.uuid,
        document_source=document.document_source,
        document_type=document.document_type,
        document_name=document.document_name,
        document_tags=document_tags,
        document_num_char=len(document.document_content),
        chunk_num_char=len(document.document_content),
        content_kw=keyword_extractions.extract_keywords(document.document_content),
    )


def group_results_by_properties(results: object, group_by_properties: List[str]) -> List:
    """Group a list of dictionaries (chunks of data) by given keys and return the grouped data as a list of dictionaries.

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

    allowed_keys = list(Chunk.model_json_schema()["properties"].keys())

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
    """Split the provided text into chunks based on a token.

    This function divides the input text into chunks of defined size. If the specified chunk end happens to split a part that is essential (defined by the token parameter), the function looks back to the previous token and the chunk is split there. The next chunk begins from the end of previous chunk minus the chunk overlap, so this way some of the text from the previous chunk may repeat in the next chunk.

    Parameters
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

    Returns
    -------
    List[str]
        A list of str where each str is a chunk of approximately 'chunk_size' characters.

    Examples
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
    previous_end = 0
    while start < text_length:
        end = start + chunk_size
        if end < text_length:
            end = text.rfind(token, start, end)
            if previous_end == end:
                end = text.rfind(token, end + 1, start + chunk_size)
            if end == -1:
                end = min(start + chunk_size, text_length)
        if end > text_length:
            end = text_length
        chunks.append(text[start:end])
        start = end + 1 - chunk_overlap
        if end >= text_length:
            break
        previous_end = end

    return chunks


class DocumentProcessor:
    """DocumentProcessor is a class that provides utilities to process and handle various types of documents.

    It allows you to perform tasks such as checking if a given text is valid Python code or contains SQL statements,
    and chunk documents through the contents while classifying them based on their content.

    Attributes
    ----------
    project_name : str
        The name of the project.

    Methods
    -------
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
        """Initialize class.

        This method is the constructor for the class. It initializes the project_name attribute
        of the object with the provided value.

        Parameters
        ----------
        project_name : str
            The name of the project.

        """
        self.project_name = project_name

    @staticmethod
    def is_python_code(text: str) -> bool:
        """Check if the given text is valid Python code.

        Parameters
        ----------
        text : str
            The Python code to be checked.

        Returns
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
        """Check if the given text contains SQL statements.

        The function uses regular expressions to search for patterns that match to SQL keywords in the given text.

        Parameters
        ----------
        text : str
            The text to check.

        Returns
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

    def load_chunk_documents(
        self,
        path: str | pathlib.Path | List[Tuple[str, str]],
        extension: Optional[str] = None,
        chunk_size: int = LOAD_DOC_CHUNK_SIZE,
        chunk_overlap: int = LOAD_DOC_CHUNK_OVERLAP,
    ):
        """Execute loading and chunking of documents."""
        docs = self.load_documents(path, extension=extension)
        chunks = self.chunk_documents(
            docs, extension=extension, chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )
        return chunks

    def load_documents(
        self, inputs: str | pathlib.Path | List[Tuple[str, str]], extension: Optional[str] = None
    ) -> List[Document]:
        """Load Documents from given path and return documents.

        It can also take a list of texts as input as List[Tuple[str,str]].
        For each tuple the first entry is the text and the second the filename
        to use for determining the extension. Extension is only used when directory path is given.
        """
        if isinstance(inputs, (str, pathlib.Path)):
            my_path = pathlib.Path(inputs)
            if not my_path.exists():
                msg = f"The path {my_path.__str__} does not exist."
                raise FileNotFoundError(msg)
            if my_path.is_file():
                if my_path.suffix in (".yml", ".yaml"):
                    loader = yaml_loader.YamlLoader(my_path)
                else:
                    loader = TextLoader(my_path)
            elif my_path.is_dir():
                if not extension:
                    loader = custom_directory_loader.CustomDirectoryLoader(
                        my_path, 
                        glob="**/*.*",
                        glob_loader=TextLoader,
                        special_loaders={".yaml": yaml_loader.YamlLoader, ".yml": yaml_loader.YamlLoader})
                else:
                    msg = f"Extension {extension} not allowed. Allowed Extensions are {ALLOWED_EXTENSIONS}."
                    if extension[0] != ".":
                        extension = "." + extension
                    if extension not in ALLOWED_EXTENSIONS:
                        raise ValueError(msg)
                    loader = custom_directory_loader.CustomDirectoryLoader(
                        my_path, 
                        glob=f"**/*{extension}",
                        glob_loader=TextLoader,
                        special_loaders={".yaml": yaml_loader.YamlLoader, ".yml": yaml_loader.YamlLoader})
            else:
                msg = f"{my_path} does not exist or is a special file (e.g., socket, device file, etc.)."
                raise FileNotFoundError(msg)
        else:
            loader = string_loader.StringDocumentLoader(inputs)

        documents = loader.load()
        files = [
            doc
            for doc in documents
            if pathlib.Path(doc.metadata.get("source", "")).suffix in ALLOWED_EXTENSIONS
        ]
        disallowed_files = [
            pathlib.Path(doc.metadata.get("source", "")).name
            for doc in documents
            if pathlib.Path(doc.metadata.get("source", "")).suffix not in ALLOWED_EXTENSIONS
        ]

        if len(disallowed_files) > 0:
            error_msg = f"""The extensions of following files are not allowed: {disallowed_files}. \n
                Allowed extensions: {ALLOWED_EXTENSIONS}"""
            raise ValueError(error_msg)

        return files

    def chunk_documents(
        self,
        documents: List[Document],
        extension: Optional[str] = None,
        chunk_size: int = LOAD_DOC_CHUNK_SIZE,
        chunk_overlap: int = LOAD_DOC_CHUNK_OVERLAP,
    ):
        """Chunk a list of documents in documents to specified size.

        It categorizes the loaded documents into three distinct groups based on their content: Python code documents,
        SQL statements documents and text documents. Each group of documents is then split into chunks using different
        splitters tailored to the content of each group.

        This method returns a list of these chunk objects, along with a dictionary of the original documents' lengths.

        Parameters
        ----------
        documents : List[Document]
            List of Langchain Documents for chunking.
        extension : Optional[str]
            Optional string with the extension info.
        chunk_size : int = 2000
            The size of chunks in characters into which to split the documents. Default is 2000 characters.
        chunk_overlap : int = 200
            The size in characters of the overlap between consecutive chunks. Default is 200 characters.

        Returns
        -------
        list of Chunk objects, dict
            A list containing Chunk objects produced from the chunking process, and a dictionary where each entry is
            a source document's name and its corresponding length in characters.

        Raises
        ------
        FileNotFoundError
            If the specified path does not exist or refers to a special file (e.g., socket, device file, etc.)

        Usage:
        ------
        The method is generally used as part of a document processing pipeline, prior to further text processing tasks or
        storage of chunked documents in a database or filesystem.

        Examples
        --------
        >>> chunk_documents("./documents", extension=".txt", chunk_size=1000, chunk_overlap=100)
        ([<Chunk object>, <Chunk object>, ...], {"document1": 5000, "document2": 4000, ...})

        """
        doc_lengths = {doc.metadata["source"]: len(doc.page_content) for doc in documents}

        python_documents = [
            doc for doc in documents if pathlib.Path(doc.metadata.get("source", "")).suffix == ".py"
        ]
        sql_documents = [
            doc for doc in documents if pathlib.Path(doc.metadata.get("source", "")).suffix == ".sql"
        ]
        yml_documents = [
            doc
            for doc in documents
            if pathlib.Path(doc.metadata.get("source", "")).suffix in [".yml", ".yaml"]
        ]
        text_documents = [
            doc
            for doc in documents
            if doc not in sql_documents
            if doc not in python_documents
            if doc not in yml_documents
        ]

        python_splitter = RecursiveCharacterTextSplitter.from_language(
            language=Language.PYTHON,
            chunk_size=int(chunk_size),
            chunk_overlap=int(chunk_overlap),
        )
        python_chunks = python_splitter.split_documents(python_documents)

        sql_splitter = sql_recursive_text_splitter.SQLRecursiveCharacterTextSplitter.from_language(
            language="SQL",
            chunk_size=int(chunk_size),
            chunk_overlap=int(chunk_overlap),
        )
        sql_chunks = sql_splitter.split_documents(sql_documents)

        yml_splitter = custom_recursive_json_splitter.CustomRecursiveJsonSplitter(
            max_chunk_size=int(chunk_size)
        )
        yml_chunks = yml_splitter.split_documents(yml_documents)

        doc_splitter = RecursiveCharacterTextSplitter(
            chunk_size=int(chunk_size), chunk_overlap=int(chunk_overlap)
        )
        documents_chunks = doc_splitter.split_documents(text_documents)

        documents_chunks.extend(python_chunks)
        documents_chunks.extend(sql_chunks)
        documents_chunks.extend(yml_chunks)
        chunks = [
            Chunk(
                content=chunk.page_content,
                document_source=chunk.metadata["source"],
                document_type=extension,
                document_name=pathlib.Path(chunk.metadata["source"]).name,
                document_num_char=doc_lengths[chunk.metadata["source"]],
                chunk_num_char=len(chunk.page_content),
                created_ts=datetime.now(timezone.utc),
                content_kw=keyword_extractions.extract_keywords(chunk.page_content),
            )
            for chunk in documents_chunks
        ]
        return chunks

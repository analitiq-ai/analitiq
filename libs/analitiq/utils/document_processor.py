import os
from typing import List, Optional
import re
import pathlib
import ast

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language

from analitiq.utils import sql_recursive_text_splitter

ROOT = pathlib.Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "services/search_vdb/examples/example_test_files"


class DocumentChunkLoader:
    """Initializes a new instance of `DocumentChunkLoader`.

    Parameters
    ----------
        project_name: The name of the project.

    """

    def __init__(self, project_name: str):
        """Initialize the Document Chunkloader."""
        self.project_name = project_name

    def _is_python_code(self, text: str) -> bool:
        """Calculate if the given snippet is sql or python code returns true if so."""
        try:
            ast.parse(text)
            return True
        except SyntaxError:
            pass
        return False

    def _is_sql_statements(self, text: str) -> bool:
        """Calculate if the given text is an sql statement."""
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

    def load_and_chunk_documents(
        self, path: str, extension: Optional[str] = None, chunk_size: int = 2000, chunk_overlap: int = 200
    ):
        """Load files from a directory or a single file, split them into chunks, and return a list of Chunk objects.

        Parameters
        ----------
            path: Path to the file or directory containing files to be chunked.
            extension: File extension to filter the files in the directory.
            chunk_size: The size of chunks into which to split the documents.
            chunk_overlap: How much the chunks should overlap.

        Returns
        -------
            document chunks

        Raises
        ------
            FileNotFoundError: If the specified file does not exist.
            ValueError: If the file's extension is not among the allowed ones.

        """
        if os.path.isfile(path):
            loader: TextLoader | DirectoryLoader = TextLoader(path)
        elif os.path.isdir(path):
            loader = DirectoryLoader(path, glob=f"**/*.{extension}", loader_cls=TextLoader)
        else:
            msg = f"{path} does not exist or is a special file (e.g., socket, device file, etc.)."
            raise FileNotFoundError(msg)

        documents = loader.load()
        doc_lengths = {doc.metadata["source"]: len(doc.page_content) for doc in documents}

        python_documents = [
            doc
            for doc in documents
            if self._is_python_code(doc.page_content) and not self._is_sql_statements(doc.page_content)
        ]
        sql_documents = [
            doc
            for doc in documents
            if not self._is_python_code(doc.page_content) and self._is_sql_statements(doc.page_content)
        ]
        text_documents = [
            doc
            for doc in documents
            if not self._is_python_code(doc.page_content) and not self._is_sql_statements(doc.page_content)
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

        return documents_chunks, doc_lengths

    def chunk_text(
        self, text: str, chunk_size: int = 2000, chunk_overlap: int = 200, token: str = ","
    ) -> List[str]:
        """Split the provided text into chunks based on a token.

        Parameters
        ----------
            text: The text to be chunked.
            chunk_size: The size of chunks into which to split the text.
            chunk_overlap: How much the chunks should overlap.
            token: The token by which to split the text.

        Returns
        -------
            A list of text chunks.

        Raises
        ------
            ValueError: If chunk_size or chunk_overlap is less than 1.
            TypeError: If text is not a string.

        """
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            if end > len(text):
                end = len(text)
            chunk = text[start:end]
            if token and start != 0:
                chunk = token + chunk
            chunks.append(chunk)
            start += chunk_size - chunk_overlap
        return chunks

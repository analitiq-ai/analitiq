import os
from typing import List, Optional
import re
import pathlib
import ast

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from analitiq.utils import sql_recursive_text_splitter

ROOT = pathlib.Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "services/search_vdb/examples/example_test_files"

class DocumentChunkLoader:
    """
    Initializes a new instance of `DocumentChunkLoader`.

    Parameters:
        project_name: The name of the project.
    """
    def __init__(self, project_name: str):
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
            r'\bSELECT\b',         # SELECT statement
            r'\bINSERT\b',         # INSERT statement
            r'\bUPDATE\b',         # UPDATE statement
            r'\bDELETE\b',         # DELETE statement
            r'\bFROM\b',           # FROM clause
            r'\bWHERE\b',          # WHERE clause
            r'\bJOIN\b',           # JOIN clause
            r'--[^\n]*',           # Comments
            r'/\*[\s\S]*?\*/',     # Multiline comments
        ]

        # Check for SQL code patterns
        for pattern in sql_patterns:
            if re.search(pattern, text):
                return True
        return False

    def load_and_chunk_documents(self, path: str, extension: Optional[str] = None, chunk_size: int = 2000, chunk_overlap: int = 200):
        """
        Load files from a directory or a single file, split them into chunks, and return a list of Chunk objects.

        Parameters:
            path: Path to the file or directory containing files to be chunked.
            extension: File extension to filter the files in the directory.
            chunk_size: The size of chunks into which to split the documents.
            chunk_overlap: How much the chunks should overlap.

        Returns:
            document chunks

        Raises:
            FileNotFoundError: If the specified file does not exist.
            ValueError: If the file's extension is not among the allowed ones.
        """
        if os.path.isfile(path):
            loader = TextLoader(path)
        elif os.path.isdir(path):
            loader = DirectoryLoader(path, glob=f"**/*.{extension}", loader_cls=TextLoader)
        else:
            raise FileNotFoundError(f"{path} does not exist or is a special file (e.g., socket, device file, etc.).")

        documents = loader.load()
        doc_lengths = {doc.metadata['source']: len(doc.page_content) for doc in documents}

        python_documents = [doc for doc in documents if self._is_python_code(doc.page_content) and not self._is_sql_statements(doc.page_content)]
        sql_documents = [doc for doc in documents if not self._is_python_code(doc.page_content) and self._is_sql_statements(doc.page_content)]
        text_documents = [doc for doc in documents if not self._is_python_code(doc.page_content) and not self._is_sql_statements(doc.page_content)]

        python_splitter = RecursiveCharacterTextSplitter.from_language(
            language=Language.PYTHON, chunk_size=int(chunk_size), chunk_overlap=int(chunk_overlap))
        python_chunks = python_splitter.split_documents(python_documents)

        sql_splitter = sql_recursive_text_splitter.SQLRecursiveCharacterTextSplitter.from_language(
            language="SQL", chunk_size=int(chunk_size), chunk_overlap=int(chunk_overlap))
        sql_chunks = sql_splitter.split_documents(sql_documents)

        doc_splitter = RecursiveCharacterTextSplitter(chunk_size=int(chunk_size), chunk_overlap=int(chunk_overlap))
        documents_chunks = doc_splitter.split_documents(text_documents)

        documents_chunks.extend(python_chunks)
        documents_chunks.extend(sql_chunks)

        return documents_chunks, doc_lengths

    def chunk_text(self, text: str, chunk_size: int = 2000, chunk_overlap: int = 200, token: str = ',') -> List[str]:
        """
        Split the provided text into chunks based on a token.

        Parameters:
            text: The text to be chunked.
            chunk_size: The size of chunks into which to split the text.
            chunk_overlap: How much the chunks should overlap.
            token: The token by which to split the text.

        Returns:
            A list of text chunks.
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

if __name__ == "__main__":
    chunky = DocumentChunkLoader("my_project")
    result, doc_leng= chunky.load_and_chunk_documents(path=str(EXAMPLES), extension="*", chunk_size=200, chunk_overlap=10)
    print(result)
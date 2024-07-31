import os
from typing import List, Optional
import re
import ast
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language

class DocumentChunkLoader:
    def __init__(self, project_name: str):
        self.project_name = project_name

    def _is_code(self, text: str) -> bool:
        """Calculate if the given snippet is sql or python code returns true if so."""
        try: 
            ast.parse(text)
            return True
        except SyntaxError:
            pass

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
                print("found sql pattern")
                return True
        # If no patterns matched, return False
        return False

    def _text_splitter(self, text: str) -> List[str]:
        """Split up the texts based on paragraphs, sentences or document sites."""

    def _code_splitter(self, text: str) -> List[str]:
        """Split up Code snippets based on functions or Selects and Sub Selects."""

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

        code_documents = [doc for doc in documents if self._is_code(doc.page_content)]
        text_documents = [doc for doc in documents if not self._is_code(doc.page_content)]

        python_splitter = RecursiveCharacterTextSplitter.from_language(
            language=Language.PYTHON, chunk_size=int(chunk_size), chunk_overlap=int(chunk_overlap))
        python_chunks = python_splitter.split_documents(code_documents)

        doc_splitter = RecursiveCharacterTextSplitter(chunk_size=int(chunk_size), chunk_overlap=int(chunk_overlap))
        documents_chunks = doc_splitter.split_documents(text_documents)

        documents_chunks.extend(python_chunks)

        return documents_chunks, doc_lengths

if __name__ == "__main__":
    import pathlib

    ROOT = pathlib.Path(__file__).resolve().parent.parent
    print(ROOT)
    EXAMPLES = ROOT / "services/search_vdb/examples/example_test_files"

    chunky = DocumentChunkLoader("my_project")
    result, doc_leng= chunky.load_and_chunk_documents(path=str(EXAMPLES), extension="*", chunk_size=200, chunk_overlap=10)

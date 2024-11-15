""" SQL Chunker
Filename: analitiq/chunkers/sql_chunker.py

"""
import sqlparse
from typing import Any, List
from langchain_text_splitters import RecursiveCharacterTextSplitter
from analitiq.utils.keyword_extractions import extract_keywords
from analitiq.base.base_chunker import BaseChunker
from analitiq.base.base_chunker import CHUNK_SIZE, CHUNK_OVERLAP
from analitiq.loaders.documents.schemas import  Chunk, DocumentSchema

class SQLChunker(BaseChunker):
    def __init__(self, max_chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP):
        self.max_chunk_size = max_chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk(self, document: DocumentSchema) -> List[Chunk]:
        splitter = SQLRecursiveCharacterTextSplitter(self.max_chunk_size, self.chunk_overlap)
        return splitter.split_documents(document)


class SQLRecursiveCharacterTextSplitter(RecursiveCharacterTextSplitter):
    """A Recursive Character TextSplitter for SQL."""

    def __init__(
            self,
            max_chunk_size: int,
            chunk_overlap: int,
            separators: List[str] | None = None,
            keep_separator: bool = True,
            is_separator_regex: bool = False,
            **kwargs: Any,
    ):
        """Initialize the Textsplitter class."""
        super().__init__(
            separators=separators,
            keep_separator=keep_separator,
            is_separator_regex=is_separator_regex,
            **kwargs,
        )
        self.max_chunk_size = max_chunk_size
        self.chunk_overlap = chunk_overlap

    @classmethod
    def from_language(cls, language: str = "SQL", **kwargs: Any) -> "SQLRecursiveCharacterTextSplitter":
        """Get data from Language."""
        if language.upper() != "SQL":
            errmsg = "This splitter only supports SQL language."
            raise ValueError(errmsg)

        # Define SQL-specific separators
        sql_separators = [
            ";",  # SQL statement terminator
            "\n",  # Newline
            " ",  # Space
            ",",  # Comma
            "(",  # Opening parenthesis
            ")",  # Closing parenthesis
        ]

        return cls(separators=sql_separators, **kwargs)

    def split_text(self, text: str) -> List[str]:
        """Split text by sql statements."""
        # Parse the SQL text using sqlparse
        parsed = sqlparse.parse(text)
        statements = []
        for statement in parsed:
            statements.extend(self._split_statement(str(statement)))
        return statements

    def _split_statement(self, statement: str) -> List[str]:
        """Split text from parent class."""
        # Use the parent class method to split the statement recursively
        return super().split_text(statement)

    def split_documents(self, document: DocumentSchema) -> List[Chunk]:
        """Split a list of documents into chunks.

        Args:
        ----
            documents: A list of dictionaries, each containing a 'text' key.

        Returns:
        -------
            A list of dictionaries, each containing a 'text' key with the split text.

        """
        if document.document_content == '':
            return None

        chunks = self.split_text(document.document_content)

        return_chunks = []
        for chunk in chunks:
            chunk_obj = Chunk(
                content=chunk,
                document_num_char=len(document.document_content),
                document_name=document.metadata.document_name,
                document_uuid = document.uuid,
                chunk_num_char=len(chunk),
                content_kw = extract_keywords(chunk)
            )
            return_chunks.append(chunk_obj)


        return return_chunks
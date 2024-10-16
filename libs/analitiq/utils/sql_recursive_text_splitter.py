from typing import Any, List, Iterable
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.docstore.document import Document
import sqlparse


class SQLRecursiveCharacterTextSplitter(RecursiveCharacterTextSplitter):
    """A Recursive Character TextSplitter for SQL."""

    def __init__(
        self,
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

    def split_documents(self, documents: Iterable[Document]) -> List[Document]:
        """Split a list of documents into chunks.

        Args:
        ----
            documents: A list of dictionaries, each containing a 'text' key.

        Returns:
        -------
            A list of dictionaries, each containing a 'text' key with the split text.

        """
        split_docs: List[Document] = []
        for doc in documents:
            text = doc.page_content
            chunks = self.split_text(text)
            for chunk in chunks:
                split_doc = doc.copy()
                split_doc.page_content = chunk
                split_docs.append(split_doc)
        return split_docs

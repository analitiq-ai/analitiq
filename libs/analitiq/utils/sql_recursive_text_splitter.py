from typing import Any, List, Optional
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.docstore.document import Document
import sqlparse
class SQLRecursiveCharacterTextSplitter(RecursiveCharacterTextSplitter):
    def __init__(self, separators: List[str] | None = None, keep_separator: bool = True, is_separator_regex: bool = False, **kwargs: Any):
        super().__init__(separators=separators, keep_separator=keep_separator, is_separator_regex=is_separator_regex, **kwargs)
        
    @classmethod
    def from_language(cls, language: str = "SQL", **kwargs: Any) -> 'SQLRecursiveCharacterTextSplitter':
        if language.upper() != "SQL":
            raise ValueError("This splitter only supports SQL language.")
        
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
        # Parse the SQL text using sqlparse
        parsed = sqlparse.parse(text)
        statements = []
        for statement in parsed:
            statements.extend(self._split_statement(str(statement)))
        return statements
    
    def _split_statement(self, statement: str) -> List[str]:
        # Use the parent class method to split the statement recursively
        return super().split_text(statement)
    
    def split_documents(self, documents: List[Document]) -> List[Document]:
        """
        Split a list of documents into chunks.

        Args:
            documents: A list of dictionaries, each containing a 'text' key.

        Returns:
            A list of dictionaries, each containing a 'text' key with the split text.
        """
        split_docs: List[Optional[Document]] = []
        for doc in documents:
            text = doc.page_content
            chunks = self.split_text(text)
            for chunk in chunks:
                split_doc = doc.copy()
                split_doc.page_content = chunk
                split_docs.append(split_doc)
        return split_docs

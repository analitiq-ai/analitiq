"""Class for a custom string loader."""

from typing import AsyncIterator, Iterator, List, Tuple

from langchain_core.document_loaders import BaseLoader
from langchain_core.documents import Document


class StringDocumentLoader(BaseLoader):
    """An example document loader that reads a list of tuples with texts line by line."""

    def __init__(self, strings: List[Tuple[str, str]]) -> None:
        """Initialize the loader with a file path.
        Args:
        ----
         strings: List[Tuple[str,str]]
            Input texts as a list whereas the tuple represents each a document text.
            The first entry is the text and the second is the filename including file extension.
        Example:
        -------
        loader = StringDocumentLoader([
        "This is my string to convert to a document", "dummy_filename.txt",
        "This is a second string to convert into a document", "dummy_filename.txt",
        ])
        documents = loader.load()
        """
        self.strings = strings

    def stream(self) -> Iterator[Document]:  # <-- Does not take any arguments
        """Load a file line by line in lazy mode.
        When you're implementing lazy load methods, you should use a generator
        to yield documents one by one.
        """
        for text, source in self.strings:
            yield Document(
                page_content=text,
                metadata={"source": source},
            )
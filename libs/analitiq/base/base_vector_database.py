# File: databases/base/base_vector_database.py

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseVectorDatabase(ABC):
    """Abstract base class for vector database connectors.
    Defines the interface that all vector database connectors should implement.
    """

    @abstractmethod
    def __init__(self, params: Dict[str, Any]):
        pass

    @abstractmethod
    def __enter__(self):
        pass

    @abstractmethod
    def __exit__(self, exc_type, exc_value, traceback):
        pass

    @abstractmethod
    def connect(self):
        """Connect to the vector database."""

    @abstractmethod
    def create_collection(self, collection_name: str) -> str:
        """Create a collection in the vector database."""

    @abstractmethod
    def close(self):
        """Close the connection to the vector database."""

    @abstractmethod
    def load_chunks(self, chunks: List[Any]) -> int:
        """Load chunks into the vector database."""

    @abstractmethod
    def load_file(self, path: str) -> int:
        """Load a file into the vector database."""

    @abstractmethod
    def load_dir(self, path: str, extension: str) -> int:
        """Load files from a directory into the vector database."""

    @abstractmethod
    def kw_search(self, query: str, limit: int = 3) -> Any:
        """Perform a keyword search."""

    @abstractmethod
    def vector_search(self, query: str, limit: int = 3) -> Any:
        """Perform a vector search."""

    @abstractmethod
    def hybrid_search(self, query: str, limit: int = 3) -> Any:
        """Perform a hybrid search."""

    @abstractmethod
    def search_filter(self, query: str, filter_expression: Dict, group_properties: List[str]) -> Any:
        """Perform a search with filters."""

    @abstractmethod
    def filter_count(self, filter_expression: Dict, group_by_prop: str = None) -> Any:
        """Count items with a filter."""

    @abstractmethod
    def filter_group_count(self, filter_expression: Dict, group_by_prop: str = None) -> Any:
        """Count items with a filter."""

    @abstractmethod
    def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection."""

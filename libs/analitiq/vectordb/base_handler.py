from abc import ABC, abstractmethod
from analitiq.logger.logger import logger


class BaseVDBHandler(ABC):
    """A base class for database handlers to manage common functionalities."""

    def __init__(self, params):
        """Initialize the Base Class."""
        self.params = params

        self.collection_name = params["collection_name"]
        self.client = None
        self.connected = False

    def connect(self):
        """Connect to the database. This method should be implemented by subclasses."""
        errmsg = "Connect method not implemented."
        raise NotImplementedError(errmsg)

    def close(self):
        """Close the database connection. This method should be implemented by subclasses."""
        errmsg = "Execute query method not implemented."
        raise NotImplementedError(errmsg)

    def try_connect(self):
        """Attempt to connect to the database. Returns None if the connection fails."""
        try:
            self.connect()
            self.connected = True
        except Exception as e:
            logger.error({e})
            self.connected = False
            return None
        return self

    @abstractmethod
    def create_collection(self, collection_name: str) -> str:
        """Create a collection."""
        pass

    @abstractmethod
    def delete_collection(self, collection_name: str):
        """Delete the entire collection."""
        pass

    def update_collection(self):
        """Delete the entire collection."""
        errmsg = "Update collection method not implemented."
        raise NotImplementedError(errmsg)

    @abstractmethod
    def hybrid_search(self, collection_name: str):
        pass


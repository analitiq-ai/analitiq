from typing import Optional
from analitiq.logger.logger import logger


class BaseVDBHandler:
    """
    A base class for database handlers to manage common functionalities.
    """

    def __init__(self, params):
        self.params = params

        self.collection_name = params['collection_name']
        self.client = None
        self.connected = False

    def connect(self):
        """
        Connect to the database. This method should be implemented by subclasses.
        """
        raise NotImplementedError("Connect method not implemented.")

    def close(self):
        """
        Close the database connection. This method should be implemented by subclasses.
        """
        raise NotImplementedError("Execute query method not implemented.")

    def try_connect(self):
        """
        Attempt to connect to the database. Returns None if the connection fails.
        """
        try:
            self.connect()
            self.connected = True
        except Exception as e:
            logger.error({e})
            self.connected = False
            return None
        return self

    def delete_collection(self):
        """
        Deletes the entire collection.

        :return: None
        """
        raise NotImplementedError("Delete collection method not implemented.")
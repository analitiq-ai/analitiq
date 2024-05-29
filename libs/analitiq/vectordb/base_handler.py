import logging


class BaseVDBHandler:
    """
    A base class for database handlers to manage common functionalities.
    """

    def __init__(self, params):
        self.params = params
        self.project_name = params['collection_name']
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
            logging.error(f"{self.params['type']} connection failed: {e}")
            self.connected = False
            return None
        return self

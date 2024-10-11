# factories/relational_database_factory.py
import importlib


class RelationalDatabaseFactory:
    """Factory class for creating instances of different relational database types.

    :param params: additional keyword arguments to pass to the database class constructor.

    :return: Instance of the specified database class.

    :raises ValueError: If the specified database type is unknown or not supported.

    Example usage:

    .. code-block:: python

        factory = DatabaseFactory()
        db = factory.connect("mysql", host="localhost", port=3306, user="root", password="password")

    """

    @staticmethod
    def connect(params: dict):
        if "type" not in params:
            raise KeyError("'type' not found in params. Please specify database type")

        db_type = params["type"]
        """Factory function to create a database wrapper instance based on db_type."""
        module_path = f"analitiq.databases.relational.{db_type}.{db_type}_connector"
        class_name = f"{db_type.capitalize()}Connector"

        try:
            module = importlib.import_module(module_path)
            database_class = getattr(module, class_name)
            return database_class(params)
        except (ImportError, AttributeError) as e:
            raise ValueError(f"Unknown relational database type: {db_type}") from e

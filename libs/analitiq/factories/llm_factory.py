# factories/llm_factory.py
import importlib


class LlmFactory:
    """
    Factory class for creating instances of different large language model types.

    :param params: additional parameters to pass to the llm class constructor.

    :return: Instance of the specified database class.

    :raises ValueError: If the specified database type is unknown or not supported.

    Example usage:

    .. code-block:: python

        factory = LlmFactory()
        db = factory.create_llm(params)

    """
    @staticmethod
    def create_llm(params: dict):
        if 'type' not in params:
            raise KeyError("'type' not found in params. Please specify llm type")

        llm_type = params['type']

        """Factory function to create a database wrapper instance based on db_type."""
        module_path = f"analitiq.llms.{llm_type}.{llm_type}_connector"
        class_name = f"{llm_type.capitalize()}Connector"

        try:
            module = importlib.import_module(module_path)
            database_class = getattr(module, class_name)
            return database_class(params)
        except (ImportError, AttributeError) as e:
            raise ValueError(f"Unknown llm type: {llm_type}") from e


from typing import List, Any, Dict


class BaseService:
    """
    Placeholder BaseService
    """



    def run(self, service_input=None):
        """
        The main execution method for the service which should be implemented by derived classes.

        Args:
            service_input: The input data for the service. This could be the output of another service.

        Raises:
            NotImplementedError: If the subclass does not implement this method.
        """
        raise NotImplementedError("Each service must implement a 'run' method.")


class BaseResponse:
    """A class to encapsulate the response of service operations.

    Attributes:
        content (Any): The main content of the response, typically a DataFrame.
        metadata (Dict): Metadata about the operation, including relevant tables and executed SQL.
    """
    def __init__(self, content: Any, metadata: Dict):
        self.content = content
        self.metadata = metadata
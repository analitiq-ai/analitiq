from typing import List, Any, Dict


class BaseService:

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
    def __init__(self, content: Any, metadata: Dict, error: str = None):
        self.content = content
        self.metadata = metadata
        self.error = metadata

    def __str__(self):
        content_str = str(self.content)
        metadata_str = ', '.join(f"{key}: {value}" for key, value in self.metadata.items())
        return f"Content: {content_str}\nMetadata: {metadata_str}"

    def print_details(self):
        print(self.__str__())

    def add_llm_msg(self, msg):
        self.content = msg
        self.metadata['format'] = 'text'

    def add_error(self, msg):
        self.content = msg
        self.metadata['format'] = 'text'

    def get_content_str(self):
        if self.metadata['format'] == 'dataframe':
            return self.content.to_json(orient='split')
        else:
            return str(self.content)
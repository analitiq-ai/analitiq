from typing import List, Any, Dict
import json

class BaseResponse:
    """A class to encapsulate the response of service operations.

    Attributes:
        content (Any): The main content of the response, typically a DataFrame.
        metadata (Dict): Metadata about the operation, including relevant tables and executed SQL.
    """
    ALLOWED_FORMATS = ["text", "dataframe", "json", "sql"]

    def __init__(self, service_name: str):
        self.service_name = service_name
        self.content = None
        self.content_format = None
        self.metadata = {}
        self.error = None

    def __str__(self):
        content_str = str(self.content)
        metadata_str = ', '.join(f"{key}: {value}" for key, value in self.metadata.items())
        return f"Content: {content_str}\nMetadata: {metadata_str}"

    def print_details(self):
        print(self.__str__())

    def get_content_str(self):
        if self.content_format == 'dataframe':
            return str(self.content.to_json(orient='split'))
        elif self.content_format == 'json':
            return json.dumps(self.content)
        elif self.content_format == 'sql':
            return str(self.content) + ";\n"
        else:
            return str(self.content)

    def set_content(self, msg: str, msg_format: str = 'text'):
        # validate the passed msg_format
        if msg_format not in self.ALLOWED_FORMATS:
            raise ValueError(f"Invalid response content format: {msg_format}. Expected one of {self.ALLOWED_FORMATS}")
        self.content = msg
        self.content_format = msg_format

    def set_metadata(self, metadata: dict):
        self.metadata.update(metadata)

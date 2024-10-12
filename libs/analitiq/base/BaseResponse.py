import json
from enum import Enum


class AllowedFormats(str, Enum):
    TEXT = "text"
    DATAFRAME = "dataframe"
    JSON = "json"
    SQL = "sql"


class BaseResponse:
    """A class to encapsulate the response of service operations.

    Attributes
    ----------
        content (Any): The main content of the response, typically a DataFrame.
        metadata (Dict): Metadata about the operation, including relevant tables and executed SQL.

    """

    def __init__(self, service_name: str):
        self.service_name = service_name
        self.content = None
        self.content_format = None
        self.metadata: dict = {}
        self.error: str = None

    def __str__(self):
        content_str = str(self.content)
        metadata_str = ", ".join(f"{key}: {value}" for key, value in self.metadata.items())
        return f"Content: {content_str}\nMetadata: {metadata_str}"

    def to_json(self):
        """Returns a JSON string representation of the object.

        :return: A JSON string representation of the object.
        :rtype: str
        """
        return {
            "content": self.get_content_str(),
            "content_format": self.content_format,
            "metadata": self.metadata
            }

    def print_details(self):
        pass

    def get_content_str(self):
        if self.content_format == AllowedFormats.DATAFRAME:
            return str(self.content.to_json(orient="split"))
        elif self.content_format == AllowedFormats.JSON:
            return json.dumps(self.content)
        elif self.content_format == AllowedFormats.SQL:
            return str(self.content) + ";\n"
        else:
            return str(self.content)

    def set_content(self, msg: str, msg_format: str = "text"):
        # validate the passed msg_format
        if msg_format not in AllowedFormats._value2member_map_:
            msg = f"Invalid response content format: {msg_format}. Expected one of {[item.value for item in AllowedFormats]}"
            raise ValueError(msg)
        self.content = msg
        self.content_format = msg_format

    def set_metadata(self, metadata: dict):
        """Update the metadata of an object with the given metadata.

        :param metadata: A dictionary containing the metadata to be updated.
        :type metadata: dict
        :return: None
        """
        self.metadata.update(metadata)

    def add_text_to_metadata(self, content, content_format: str = "text"):
        """:param content: The content to be added to the metadata dictionary.
        :return: None

        Add the given text to the existing value of the 'text' key in the metadata dictionary. If the 'text' key does not exist in the metadata dictionary, create a new key-value pair with the
        * 'text' key and the given text value.
        """
        # validate the passed format
        if content_format not in AllowedFormats._value2member_map_:
            raise ValueError(f"Invalid format: {content_format}. Expected one of {[items.value for items in AllowedFormats]}")

        if content_format in self.metadata:
            self.metadata[content_format] += "\n" + content
        else:
            self.metadata[content_format] = content

import json


class BaseResponse:
    """A class to encapsulate the response of service operations.

    Attributes
    ----------
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
        metadata_str = ", ".join(
            f"{key}: {value}" for key, value in self.metadata.items()
        )
        return f"Content: {content_str}\nMetadata: {metadata_str}"

    def to_json_str(self):
        """Returns a JSON string representation of the object.

        :return: A JSON string representation of the object.
        :rtype: str
        """
        return json.dumps(
            {"content": self.get_content_str(), "metadata": self.metadata}
        )

    def to_json(self):
        """Returns a JSON string representation of the object.

        :return: A JSON string representation of the object.
        :rtype: str
        """
        return {"content": self.get_content_str(), "metadata": self.metadata}

    def print_details(self):
        pass

    def get_content_str(self):
        if self.content_format == "dataframe":
            return str(self.content.to_json(orient="split"))
        elif self.content_format == "json":
            return json.dumps(self.content)
        elif self.content_format == "sql":
            return str(self.content) + ";\n"
        else:
            return str(self.content)

    def set_content(self, msg: str, msg_format: str = "text"):
        # validate the passed msg_format
        if msg_format not in self.ALLOWED_FORMATS:
            msg = f"Invalid response content format: {msg_format}. Expected one of {self.ALLOWED_FORMATS}"
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

    def add_text_to_metadata(self, text):
        """:param text: The text to be added to the metadata dictionary.
        :return: None

        Add the given text to the existing value of the 'text' key in the metadata dictionary. If the 'text' key does not exist in the metadata dictionary, create a new key-value pair with the
        * 'text' key and the given text value.
        """
        key = "text"
        if key in self.metadata:
            self.metadata[key] += "\n" + text
        else:
            self.metadata[key] = text

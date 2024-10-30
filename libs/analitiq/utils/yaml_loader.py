"""Class for a custom string loader."""

from typing import Iterator, List, Tuple
import pathlib

import json
import yaml

from langchain_core.document_loaders import BaseLoader
from langchain_core.documents import Document


class YamlLoader(BaseLoader):
    """An example YAML Loader to load a YAML File and interpret it as a dictionary."""

    def __init__(self, file_path: str | pathlib.Path) -> None:
        """Initialize the loader with a file path.

        Args:
        ----
         file_path: str | pathlib.Path
            Input path to a yaml file

        Example:
        -------
        loader = YamlLoader("my_file_path.yaml")
        document = loader.load()

        ExampleFileInput:
        ----------------
        '''
        ---
        key1: value
        key2:
          - value1
          - value2

        ExampleResult:
        -------------
        "{'key1':'value', 'key2': ['value1','value2']}"

        """
        self.file_path = str(file_path)

    def lazy_load(self) -> Iterator[Document]:  # <-- Does not take any arguments
        """Load a yaml file in lazy mode.

        When you're implementing lazy load methods, you should use a generator
        to yield documents one by one.
        """
        with open(self.file_path, encoding="utf-8") as f:
            yaml_data = yaml.safe_load(f)
            yield Document(
                page_content=json.dumps(yaml_data),
                metadata={"source": self.file_path},
            )

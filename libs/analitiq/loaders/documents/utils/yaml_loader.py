"""Class for a custom string loader."""

from typing import List
import pathlib
import json
import yaml
from pathlib import Path
from langchain_core.document_loaders import BaseLoader
from analitiq.loaders.documents.schemas import DocumentSchema, DocumentMetadata, ALLOWED_EXTENSIONS
from analitiq.loaders.documents.utils.common_loader_funcs import split_filename, get_document_type
from analitiq.agents.sql.sql_agent import logger
from langchain_core.documents.base import Document


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
        logger.info("YAML loader initialized")
        self.file_path = Path(file_path)
        self.file_name = self.file_path.name
        suffix = self.file_path.suffix
        self.extension = suffix[1:] if suffix.startswith('.') else suffix
        if not self.file_path.exists():
            raise FileNotFoundError(f"The file {self.file_path} does not exist.")
        if self.extension not in ALLOWED_EXTENSIONS:
            raise ValueError(f"Extension {self.extension} not allowed. Allowed extensions are {ALLOWED_EXTENSIONS}.")

    def lazy_load(self) -> List[DocumentSchema]:
        """Load a yaml file in stream mode.

        When you're implementing stream load methods, you should use a generator
        to yield documents one by one.
        """
        with open(self.file_path, encoding="utf-8") as f:
            yaml_data = yaml.safe_load(f)

            #Yaml loader should return the same Document object as Text Loaders for consistency
            return [Document(page_content=json.dumps(yaml_data),
                               metadata={"document_name": self.file_name,
                                   "document_type": get_document_type(self.extension)
                                }
                            )
                    ]

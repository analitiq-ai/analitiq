from typing import List, Optional, Dict
import pathlib
from langchain_core.documents import Document
from langchain_core.document_loaders import BaseLoader

class CustomDirectoryLoader:
    """Custom Directory Loader class to implement own logic in loading a complete Directory.

    Loading a whole Directory with the specified glob_loader. Can define loaders for specific suffixes.
    E.g. for .yaml files.
    """

    def __init__(self, directory_path: str | pathlib.Path, glob: str = "**/*.*", glob_loader=BaseLoader,
                 special_loaders: Optional[Dict[str, BaseLoader]]= None):
        """Initialize the loader with a directory path and a glob pattern.

        :param directory_path: Path to the directory containing files to load.
        :param glob: Glob pattern to match files within the directory.
        :param glob_loader: Mode to use with UnstructuredFileLoader ('single', 'elements', or 'paged').
        :param special_loader: Special loaders for specific requests. Given in dict as key the suffix of files
        and the loader as value to use for these files.

        Example:
        -------
        loader = CustomDirectoryLoader("your_path_to_dir", glob = "**/*.*", glob_loader=TextLoader,
                specific_loaders={".yaml":YamlLoader, ".csv":CsvLoader}
        )

        """
        self.directory_path = pathlib.Path(directory_path)
        self.glob_pattern = glob
        self.glob_loader = glob_loader
        self.special_loaders = special_loaders
        self.excluded_pattern: Optional[List[str]] = None
        if special_loaders:
            excluded_pattern = [pattern for pattern, _loader in special_loaders.items()]
            self.excluded_pattern = excluded_pattern

    def load(self) -> List[Document]:
        """Load all files matching the glob pattern in the directory using UnstructuredFileLoader.

        :return: List of Document objects loaded from the files.
        """
        documents = []
        for file_path  in self.directory_path.glob(self.glob_pattern):
            if file_path.suffix not in self.excluded_pattern:
                loader = self.glob_loader(file_path=file_path)
            else:
                loader = self.special_loaders[file_path.suffix](file_path=file_path)
            docs = loader.load()
            documents.extend(docs)
        return documents

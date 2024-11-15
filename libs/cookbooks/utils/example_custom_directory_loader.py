"""File shows the usage of the custom direcotry processor and how to load multiple documents at once.

You just need to specify the part to the directory with the files and to specify the standard loader.
If you need a specific loader for a filetype ( like yaml or yml you need to specify it for each suffix).
"""
import pathlib

from langchain_community.document_loaders import TextLoader
from langchain_core.documents.base import Document

from analitiq.utils import custom_directory_loader
from analitiq.loaders.documents.utils.yaml_loader import YamlLoader

path_to_files = pathlib.Path("file").resolve().parent / "example_files"
loader = custom_directory_loader.CustomDirectoryLoader(
    directory_path=path_to_files,
    glob="**/*.*",
    glob_loader=TextLoader,
    special_loaders={".yml":YamlLoader,".yaml":YamlLoader}
)

documents = loader.load()

for doc in documents:
    assert isinstance(doc, Document)

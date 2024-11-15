from typing import List
import re
import pathlib
import ast
from datetime import datetime, timezone
from analitiq.loaders.documents.schemas import  Chunk


ROOT = pathlib.Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "services/search_vdb/examples/example_test_files"


def group_results_by_properties(results: object, group_by_properties: List[str]) -> List:
    """Group a list of dictionaries (chunks of data) by given keys and return the grouped data as a list of dictionaries.

    Each dictionary in the returned list corresponds to a unique group as determined by `group_by_properties`. The keys of the
    dictionaries are the group properties and a special key 'document_chunks' which stores the associated chunks of data.

    Args:
    ----
        results (Response): The original response object that includes 'objects' which is
            a list of items, each having properties from which keys values are extracted.
        group_by_properties (list[str]): List of properties which are used to group data.

    Raises:
    ------
        ValueError: If any key in `group_keys` is not in `allowed_keys`.

    Returns:
    -------
        list[str] : List of string, which are names of the attributes within the Chunk class.

    Example:
    -------
        Given group_keys=['document_name', 'source'] and this item in `response.objects`:

        { 'properties' :
           { 'document_name': 'doc1', 'source' : 'src1', 'content': 'content1' }
        } ...

        The output will be:

        [
            {
               "document_name": "doc1",
               "source": "src1",
               "document_chunks": ['content1', ...]
            },
           ...
        ]

    """
    if not results.objects:
        return None

    allowed_keys = list(Chunk.model_json_schema()["properties"].keys())

    if not set(group_by_properties).issubset(set(allowed_keys)):
        msg = f"The provided keys for grouping are not allowed. Allowed keys are: {allowed_keys}"
        raise ValueError(msg)

    grouped_data = {}
    # put all chunks into the same key.
    for item in results.objects:
        key = tuple(item.properties[k] for k in group_by_properties)
        if key in grouped_data:
            grouped_data[key].append(item.properties["content"])
        else:
            grouped_data[key] = [item.properties["content"]]

    # format the data into more explicit dictionary
    reformatted_data = []
    for key, value in grouped_data.items():
        data_dict = {"document_chunks": value}
        # key is a tuple, so we use enumerate to get indexes and use them to fetch property names
        for idx, item in enumerate(key):
            data_dict[group_by_properties[idx]] = item
        reformatted_data.append(data_dict)
    return reformatted_data


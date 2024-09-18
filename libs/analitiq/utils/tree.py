from pathlib import Path

# prefix components:
space = "    "
branch = "│   "
# pointers:
tee = "├── "
last = "└── "


def tree(dir_path: Path, prefix: str = ""):
    """
    Generate a formatted string representation of a directory tree.

    This function traverses a given directory and generates a formatted string representation of its structure, similar
    to the output of `tree` command in Unix. It ignores directories and files that start with ".", "__", "venv", and "env".
    It is a recursive function which uses depth-first search to traverse all the directories. When a directory is encountered,
    this function is called recursively with an updated prefix.

    Parameters:
    ----------
    dir_path : Path
        The Path object of the directory to be traversed.

    prefix : str, optional
        The prefix to be added before each file/folder name in the tree structure (default is "").

    Returns:
    -------
    generator
        A generator that yields each line of the tree structure as a formatted string.

    Example:
    --------
    ```python
    from pathlib import Path

    dir_path = Path('/path/to/directory')
    tree_generator = tree(dir_path)

    for line in tree_generator:
        print(line)
    ```
    In this example, if "/path/to/directory" contains a subdirectory "subdir" and a file "file.txt",
    the output could be (for example):

    ```
    ├── subdir
    │   └── file_inside_subdir.txt
    └── file.txt
    ```
    """

    prefixes = [".", "__", "venv", "env"]
    contents = list(dir_path.iterdir())
    # contents each get pointers that are ├── with a final └── :
    pointers = [tee] * (len(contents) - 1) + [last]
    for pointer, path in zip(pointers, contents):
        if any(path.name.startswith(prefix) for prefix in prefixes):
            continue
        yield prefix + pointer + path.name
        if path.is_dir():  # extend the prefix and recurse:
            extension = branch if pointer == tee else space
            # i.e. space because last, └── , above so no more |
            yield from tree(path, prefix=prefix + extension)


if __name__ == "__main__":
    # Create a Path object for the directory
    dir_path = Path("/Users/kirillandriychuk/Documents/Projects/analitiq")

    # Generate the tree structure
    tree_generator = tree(dir_path)

    # Iterate over the generator and print each line
    for _line in tree_generator:
        print(line)

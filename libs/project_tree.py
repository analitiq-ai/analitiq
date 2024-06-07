from analitiq.utils.tree import *
from pathlib import Path
print()
for line in tree(Path.home() / 'Documents/Projects/analitiq/libs'):
    print(line)
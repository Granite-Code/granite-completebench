from contextlib import contextmanager
import json
from pathlib import Path
from typing import IO


def read_json(path: Path):
    with open(path, "r", encoding="utf8") as f:
        return json.load(f)

def write_json(path: Path, obj, create_parents=False):
    if create_parents:
        path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", newline="\n", encoding="utf8") as f:
        json.dump(obj, f, indent=2)

class JsonlWriter():
    def __init__(self, file: IO[str]):
        self._file = file

    def append(self, object):
        self._file.write(json.dumps(object))
        self._file.write("\n")

@contextmanager
def write_jsonl(path: Path, create_parents=False):
    if create_parents:
        path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", newline="\n", encoding="utf8") as f:
        yield JsonlWriter(f)

def read_jsonl(path: Path):
    for line in path.open("r", encoding="utf8"):
        yield json.loads(line)

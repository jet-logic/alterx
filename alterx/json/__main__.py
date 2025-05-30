from argparse import ArgumentParser
from typing import Sequence
from ..app import App
from ..main import flag
from ..utils import HashSink


class AlterJSON(App):
    tag = "JSON"
    default_glob_includes = (r"*.json", r"*.jsn")

    def parse_source(self, src: object) -> object:
        from json import load

        return load(src)

    def hash_of(self, doc: object) -> str:

        from json import dump

        h = HashSink()
        dump(doc, h)
        return h.digest.hexdigest()


(__name__ == "__main__") and AlterJSON().main()

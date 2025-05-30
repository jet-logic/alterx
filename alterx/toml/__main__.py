from argparse import ArgumentParser
from typing import Sequence
from ..app import App
from ..main import flag
from ..utils import HashSink


class AlterToml(App):
    tag = "TOML"
    default_glob_includes = (r"*.toml", r"*.tml")

    def parse_source(self, src: object) -> object:
        from tomlkit import load

        return load(src)

    def hash_of(self, doc: object) -> str:
        from tomlkit import dump

        h = HashSink()
        dump(doc, h)
        return h.digest.hexdigest()


(__name__ == "__main__") and AlterToml().main()

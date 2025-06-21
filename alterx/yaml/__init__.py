from ..app import App
from ..utils import HashSink


import yaml


class AlterYAML(App):
    tag = "YAML"
    default_glob_includes = (r"*.yaml", r"*.yml")

    def parse_source(self, src: object) -> object:
        return yaml.safe_load(src)

    def hash_of(self, doc: object) -> str:
        h = HashSink()
        yaml.dump(doc, h, encoding="utf-8")
        return h.digest.hexdigest()

    def dump(self, doc: object, out: object, encoding: str):
        yaml.dump(doc, out, encoding="utf-8")

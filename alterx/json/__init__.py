from ..app import App
from ..utils import HashSinkText
import json


class AlterJSON(App):
    tag = "JSON"
    default_glob_includes = (r"*.json", r"*.jsn")

    def parse_source(self, src: object) -> object:
        return json.load(src)

    def hash_of(self, doc: object) -> str:
        h = HashSinkText()
        json.dump(doc, h)
        return h.digest.hexdigest()

    def sink_file(self, src, encoding=None):
        return open(src, "w", encoding=encoding or "utf-8")

    def dump(self, doc: object, out: object, encoding: str):
        json.dump(doc, out)

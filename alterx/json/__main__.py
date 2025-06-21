from ..app import App
from ..utils import HashSink
import json


class AlterJSON(App):
    tag = "JSON"
    default_glob_includes = (r"*.json", r"*.jsn")

    def parse_source(self, src: object) -> object:
        return json.load(src)

    def hash_of(self, doc: object) -> str:
        h = HashSink()
        json.dump(doc, h)
        return h.digest.hexdigest()

    def dump(self, doc: object, out: object, encoding: str):
        json.dump(doc, out)


(__name__ == "__main__") and AlterJSON().main()

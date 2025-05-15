from . import Data, HashSink
from .main import main

class Json(Data):
    id = "json"
    name_re = r"\.(json)$"

    def parse_file(self, src, app):
        from json import load

        with open(src, "r") as stream:
            return load(stream)

    def hash_of(self, O):
        from json import dump

        h = HashSink()
        dump(O, h)
        return h.h.hexdigest()

    def dump(O, out, encoding, app):
        from json import dump

        dump(O, out, ensure_ascii=encoding and encoding.lower().find("ascii") >= 0)

    def supply_argparse(self, parser):
        super().supply_argparse(parser)
        parser.description = "Alters JSON files"


__name__ == "__main__" and main(Json())

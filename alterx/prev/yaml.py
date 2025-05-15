from . import Data, HashSink
from .main import main


class Yaml(Data):
    id = "yaml"
    name_re = r"\.(ya?ml)$"
    # dump
    allow_unicode = True
    sort_keys = False

    def parse_file(self, src, app):
        from yaml import safe_load

        with open(src, "r") as stream:
            return safe_load(stream)

    def hash_of(self, O):
        from yaml import safe_dump

        h = HashSink()
        safe_dump(O, h, encoding="utf-8")
        return h.h.hexdigest()

    def dump(self, O, out, encoding, app):
        from yaml import safe_dump

        safe_dump(
            O,
            out,
            encoding=encoding,
            allow_unicode=self.allow_unicode,
            sort_keys=self.sort_keys,
        )

    def supply_argparse(self, parser):
        super().supply_argparse(parser)
        parser.description = "Alters YAML files"


__name__ == "__main__" and main(Yaml())

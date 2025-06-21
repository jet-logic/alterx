from ..app import App


from tomlkit import dumps, load


from hashlib import md5


class AlterToml(App):
    tag = "TOML"
    default_glob_includes = (r"*.toml", r"*.tml")

    def parse_source(self, src: object) -> object:
        return load(src)

    def hash_of(self, doc: object) -> str:
        h = md5()
        h.update(dumps(doc).encode())
        return h.hexdigest()

    def dump(self, doc: object, out: object, encoding: str):
        out.write(dumps(doc).encode())

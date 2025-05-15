from . import HtmlFiles


def abs2rel(path, base):
    try:
        return relpath(path, base)
    except ValueError:
        return path


class App(HtmlFiles):
    def _get_httpc(self):
        from requests_cache import CachedSession
        from sys import stderr

        _httpc = CachedSession("http_cache", backend="sqlite", use_cache_dir=True)

        print(f"HTTPC: init", file=stderr)
        return _httpc

    def arguments(self, ap):
        self.seen = {}
        self.save_dir = None
        ap.add_argument("--save-dir", help="save directory")
        ap.add_argument("--root-dir", help="root directory")
        if not ap.description:
            ap.description = "Save links of html files"
        super().arguments(ap)

    def ready(self):
        from pathlib import Path

        self.dir_save = None
        if not self.save_dir and not self.root_dir:
            for i, p in enumerate(self.paths):
                if "//" in p:
                    rite, sep, left = p.partition("//")
                    self.root_dir = rite
                    self.save_dir = f"{rite}{sep[0]}{left}"
                    self.paths[i] = rite
                    break

        if not self.save_dir and self.root_dir and "//" in self.root_dir:
            rite, sep, left = self.root_dir.partition("//")
            self.root_dir = rite
            self.save_dir = f"{rite}{sep[0]}{left}"

        if self.save_dir:
            if self.root_dir:
                self.dir_save = Path(self.root_dir) / Path(self.save_dir)
            else:
                self.dir_save = Path(self.save_dir)

        # print(self.root_dir)

        super().ready()

    def on_tree(self, doc, this):
        root = doc.getroot()
        seen = self.seen

        links = root.iterlinks()
        # print(args)

        def ff(v):
            (element, attribute, link, pos) = v

            if not attribute:
                if link.startswith("urn:not-loaded:"):
                    return False
                return True
            elif attribute in ("src", "background"):
                return True
            elif attribute in ("href",):
                if element.tag == "link":
                    rel = element.get("rel") or ""
                    return rel.find("icon") >= 0 or rel.find("stylesheet") >= 0
            elif attribute in ("archive", "codebase", "code"):
                return element.tag == "applet"

        def enum():
            yield from filter(ff, links)

        for element, attribute, link, pos in enum():
            if not link:
                continue
            u = urlsplit(link)
            if u[2] and u[2].startswith("/"):
                pass
            else:
                continue
            if not u[0]:  # scheme
                if u[1]:  # netloc
                    link = urlunsplit(["https", *u[1:]])
            # print("OKS", u[2], attribute, link)
            name = seen.get(link)
            if name is None:
                _, suffix = splitext(u[2])
                h = md5()
                h.update(link.encode("utf-8"))
                seen[link] = name = (
                    b32encode(h.digest()).lower().strip(b"=").decode() + suffix
                )
            else:
                assert name
            if self.save_dir:
                res_file = join(self.save_dir, name)
                src = pathname2url(abs2rel(res_file, dirname(this.path)))
                if self.root_dir:
                    from_root = relpath(res_file, self.root_dir)
                    assert not (
                        from_root.startswith(".") or from_root.startswith("/")
                    ), f"from_root={from_root!r} root_dir={self.root_dir!r} res_file={res_file!r} save_dir={self.save_dir!r}"
            else:
                res_file = None
                src = name
            if res_file:
                if not exists(res_file):
                    print(f"Fetch {link!r} --> {res_file}")
                    if self.dry_run is False:
                        r = self.httpc.get(link)
                        s = r.status_code
                        if s == 200:
                            d = dirname(res_file)
                            exists(d) or makedirs(d)
                            with open(res_file, "wb") as w:
                                w.write(r.content)
                if element is not None and attribute and src:
                    print(f"Set {element.tag}.{attribute}={src!r}")
                    element.attrib[f"{attribute}-old"] = link
                    element.attrib[attribute] = src


from sys import stdout, stderr
from os import environ, makedirs
from urllib.parse import urlsplit, urlunsplit
from hashlib import md5
from base64 import b32encode
from os.path import splitext, relpath, join, dirname, exists
from urllib.request import pathname2url

__name__ == "__main__" and App().main()

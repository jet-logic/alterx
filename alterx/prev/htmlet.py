from . import HtmlFiles


def loadModule(ctx, value):
    from imp import find_module, load_module
    from os.path import splitext, basename, isfile, dirname

    (mo, parent, title) = (None, dirname(value), basename(value))
    if isfile(value):
        (title, _) = splitext(title)
    if parent:
        mo = find_module(title, [parent])
    else:
        mo = find_module(title)
    if mo:
        mo = load_module(title, *mo)
    return mo


class App(HtmlFiles):
    def arguments(self, ap):
        ap.add_argument("-m", help="plugin", dest="modules", action="append")
        ap.add_argument(
            "--pp", help="python path", dest="python_paths", action="append"
        )
        ap.add_argument(
            "--define", "-d", help="define some variable", dest="defs", action="append"
        )

        if not ap.description:
            ap.description = "Alter htmls using modules you provide"
        super().arguments(ap)

    def ready(self):
        ### python_paths
        if self.python_paths:
            from sys import path

            for p in self.python_paths:
                path.append(p)
        ### Load plugins
        modre = regex(r"^\w+[\w\d\.]+$")
        for p in self.modules:
            mo = None
            if p == "-":
                from . import _stdin

                mo = _stdin
            elif modre.fullmatch(p):
                mo = import_module(p)
            else:
                try:
                    mo = loadModule(self, p)
                finally:
                    logging.info(
                        "Module %r %r", mo and getattr(mo, "__name__", "") or "", p
                    )

            if mo:
                self._modules.append(mo)
                fn_init = getattr(self, "fn_init", None)
                if fn_init:
                    hasattr(mo, fn_init) and getattr(mo, fn_init)(self)

        # defs
        def defs(x):
            if x:
                for v in x:
                    k, s, v = v.partition("=")
                    if s:
                        yield (k, v)
                    else:
                        yield (k, True)

        self.defs = dict(defs(self.defs))

        # Call: fn_start (give chance to modify app)
        fn_start = getattr(self, "fn_start", None)
        if fn_start:
            for x in self._modules:
                hasattr(x, fn_start) and getattr(x, fn_start)(self)
        super().ready()

    def done(self):
        fn_end = getattr(self, "fn_end", None)
        if fn_end:
            for x in self._modules:
                hasattr(x, fn_end) and getattr(x, fn_end)(self)
        super().done()

    def on_tree(self, doc, *args):
        root = doc.getroot()
        seen = self.seen
        fmt = self.format
        if self.hot_links:
            links = root.iterlinks()

            def ff(v):
                (element, attribute, link, pos) = v

                if link.startswith("data:"):
                    return False
                elif not attribute:
                    if link.startswith("urn:not-loaded:"):
                        return False
                    return True
                elif attribute in ("src", "background"):
                    return True
                elif attribute in ("href",):
                    if element.tag == "link":
                        rel = element.get("rel") or ""
                        return rel.find("icon") >= 0
                elif attribute in ("archive", "codebase", "code"):
                    return element.tag == "applet"

            def enum():
                yield from filter(ff, links)

        else:

            def enum():
                for e in root.xpath(r".//*"):
                    tag = e.tag

                    for attr in lm.get(tag, ()):
                        link = e.attrib.get(attr)
                        if not link:
                            continue
                        yield e, attr, link, None

        for element, attribute, link, pos in enum():
            if not link:
                continue
            elif self.absolute_links:
                u = urlsplit(link)
                if u[2] and u[2].startswith("/"):
                    pass
                else:
                    continue

            tag = element.tag
            s = fmt.format_map(dict(link=link, attr=attribute or "-", tag=tag))
            if s in seen:
                continue
            seen[s] = True
            try:
                stdout.write(s)
                stdout.write("\n")
            except:
                stderr.write("Failed %r\n" % s)


from sys import stdout, stderr
from os import environ
from urllib.parse import urlsplit, urlunsplit

lm = {
    "xmp": [
        "href",
    ],
    "embed": [
        "pluginspage",
        "src",
    ],
    "tr": [
        "background",
    ],
    "object": [
        "classid",
        "codebase",
        "data",
        "archive",
        "usemap",
    ],
    "input": [
        "src",
        "usemap",
    ],
    "a": [
        "href",
    ],
    "area": [
        "href",
    ],
    "table": [
        "background",
    ],
    "form": [
        "action",
    ],
    "img": [
        "src",
        "lowsrc",
        "longdesc",
        "usemap",
    ],
    "frame": [
        "src",
        "longdesc",
    ],
    "isindex": [
        "action",
    ],
    "body": [
        "background",
    ],
    "bgsound": [
        "src",
    ],
    "th": [
        "background",
    ],
    "link": [
        "href",
    ],
    "base": [
        "href",
    ],
    "script": [
        "src",
        "for",
    ],
    "head": [
        "profile",
    ],
    "ilayer": [
        "background",
    ],
    "del": [
        "cite",
    ],
    "blockquote": [
        "cite",
    ],
    "iframe": [
        "src",
        "longdesc",
    ],
    "ins": [
        "cite",
    ],
    "layer": [
        "background",
        "src",
    ],
    "q": [
        "cite",
    ],
    "td": [
        "background",
    ],
    "applet": [
        "archive",
        "codebase",
        "code",
    ],
}
__name__ == "__main__" and App().main()

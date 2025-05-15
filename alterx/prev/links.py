from . import HtmlFiles


class App(HtmlFiles):
    def arguments(self, ap):
        self.seen = {}
        ap.add_argument(
            "--hot-links", help="Only hot links", dest="hot_links", action="store_true"
        )
        ap.add_argument(
            "--absolute-links", help="Non relative links", action="store_true"
        )
        ap.add_argument("--format", default="{tag}\t{attr}\t{link}", help="line format")
        if not ap.description:
            ap.description = "List links of html files"
        super().arguments(ap)

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

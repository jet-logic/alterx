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

try:
    from urlparse import urlparse
except:
    from urllib.parse import urlparse

seen = {}
from sys import stdout, stderr
from os import environ

which = (
    "hot" if environ.get("HOT_LINKS") else "cold" if environ.get("COLD_LINKS") else None
)


def on_etree(doc, app, file):
    root = doc.getroot()
    # print("on_etree", file)
    if "hot" == which:
        links = root.iterlinks()

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
                    return rel.find("icon") >= 0
            elif attribute in ("archive", "codebase", "code"):
                return element.tag == "applet"

        links = filter(ff, links)
        for element, attribute, link, pos in links:
            s = f'{element.tag} {attribute or "-"} {link}\n'
            if s in seen:
                continue
            seen[s] = True
            stdout.write(s)
        return

    for e in root.xpath(r".//*"):
        t = e.tag

        for v in lm.get(t, ()):
            h = e.attrib.get(v)
            if not h:
                continue
            h = f'{e.tag}\t{v or "-"}\t{h}'
            if h in seen:
                continue
            seen[h] = True
            try:
                stdout.write(h)
                stdout.write("\n")
            except:
                stderr.write("Failed %r\n" % h)

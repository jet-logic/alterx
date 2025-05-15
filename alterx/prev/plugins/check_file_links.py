from sys import stdout, stderr
from os import environ
from os.path import (
    isabs,
    isfile,
    isdir,
    abspath,
    normpath,
    join,
    dirname,
    exists,
    relpath,
)
from urllib.parse import urlsplit, urlunsplit
from urllib.request import url2pathname
from pathlib import Path


def resolve_source(uriSrc, dirParent, pathIdTup=None):
    # (scheme, netloc, path, params, query, fragment)
    url = urlsplit(uriSrc)
    path = url2pathname(url[2])
    if isabs(path):
        path = abspath(path)
    else:
        path = normpath(join(dirParent, path))
    if pathIdTup:
        return (path, url[5])
    return path


def abs2rel(path, base):
    try:
        return relpath(path, base)
    except ValueError:
        return path


def on_etree(doc, app, this):
    root = doc.getroot()
    pwd = dirname(this.path)

    links = root.iterlinks()

    def _set(elemnt, attr, rel, target, resolve, link):
        print(f"Set <{rel}> <-- <{target}> <-- <{resolve}> <-- <{link}>")
        old = element.attrib[attribute]
        element.attrib[attribute] = rel
        element.attrib[f"{attribute}-0"] = old

    for element, attribute, link, pos in links:
        u = urlsplit(link)
        p = u.path
        if (
            not attribute
            or link.startswith("//")
            or (not p)
            or (u.scheme and u.scheme != "file")
        ):
            continue
        f = url2pathname(link)
        path_resolved = resolve_source(link, pwd)

        target = None
        if isdir(path_resolved):
            i = join(path_resolved, "index.html")
            if isfile(i):
                target = i
                r = abs2rel(target, pwd)
                w = list(u)
                w[2] = r
                r = urlunsplit(w)
                _set(element, attribute, r, target, path_resolved, link)
        if exists(path_resolved):
            continue
        if (
            path_resolved.startswith("/")
            and len(path_resolved) > 1
            and path_resolved[1] != "/"
        ):
            for x in Path(pwd).parents:
                b = x / path_resolved[1:]
                if b.is_dir():
                    b = b / "index.html"
                if b.is_file():
                    target = str(b)
                    r = abs2rel(target, pwd)
                    w = list(u)
                    w[2] = r
                    r = urlunsplit(w)
                    _set(element, attribute, r, target, path_resolved, link)
                    break

        if not target:
            print(f"No <{link}> <-- <{path_resolved}>")


ROOTD = environ.get("ROOTD")
# /mnt/META/wrx/pp/alterx/plugins/check_file_links.py

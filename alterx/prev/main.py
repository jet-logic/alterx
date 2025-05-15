import logging
from re import compile as regex
from . import Counter, dosGlob2RE, FSInfo, walk_dir_pre, loadModule
from importlib import import_module


def files(args, nameRE):
    from os.path import isfile, isdir

    for f in args:
        if f == "-":
            from sys import stdin

            line = stdin.readline().strip()
            while line:
                yield line
                line = stdin.readline().strip()
            continue
        if isfile(f):
            yield f
        elif isdir(f):
            f = FSInfo(f)
            f.depth = 0
            f.rel = ""
            for f in walk_dir_pre(f):
                if f.isdir:
                    f.walk = True
                    continue
                x = f.name
                for r in nameRE:
                    if r.search(x):
                        yield f.path
        else:
            # TODO: URLs
            raise RuntimeError("File not found `%s'" % f)


def main(app):
    re_names = []
    app.useEncoding = None
    app.savePretty = None
    app.dryRun = None
    app.deBug = None
    app.modifyIf = 0
    app.fileOut = []
    app.plugIns = []
    app.checksModification = None
    app.total = Counter()
    app.plugInsArgs = []

    from argparse import ArgumentParser

    parser = ArgumentParser()

    parser.add_argument("args", nargs="+")
    parser.add_argument("-p", help="plugin", dest="plugInsArgs", action="append")
    parser.add_argument("--pp", help="python path", dest="pyPaths", action="append")
    parser.add_argument("--dry", help="dry run", dest="dryRun", action="store_true")
    parser.add_argument(
        "--act", "-a", help="not dry run", dest="dryRun", action="store_false"
    )
    parser.add_argument("--debug", help="debug", dest="deBug", action="store_true")
    parser.add_argument(
        "--pretty", help="save pretty formated", dest="savePretty", action="store_true"
    )
    parser.add_argument("--log", help="log level", dest="logLevel", action="store")
    parser.add_argument(
        "--define", "-d", help="define some variable", dest="defs", action="append"
    )
    parser.add_argument(
        "-name", "-g", help="plugin", dest="name_globs", metavar="GLOB", action="append"
    )
    parser.add_argument(
        "-rname",
        "-e",
        help="plugin",
        dest="name_patterns",
        metavar="REGEX",
        action="append",
    )
    parser.add_argument("-o", help="output to", dest="fileOut", action="append")
    parser.add_argument("-m", help="modify", dest="modifyIf", action="count")
    parser.add_argument(
        "--threads",
        help="use threads",
        metavar="COUNT",
        dest="use_threads",
        action="store",
    )

    # parser.add_argument("--lxml", help="use lxml", dest="useLXML", action="store_true")

    ### Parse argument
    app.supply_argparse(parser)

    parser.parse_args(namespace=app)

    ### Logging
    from logging import INFO, basicConfig

    basicConfig(**{"level": INFO, "format": "%(levelname)s: %(message)s"})
    if app.logLevel:
        n = getattr(logging, app.logLevel.upper(), None)
        if not isinstance(n, int):
            raise ValueError("Invalid log level: %s" % (v,))
        logging.getLogger().setLevel(n)
    ### pyPaths
    if app.pyPaths:
        from sys import path

        for p in app.pyPaths:
            path.append(p)

    ### Load plugins
    modre = regex(r"^\w+[\w\d\.]+$")
    for p in app.plugInsArgs:
        mo = None
        if p == "-":
            from . import _stdin

            mo = _stdin
        elif modre.fullmatch(p):
            mo = import_module(p)
        else:
            try:
                mo = loadModule(app, p)
            finally:
                logging.info(
                    "Module %r %r", mo and getattr(mo, "__name__", "") or "", p
                )

        if mo:
            app.plugIns.append(mo)
            fn_init = getattr(app, "fn_init", None)
            if fn_init:
                hasattr(mo, fn_init) and getattr(mo, fn_init)(app)

    # defs
    def defs(x):
        if x:
            for v in x:
                k, s, v = v.partition("=")
                if s:
                    yield (k, v)
                else:
                    yield (k, True)

    app.defs = dict(defs(app.defs))
    # # print("P", app.defs)
    # Call: fn_start (give chance to modify app)
    fn_start = getattr(app, "fn_start", None)
    if fn_start:
        for x in app.plugIns:
            hasattr(x, fn_start) and getattr(x, fn_start)(app)
    # Globing
    if app.name_globs:
        for v in app.name_globs:
            re_names.append(dosGlob2RE(v))
    if app.name_patterns:
        for v in app.name_patterns:
            re_names.append(regex(v))
    if len(re_names) < 1:
        re_names.append(regex(app.name_re))

    ### Walk
    from .process import on_file

    assert len(re_names) > 0

    if app.use_threads:
        from concurrent.futures import ThreadPoolExecutor, as_completed

        with ThreadPoolExecutor(
            max_workers=5 if app.use_threads == "-" else int(app.use_threads)
        ) as executor:
            for future in as_completed(
                (executor.submit(on_file, v, app) for v in files(app.args, re_names)),
                timeout=None,
            ):
                future.result()
    else:
        for v in files(app.args, re_names):
            on_file(v, app)

    # Call: fn_end
    fn_end = getattr(app, "fn_end", None)
    if fn_end:
        for x in app.plugIns:
            hasattr(x, fn_end) and getattr(x, fn_end)(app)
    # Total
    # print(dir(app))
    v = app.total
    if v and len(v.__dict__) > 0:
        logging.warning(
            "%s: %s", __name__, "; ".join((f"{k} {v}" for (k, v) in v.__dict__.items()))
        )

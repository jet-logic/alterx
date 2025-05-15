import logging
from . import (
    Store,
    loadModule,
    HashSink,
    SinkRaw,
    getDecl,
    FSInfo,
    walk_dir_pre,
    dosGlob2RE,
    Counter,
)


from os.path import abspath


def onFile(f, ctx):
    total = ctx.total
    this = Store(ctx)
    # print(f, "sDG")
    encoding = None
    this.filePath = f = abspath(f)
    total.Files += 1
    # Load document
    try:
        dom = ctx.domParse(f)
    except:
        total.Errors += 1
        return logging.exception("Failed to load %r", f)
    else:
        logging.info("XML: %s %s", (dom and ("[#%d]" % total.Files) or "ERROR"), f)
    # Feed to plugins
    if ctx.checksModification:
        if ctx.modifyIf == 2:
            mHash = ctx.domHash(dom)
        else:
            mHash = None
            ctx.domHash(dom)
    else:
        mHash = (ctx.modifyIf == 2) and ctx.domHash(dom)
    mUrge = None
    # TODO: optimize
    for _ in (_ for _ in (ctx.domCallStart, ctx.domCall, ctx.domCallEnd) if _):
        for x in ctx.plugIns:
            r = getattr(x, _, None)

            if r and r(dom, this):
                mUrge = True
                # call back says he modified it
    # Was modified?
    if mHash:  # (ctx.modifyIf == 2) Modify if hash changed
        mSave = not (ctx.domHash(dom) == mHash)
    else:
        mSave = mUrge or (ctx.modifyIf > 2)
    if not mSave:
        return None
    # Modified, Save it
    encoding = ctx.useEncoding or ctx.domEncoding(dom, f) or "ASCII"
    if not ctx.dryRun:
        out = None
        if len(ctx.fileOut) < 1:  # []
            out = ctx.domSinkFile(this.filePath, encoding)
        elif (len(ctx.fileOut) == 1) and (ctx.fileOut[0] == "-"):  # ['-']
            out = ctx.domSinkOut(encoding)
        else:  # ['file1', ...]
            out = ctx.domSinkFile(ctx.fileOut.pop(0), encoding)
        ctx.domWrite(dom, out, encoding, ctx)
        out.close()
    total.Altered += 1
    logging.warning(
        f'XML: Altered {ctx.dryRun is False and "!" or "?"} {encoding and (" [" + encoding + "]") or ""}',
    )


from re import compile as regex


def main(app):
    app.stripWS = None
    app.stripPIs = None
    app.stripCDatas = None
    app.stripComments = None
    app.useLXML = None
    app.useEncoding = None
    app.useNL = ""
    app.useIndent = ""
    app.useTab = ""
    app.savePretty = None
    app.dryRun = None
    app.deBug = None
    app.modifyIf = 0
    app.fileOut = []
    app.plugIns = []
    app.nameRE = []
    app.modeHTML = None
    app.checksModification = None
    app.total = Counter()

    import argparse

    parser = argparse.ArgumentParser(description="Alter XML")
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
    parser.add_argument(
        "--stripws", help="strip spaces", dest="stripWS", action="store_true"
    )
    parser.add_argument(
        "--define", "-d", help="define some variable", dest="defs", action="append"
    )
    parser.add_argument(
        "--html", help="html mode", dest="modeHTML", action="store_true"
    )
    parser.add_argument("--lxml", help="use lxml", dest="useLXML", action="store_true")
    parser.add_argument("--name", "-g", help="plugin", dest="globDOS", action="append")
    parser.add_argument("--rname", "-e", help="plugin", dest="globRE", action="append")
    parser.add_argument("--log", help="log level", dest="logLevel", action="store")
    parser.add_argument("-o", help="output to", dest="fileOut", action="append")
    parser.add_argument("-m", help="modify", dest="modifyIf", action="count")

    ### Parse argument

    app = parser.parse_args(namespace=app)

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
        if modre.fullmatch(p):
            mo = __import__(p)
        else:
            try:
                mo = loadModule(app, p)
            finally:
                logging.info(
                    "XML: Module %r %r", mo and getattr(mo, "__name__", "") or "", p
                )

        if mo:
            app.plugIns.append(mo)
            if app.useLXML is None and getattr(mo, "on_xml_etree", None):
                app.useLXML = True
            hasattr(mo, "on_xml_init") and mo.on_xml_init(app)
    app.plugInsArgs = None

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
    # Call: on_xml_start (give chance to modify app)
    for x in app.plugIns:
        hasattr(x, "on_xml_start") and x.on_xml_start(app)
    # Globing
    if app.globDOS:
        for v in app.globDOS:
            app.nameRE.append(dosGlob2RE(v))
    if app.globRE:
        for v in app.globRE:
            app.nameRE.append(regex(v))
    if len(app.nameRE) < 1:
        app.nameRE.append(
            regex(app.modeHTML and r"^.+\.(x?html?)$" or r"^.+\.(?:xs(?:d|l)|xml)$")
        )

    # Parser
    if app.savePretty:
        app.useIndent = ""
        app.useTab = "\t"
        app.useNL = "\n"
    if app.useLXML:
        import sys, codecs

        try:
            from lxml import etree

            is_lxml = True
        except ImportError:
            try:  # Python 2.5
                import xml.etree.cElementTree as etree
            except ImportError:
                try:  # Python 2.5
                    import xml.etree.ElementTree as etree
                except ImportError:
                    try:  # Normal cElementTree install
                        import cElementTree as etree
                    except ImportError:
                        try:  # Normal ElementTree install
                            import elementtree.ElementTree as etree
                        except ImportError:
                            logging.exception(
                                "Failed to import ElementTree from any known place"
                            )
            is_lxml = False

        def lxmlParse(f):
            kwargs = {}
            if is_lxml:
                kwargs["remove_blank_text"] = app.stripWS
                kwargs["remove_comments"] = app.stripComments
                kwargs["remove_pis"] = app.stripPIs
                kwargs["strip_cdata"] = app.stripCDatas
            if app.modeHTML:
                from lxml import html

                with open(f, "rb") as si:
                    return html.parse(si)
            else:
                parser = etree.XMLParser(**kwargs)
            return etree.parse(open(f, "rb"), parser)

        def domHash(doc):
            h = HashSink()
            doc.write(h)
            return h.h.hexdigest()

        def domWrite(doc, out, enc, ctx):
            doc.write(
                out, xml_declaration=True, encoding=enc, pretty_print=ctx.savePretty
            )

        app.domEncoding = lambda doc, f: getDecl(f).get("encoding")
        app.domWrite = domWrite
        app.domParse = lxmlParse
        app.domHash = domHash
        app.domSinkFile = lambda f, enc: open(f, "wb")
        app.domSinkOut = lambda enc: SinkRaw(sys.stdout.buffer, enc)
        app.domCall = "on_xml_etree"
        app.domCallStart = "on_xml_etree_start"
        app.domCallEnd = "on_xml_etree_end"
        app.etree = etree
    else:
        import sys, codecs

        app.domEncoding = lambda doc, f: getDecl(f).get("encoding")
        app.domHash = lambda doc: hashXMLNode(doc)
        app.domParse = lambda f: domLoadDoc(f, app)
        app.domSinkFile = lambda f, enc: codecs.open(f, "wb", enc, "xmlcharrefreplace")
        app.domSinkOut = lambda enc: Sink(sys.stdout, enc)
        app.domCall = "on_xml_doc"
        app.domCallStart = "on_xml_doc_start"
        app.domCallEnd = "on_xml_doc_end"
        f = app.domWriter = DOMXMLWriter()
        if app.savePretty:
            f.tab = "  "
            f.newl = "\n"
        else:
            f.tab = None
            f.newl = None
        # ~ app.domWrite = lambda doc, out, enc, ctx: doc.writexml(out, indent=ctx.useIndent, addindent=ctx.useTab, newl=ctx.useNL, encoding=enc)
        app.domWrite = domWriteDoc
    ###
    if app.checksModification:

        def wasModified():
            hash = app.domHash(app.domDoc)
            return hash and app.hashOfDOM and app.hashOfDOM != hash

        app.wasModified = wasModified

    ### Walk
    from os.path import isfile, isdir
    import sys
    from concurrent.futures import ThreadPoolExecutor, as_completed

    def files():
        for f in app.args:
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
                    for r in app.nameRE:
                        if r.match(x):
                            yield f.path
            else:
                # TODO: URLs
                raise RuntimeError("File not found `%s'" % f)

    with ThreadPoolExecutor(max_workers=5) as executor:
        for future in as_completed(
            (executor.submit(onFile, v, app) for v in files()), timeout=None
        ):
            future.result()
    # Call: on_xml_end
    for x in app.plugIns:
        hasattr(x, "on_xml_end") and x.on_xml_end(app)

    v = app.total
    if v and len(v.__dict__) > 0:
        logging.warning(
            "%s: %s", __name__, "; ".join((f"{k} {v}" for (k, v) in v.__dict__.items()))
        )


__name__ == "__main__" and main(Store())

class Store(object):
    def __init__(self, parent=None):
        self._parent = parent

    def __contains__(self, name):
        return name in self.__dict__

    def __setitem__(self, key, value):
        self.__dict__[key] = value

    def __getitem__(self, name):
        return getattr(self, name)

    def __getattr__(self, name):
        if name != "_parent":
            p = self._parent
            if p:
                return getattr(p, name)
        raise AttributeError("%r on %r " % (name, self))


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


def getDecl(f):
    decl = {}

    def onDecl(version, encoding, standalone):
        decl["version"] = version
        decl["encoding"] = encoding
        decl["standalone"] = standalone

    from xml.parsers.expat import ParserCreate

    p = ParserCreate()
    p.XmlDeclHandler = onDecl
    if hasattr(f, "read"):
        p.ParseFile(f)
    else:
        f = open(f, "rb")
        try:
            p.ParseFile(f)
        finally:
            f.close()
    return decl


class Sink:
    def __init__(self, out, enc):
        self.out = out
        self.enc = enc

    def write(self, x):
        self.out.write(x.encode(self.enc, "xmlcharrefreplace"))

    def close(self):
        pass


class SinkRaw:
    def __init__(self, out, enc):
        self.out = out
        self.enc = enc

    def write(self, x):
        self.out.write(x)

    def close(
        self,
    ):
        pass


class HashSink(object):
    __slots__ = ("h",)

    def __init__(self, h=None):
        if not h:
            from hashlib import md5

            h = md5()
        self.h = h

    def write(self, x):
        self.h.update(x)


def listdr(f0):
    try:
        return listdir(f0.path)
    except:
        logging.exception("Failed to list %r", f0.path)
    return ()


class FSInfo:
    def __init__(self, p):
        self.path = p

    def __getattr__(self, name):
        if name == "stat":
            from os import stat

            self.__dict__[name] = stat(self.path)
        elif name in ("parent", "name"):
            from os.path import split

            (self.__dict__["parent"], self.__dict__["name"]) = split(self.path)
        elif "isdir" == name:
            from stat import S_ISDIR

            self.__dict__[name] = bool(S_ISDIR(self.stat.st_mode))
        elif hasattr(self.stat, name):
            self.__dict__[name] = getattr(self.stat, name)
        return self.__dict__[name]


def walk_dir_pre(f0):
    d2 = f0.depth + 1
    for name in listdr(f0):
        f1 = f0.__class__(join(f0.path, name))
        f1.depth = d2
        f1.rel = join(f0.rel, name)
        f1.walk = None
        yield f1
        if f1.walk:
            for x in walk_dir_pre(f1):
                yield x


def dosGlob2RE(s):
    import re

    s = re.escape(s)
    s = s.replace(r"\*", ".*")
    s = s.replace(r"\?", ".")
    return re.compile(s, re.I)


class Counter:
    def __getattr__(self, name):
        return self.__dict__.setdefault(name, 0)

    def __contains__(self, name):
        return name in self.__dict__

    def __iter__(self):
        return iter(self.__dict__)

    def __getitem__(self, name):
        return self.__dict__.setdefault(name, 0)

    def __setitem__(self, key, value):
        self.__dict__[key] = value

    def __str__(self):
        return " ".join(sorted("%s %d;" % (k, v) for (k, v) in self.__dict__.items()))


import logging
from os import listdir
from os.path import join, abspath
from biojet1.scandir import ScanTree


class Model(ScanTree):
    def encoding_of(self, doc, src):
        return "utf-8"

    def sink_file(self, src, encoding=None):
        return open(src, "wb", encoding=None)

    def sink_out(self, encoding):
        from sys import stdout

        return stdout.buffer

    def supply_argparse(self, parser):
        # raise NotImplementedError(f"{self.__class__.__name__}")
        pass


class Data(Model):
    fn_call = "on_data"
    fn_init = "on_data_init"
    fn_start = "on_data_start"
    fn_end = "on_data_end"


class Xml(Model):
    name_re = r"\.(xml|xsl|svg)$"


class Html(Model):
    name_re = r".*\.(html?)$"


class Status:
    def __init__(self, app, path=None):
        self.app = app
        self.hash = self.data = None
        self.path = path

    def modified(self, parent=None):
        h1 = self.hash
        if h1 is True:
            return True
        elif h1:
            h2 = app.hash_of(self.data)
            return h2 and h1 != h2 and h2


class XmlFiles(Model):
    default_name_re = [r"\.(xml|xsl|svg)$"]

    def _get_etree(self):
        try:
            from lxml import etree

            self.is_lxml = True

            return etree
        except ImportError:
            try:  # Normal ElementTree install
                import xml.etree.ElementTree as etree

                self.is_lxml = False
                return etree
            except ImportError:
                logging.exception("Failed to import ElementTree from any known place")

    def parse_file(self, src):
        etree = self.etree
        kwargs = {}
        if self.is_lxml:
            kwargs["remove_blank_text"] = self.stripWS
            kwargs["remove_comments"] = self.stripComments
            kwargs["remove_pis"] = self.stripPIs
            kwargs["strip_cdata"] = self.stripCDatas
        parser = etree.XMLParser(**kwargs)
        return etree.parse(open(src, "rb"), parser)

    def hash_of(self, doc):
        h = HashSink()
        doc.write(h)
        return h.h.hexdigest()

    def dump(self, doc, out, encoding):
        doc.write(
            out, xml_declaration=True, encoding=encoding, pretty_print=self.save_pretty
        )
        # encoding="us-ascii", xml_declaration=None, default_namespace=None, method="xml"

    def sink_out(self, encoding):
        from sys import stdout

        return SinkRaw(stdout.buffer, encoding)

    def check_accept(self, x):
        return x.is_file() and super().check_accept(x)

    def arguments(self, ap):  # supply_argparse
        self.name_re = []
        self.dry_run = True
        self.use_encoding = None
        self.modify_if = 0
        self.file_out = []
        self.checks_modification = None
        self.total = Counter()

        ap.add_argument(
            "--strip_ws", help="strip spaces", dest="stripWS", action="store_true"
        )
        ap.add_argument(
            "--strip_comment",
            help="strip comments",
            dest="stripComments",
            action="store_true",
        )
        ap.add_argument(
            "--strip_pi", help="strip pis", dest="stripPIs", action="store_true"
        )
        ap.add_argument(
            "--strip_cdata",
            help="strip cdatas",
            dest="stripCDatas",
            action="store_true",
        )
        ap.add_argument(
            "--pretty",
            help="save pretty formated",
            dest="save_pretty",
            action="store_true",
        )
        ap.add_argument("-m", help="modify", dest="modify_if", action="count")
        ap.add_argument("--log", help="log level", dest="log_level", action="store")
        ap.add_argument("-o", help="output to", dest="file_out", action="append")

        if not ap.description:
            ap.description = "Alters XML files"
        super().arguments(ap)

    def ready(self):
        if not self.name_re:
            from re import compile as regex

            for x in self.default_name_re:
                self.name_re.append(regex(x))
        ### Logging
        from logging import INFO, basicConfig

        basicConfig(**{"level": INFO, "format": "%(levelname)s: %(message)s"})
        if self.log_level:
            n = getattr(logging, self.log_level.upper(), None)
            if not isinstance(n, int):
                raise ValueError("Invalid log level: %s" % (v,))
            logging.getLogger().setLevel(n)

    def done(self):
        v = self.total
        if v and len(v.__dict__) > 0:
            logging.info(
                "%s",
                "; ".join((f"{k} {v}" for (k, v) in v.__dict__.items())),
            )

    def dir_entry(self, de):
        total = self.total
        this = Status(self)
        this.path = path = abspath(de.path)
        total.Files += 1

        # Load document
        doc = None
        try:
            this.data = doc = self.parse_file(path)
        except:
            total.Errors += 1
            return logging.exception("Failed to load %r", path)
        else:
            logging.info("%s %s", (self and ("#%d" % total.Files) or "ERROR"), path)
        # Feed to plugins
        if self.checks_modification:
            if self.modify_if == 2:
                this.hash = mHash = self.hash_of(doc)
            else:
                mHash = None
                this.hash = self.hash_of(doc)
        else:
            this.hash = mHash = (self.modify_if == 2) and self.hash_of(doc)
        mUrge = None

        if self.on_tree(doc, this):
            mUrge = True  # call back says he modified it
            this.hash = True

        # Was modified?
        if mHash:  # (self.modify_if == 2) Modify if hash changed
            mSave = not (self.hash_of(doc) == mHash)
        else:
            mSave = mUrge or (self.modify_if > 2)
        if not mSave:
            return None
        # Modified, Save it
        encoding = self.use_encoding or self.encoding_of(doc, path)
        if self.dry_run is False:
            out = None
            if len(self.file_out) < 1:  # []
                out = self.sink_file(this.path, encoding)
            elif (len(self.file_out) == 1) and (self.file_out[0] == "-"):  # ['-']
                out = self.sink_out(encoding)
            else:  # ['file1', ...]
                out = self.sink_file(self.file_out.pop(0), encoding)
            self.dump(doc, out, encoding)
            out.close()
        total.Altered += 1
        logging.warning(
            f'Altered {self.dry_run is False and "!" or "?"} {encoding and (" [" + encoding + "]") or ""}',
        )


class HtmlFiles(XmlFiles):
    default_name_re = [r".*\.(html?)$"]

    def parse_file(self, src):
        etree = self.etree
        kwargs = {}
        if self.is_lxml:
            kwargs["remove_blank_text"] = self.stripWS
            kwargs["remove_comments"] = self.stripComments
            kwargs["remove_pis"] = self.stripPIs
            kwargs["strip_cdata"] = self.stripCDatas
            from lxml import html

            with open(src, "rb") as si:
                return html.parse(si)
        else:
            kwargs["html"] = True
            with open(f, "rb") as h:
                return etree.parse(h, etree.XMLParser(**kwargs))

    def dump(self, doc, out, encoding):
        kwargs = {}
        kwargs["method"] = "html"
        kwargs["xml_declaration"] = False
        kwargs["pretty_print"] = self.save_pretty
        doc.write(out, encoding=encoding, **kwargs)
        # write(file, encoding="us-ascii", xml_declaration=None, default_namespace=None, method="xml")

    def arguments(self, ap):
        if not ap.description:
            ap.description = "Alters HTML files"
        super().arguments(ap)

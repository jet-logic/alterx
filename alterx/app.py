from importlib import import_module
from logging import info, warning, exception
from os.path import abspath
from .main import flag
from .findskel import FindSkel
from .utils import SinkRaw


class App(FindSkel):
    modify_if: int = flag("m", "Modify flag", action="count", default=0)
    variables: "list[str]" = flag("d", "Define some variable", metavar="NAME=VALUE", default=[])
    extensions: list = flag("x", "Extension script", metavar="SCRIPT")
    output: str = flag("o", "Output to FILE", metavar="FILE")
    use_encoding: str = flag("encoding", "Encoding to use when saving")
    dry_run: bool = flag("n", "No modifiaction will happend")
    fn_process = "process"
    fn_init = "init"
    fn_start = "start"
    fn_end = "end"
    tag = "APP"
    default_glob_includes = []

    def __init__(self) -> None:
        self._glob_includes = []
        self._glob_excludes = []
        self._dir_depth = ()
        self._file_sizes = []
        self._paths_from = []

        self.defs: dict[str, str] = {}
        self.dry_run: bool | None = None
        self.modex = []
        # self.checks_modification = False
        self.total = Counter()
        super().__init__()
        from logging import basicConfig, addLevelName, WARNING
        from os import environ

        format = environ.get("LOG_FORMAT", "%(levelname)s: %(message)s")
        level = environ.get("LOG_LEVEL", "INFO")
        basicConfig(format=format, level=level)
        addLevelName(WARNING, "WARN")

        def check(e, **kwargs):
            return e.is_file()

        self.on_check_accept(check)

    def ready(self) -> None:
        if not self._glob_includes:
            from re import compile

            for x in self.default_glob_includes:
                self._glob_includes.append(x)
        return super().ready()

    def start(self):
        if self.variables:
            for e in self.variables:
                k, s, v = e.partition("=")
                if s:
                    self.defs[k] = v
                else:
                    self.defs[k] = True

        from re import compile as regex

        modre = regex(r"^\w+[\w\d\.]+$")
        for x in self.extensions:
            mo = None
            if x == "-":
                mo = load_stdin_as_module()
            elif modre.fullmatch(x):
                mo = import_module(x)
            else:
                try:
                    mo = load_extension(x)
                finally:
                    info("Module %r %r", mo and getattr(mo, "__name__", "") or "", x)
            if mo:
                self.modex.append(mo)
                fn_init = self.fn_init
                if fn_init:
                    hasattr(mo, fn_init) and getattr(mo, fn_init)(self)

        fn_start = self.fn_start
        if fn_start:
            for x in self.modex:
                hasattr(x, fn_start) and getattr(x, fn_start)(self)

        self._walk_paths()

        fn_end = self.fn_end
        if fn_end:
            for x in self.modex:
                hasattr(x, fn_end) and getattr(x, fn_end)(self)
        self.total and info("Total {}".format(self.total))

    def sink_file(self, src, encoding=None):
        return open(src, "wb", encoding=None)

    def encoding_of(self, doc: object, src: str) -> str:
        return ""

    def process_entry(self, de):
        assert de.is_file()
        self.process_file(de.path)

    def process_file(self, file: str):
        # print("process_file", file)
        this = Status(self)
        this.path = path = abspath(file)
        self.total.Files += 1

        # Load document
        try:
            this.doc = self.parse_file(file)
        except:
            self.total.Errors += 1
            exception("Failed to load %r", file)
            exit(1)
        else:
            info(f"{self.tag} %s %s", "[#%d]" % self.total.Files, file)
        # Feed to plugins
        if self.modify_if > 0:
            if self.modify_if == 2:
                this.hash = mHash = self.hash_of(this.doc)
            else:
                assert self.modify_if == 1
                mHash = None
                this.hash = self.hash_of(this.doc)
        else:
            assert self.modify_if == 0
            # this.hash = mHash = (self.modify_if == 2) and self.hash_of(this.doc)
            this.hash = mHash = False

        mUrge = None

        fn = self.fn_process
        if fn:
            for x in self.modex:
                r = getattr(x, fn, None)
                if r and r(this.doc, this, self):
                    mUrge = True
                    this.hash = True

        # Was modified?
        if mHash:  # (self.modify_if == 2) Modify if hash changed
            mSave = not (self.hash_of(this.doc) == mHash)
        else:
            mSave = mUrge or (self.modify_if > 2)
        if not mSave:
            return None
        # Modified, Save it
        encoding = self.use_encoding or self.encoding_of(this.doc, path)
        if self.output == "-":
            with self.sink_out(encoding) as out:
                self.dump(this.doc, out, encoding)
        elif self.dry_run:
            pass
        else:
            out = self.sink_file(self.output, encoding) if self.output else self.sink_file(this.path, encoding)
            with out:
                self.dump(this.doc, out, encoding)
        self.total.Altered += 1
        warning(
            f'Altered{(self.modify_if >0) and "!" or "?"} {encoding and ("[" + encoding + "]") or ""}',
        )

    def dump(self, doc: object, out: object, encoding: str):
        raise NotImplementedError()

    def parse_source(self, src: object) -> object:
        raise NotImplementedError()

    def parse_file(self, src: str):
        with open(src, "rb") as h:
            return self.parse_source(h)

    def parse_bytes(self, src: bytes):
        from io import BytesIO

        return self.parse_source(BytesIO(src))

    def sink_out(self, encoding):
        from sys import stdout

        return SinkRaw(stdout.buffer, encoding)

    def hash_of(self, doc: object) -> str:
        raise NotImplementedError()


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


class Status:
    def __init__(self, app: App):
        self.app = app
        self.hash: str | bool | None = None
        self.doc = None
        self.path = ""

    def modified(self, parent=None):
        h1 = self.hash
        if h1 is True:
            return True
        elif h1:
            h2 = self.app.hash_of(self.doc)
            return h2 and h1 != h2 and h2

    def replace(self, data: object):
        if isinstance(data, bytes):
            self.doc = self.app.parse_source(data)
        elif isinstance(data, str):
            self.doc = self.app.parse_file(data)
        return self.doc


import importlib.util
import sys
from pathlib import Path
import hashlib


def generate_module_name(extension_path):
    """
    Generate a unique module name based on the file path.
    Uses a hash of the absolute path to ensure uniqueness.
    """
    abs_path = str(Path(extension_path).absolute())
    # Create a hash of the absolute path
    path_hash = hashlib.md5(abs_path.encode()).hexdigest()[:8]
    return f"ext_{path_hash}"


def load_extension(extension_path: str):
    """
    Load a Python script as an extension module with a unique name.

    Args:
        extension_path (str): Path to the Python script to load

    Returns:
        module: The loaded module
    """
    abs_path = Path(extension_path).absolute()

    if not abs_path.exists():
        raise FileNotFoundError(f"Extension file not found: {abs_path}")

    module_name = generate_module_name(abs_path)

    # Check if already loaded
    if module_name in sys.modules:
        return sys.modules[module_name]

    spec = importlib.util.spec_from_file_location(module_name, abs_path)
    if spec is None:
        raise ImportError(f"Could not load extension from {abs_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module

    try:
        spec.loader.exec_module(module)
    except Exception as e:
        del sys.modules[module_name]
        raise ImportError(f"Error loading extension {abs_path}: {str(e)}")

    return module


def load_stdin_as_module():
    """
    Load Python code from stdin as a module with a unique name.

    Returns:
        module: The loaded module
    """
    # Read all input from stdin
    code = sys.stdin.read()

    if not code.strip():
        raise ValueError("No code provided on stdin")

    # Generate a unique module name
    hash_obj = hashlib.md5(code.encode()).hexdigest()[:8]
    module_name = f"stdin_module_{hash_obj}"

    # Create a new module
    spec = importlib.util.spec_from_loader(module_name, loader=None, origin="<stdin>")  # We'll exec the code directly
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module

    try:
        # Execute the code in the module's namespace
        exec(code, module.__dict__)
    except Exception as e:
        del sys.modules[module_name]
        raise ImportError(f"Error executing stdin code: {str(e)}")

    return module

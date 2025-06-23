from os import DirEntry
from .main import Main
from .walkdir import WalkDir

__version__ = "0.0.4"


class FindSkel(WalkDir, Main):
    _glob_excludes: "list[str] | None" = None
    _glob_includes: "list[str] | None" = None
    _file_sizes: "list[object] | None" = None
    _dir_depth: "tuple[int, int] | None" = None
    _paths_from: "list[str] | None" = None
    _paths: "list[str] | None" = None

    def add_arguments(self, argp):
        group = argp.add_argument_group("Traversal")
        # --depth-first
        group.add_argument(
            "--depth-first",
            action="store_true",
            dest="depth_first",
            help="Process each directory's contents before the directory itself",
        )
        # --follow-symlinks
        group.add_argument(
            "--follow-symlinks",
            dest="follow_symlinks",
            const=1,
            help="Follow symbolic links",
            action="store_const",
            default=0,
        )
        # --act/--dry-run
        try:
            b = self.dry_run
        except AttributeError:
            pass
        else:
            if b is True:
                argp.add_argument("--act", action="store_false", dest="dry_run", help="not a test run")
            elif b is False:
                argp.add_argument(
                    "--dry-run",
                    action="store_true",
                    dest="dry_run",
                    help="test run only",
                )
        # --exclude, --include
        _glob_includes: list[str] = getattr(self, "_glob_includes", None)
        _glob_excludes: list[str] = getattr(self, "_glob_excludes", None)

        if _glob_excludes is not None or _glob_includes is not None:
            group.add_argument(
                "--exclude",
                metavar="GLOB",
                action="append",
                dest="_glob_excludes",
                help="exclude matching GLOB",
            )
            group.add_argument(
                "--include",
                metavar="GLOB",
                action="append",
                dest="_glob_includes",
                help="include matching GLOB",
            )
        # --sizes
        if self._file_sizes is not None:
            group.add_argument(
                "--sizes",
                action="append",
                dest="_file_sizes",
                type=lambda x: sizerangep(x),
                help="Filter sizes: 1k.., 4g, ..2mb",
                metavar="min..max",
            )
        # --depth
        if self._dir_depth is not None:
            group.add_argument(
                "--depth",
                dest="_dir_depth",
                type=lambda x: intrangep(x),
                help="Check for depth: 2.., 4, ..3",
                metavar="min..max",
            )
        # --paths-from
        if self._paths_from is not None:
            group.add_argument(
                "--paths-from",
                metavar="FILE",
                action="append",
                dest="_paths_from",
                default=[],
                help="read list of source-file names from FILE",
            )
        # PATH ...
        argp.add_argument(metavar="PATH", dest="_paths", nargs="*")
        return super().add_arguments(argp)

    def ready(self) -> None:
        #
        _glob_includes: list[str] = getattr(self, "_glob_includes", ())
        _glob_excludes: list[str] = getattr(self, "_glob_excludes", ())
        if _glob_includes or _glob_excludes:
            from os.path import relpath, sep, altsep
            from re import compile as regex, escape

            def makef(s: str):
                (rex, dir_only, neg, g) = globre3(s, escape=escape, no_neg=True)
                m = regex(rex)

                def col(r="", is_dir=False):
                    return (is_dir if dir_only else True) and m.search(r)

                return col

            inc = _glob_includes and [makef(s) for s in _glob_includes]
            exc = _glob_excludes and [makef(s) for s in _glob_excludes]
            alt = set(x for x in (sep, altsep) if x and x != "/")

            def check_glob(e: DirEntry, **kwargs):
                is_dir = e.is_dir()
                rel = relpath(e.path, self._root_dir)
                # print("check_glob", e, r, s)
                if alt:
                    for x in alt:
                        rel = rel.replace(x, "/")
                if inc:
                    if not any(m(rel, is_dir) for m in inc):
                        return False
                if exc:
                    if any(m(rel, is_dir) for m in exc):
                        return False

            self.on_check_accept(check_glob)
        #
        sizes: list[tuple[int, int]] = self._file_sizes
        if sizes:

            def check_size(de: DirEntry, **kwargs):
                ok = 0
                if de.is_dir():
                    pass
                else:
                    n = de.stat().st_size
                    for a, b in sizes:
                        if n >= a and n <= b:
                            ok += 1
                return ok > 0

            self.on_check_accept(check_size)
        #
        depth: tuple[int, int] = self._dir_depth
        if depth:
            a, b = depth

            # print("DEPTH", (a, b), file=stderr)

            def check_depth(de: DirEntry, **kwargs):
                d: int = kwargs["depth"]
                # print("check_depth", (d, (a, b)), de.path, file=stderr)
                return d >= a and d <= b

            def enter_depth(de: DirEntry, **kwargs):
                d: int = kwargs["depth"]
                # print("enter_depth", (d, b), de.path, file=stderr)
                return d <= b

            self.on_check_enter(enter_depth)
            self.on_check_accept(check_depth)
        #
        return super().ready()

    def start(self):
        raise DeprecationWarning("Change your code!")

    def _walk_paths(self):
        paths_from: list[str] = getattr(self, "_paths_from", None)
        if paths_from:
            for x in paths_from:
                # print(f"_paths_from {x!r}", file=stderr)
                with as_source(x, "r") as f:
                    for e in f:
                        e = e.strip()
                        if e.startswith("#") or not e:
                            continue
                        # print(f"\t- {e!r}", file=stderr)
                        self._start_path(e)
        #
        paths: list[str] = getattr(self, "_paths", None)
        if paths:
            for p in paths:
                self._start_path(p)


def as_source(path="-", mode="rb"):
    if path != "-":
        return open(path, mode)
    from sys import stdin

    return stdin.buffer if "b" in mode else stdin


def globre3(g: str, base="", escape=lambda x: "", no_neg=False):
    if no_neg is False and g.startswith("!"):
        neg = True
        g = g[1:]
    else:
        neg = None
    if g.endswith("/"):
        g = g[0:-1]
        dir_only = True
    else:
        dir_only = None
    i = g.find("/")
    if i < 0:
        at_start = False
    elif i == 0:
        at_start = True
        g = g[1:]
    else:
        at_start = None
    i, n = 0, len(g)
    res = ""
    while i < n:
        c = g[i]
        i = i + 1
        if c == "*":
            if i < n and "*" == g[i]:
                i = i + 1
                res = res + ".*"
                if i < n and "/" == g[i]:
                    i = i + 1
                    res = res + "/?"
            else:
                res = res + "[^/]*"
        elif c == "?":
            res = res + "[^/]"
        elif c == "[":
            j = i
            if j < n and g[j] == "!":
                j = j + 1
            if j < n and g[j] == "]":
                j = j + 1
            while j < n and g[j] != "]":
                j = j + 1
            if j >= n:
                res = res + "\\["
            else:
                stuff = g[i:j].replace("\\", "\\\\")
                i = j + 1
                if stuff[0] == "!":
                    stuff = "^" + stuff[1:]
                elif stuff[0] == "^":
                    stuff = "\\" + stuff
                res = "%s[%s]" % (res, stuff)
        else:
            x = escape(c)
            assert x
            res = res + x
    if at_start:
        if base:
            res = "^" + escape(base) + "/" + res + r"\Z"
        else:
            res = "^" + res + r"\Z"
    else:
        if base:
            res = r"(?ms)\A" + escape(base) + r"/(?:|.+/)" + res + r"\Z"
        else:
            res = r"(?:|.+/)" + res + r"\Z"
        assert at_start in (None, False)

    return (res, dir_only, neg, g)


def filesizep(s: str):
    if s[-1].isalpha():
        q = s.lower()
        if q.endswith("b"):
            q = q[0:-1]
        for i, v in enumerate("kmgtpezy"):
            if q[-1].endswith(v):
                return int(float(q[0:-1]) * (2 ** (10 * (i + 1))))
        return int(q)
    return int(s)


def sizerangep(s=""):
    f, d, t = s.partition("..")
    if d:
        a, b = [filesizep(f) if f else 0, filesizep(t) if t else float("inf")]
        return (a, b)
    elif f:
        c = filesizep(f)
        return (c, c)
    else:
        return (0, float("inf"))


def intrangep(s=""):
    f, d, t = s.partition("..")
    if d:
        a, b = [int(f) if f else 0, int(t) if t else float("inf")]
        return (a, b)
    elif f:
        c = int(f)
        return (c, c)
    else:
        return (0, float("inf"))

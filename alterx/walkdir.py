from os import DirEntry, scandir, stat, stat_result
from os.path import basename
from typing import List, Callable, Generator

__version__ = "0.0.3"


class FileSystemEntry:
    __slots__ = ("path", "name")

    def __init__(self, path: str) -> None:
        self.path = path
        self.name = basename(self.path)

    def inode(self) -> int:
        return self.stat(follow_symlinks=False).st_ino

    def stat(self, follow_symlinks: bool = True) -> stat_result:
        return stat(self.path, follow_symlinks=follow_symlinks)

    def is_symlink(self, follow_symlinks: bool = True) -> bool:
        return (self.stat(follow_symlinks=follow_symlinks).st_mode & 0o170000) == 0o120000

    def is_dir(self, follow_symlinks: bool = True) -> bool:
        return (self.stat(follow_symlinks=follow_symlinks).st_mode & 0o170000) == 0o040000

    def is_file(self, follow_symlinks: bool = True) -> bool:
        return (self.stat(follow_symlinks=follow_symlinks).st_mode & 0o170000) in (
            0o060000,
            0o100000,
            0o010000,
        )


class WalkDir:
    follow_symlinks: int = 0
    depth_first: bool = False
    carry_on: bool = True
    #
    _root_dir: str = ""
    _check_accept: "tuple[object, tuple[object, object] | None] | None" = None
    _check_enter: "tuple[object, tuple[object, object] | None] | None" = None

    def check_accept(self, e: DirEntry, depth: int) -> bool:
        cur = self._check_accept
        while cur is not None:
            check, then = cur
            if check(e, depth=depth) is False:
                return False
            cur = then
        return True

    def on_check_accept(self, f: Callable[[DirEntry, int], bool]):
        self._check_accept = (f, self._check_accept)

    def on_check_enter(self, f: Callable[[DirEntry, int], bool]):
        self._check_enter = (f, self._check_enter)

    def check_enter(self, x: DirEntry, depth: int) -> bool:
        if not x.is_dir():
            return False
        if x.is_symlink() and not (self.follow_symlinks > 0):
            return False
        cur = self._check_enter
        while cur is not None:
            check, then = cur
            if check(x, depth=depth) is False:
                return False
            cur = then
        return True

    def scan_directory(self, src: str) -> Generator[DirEntry, None, None]:
        try:
            it = scandir(src)
        except Exception as ex:
            if self.file_error(src, ex) is None:
                raise ex
        else:
            yield from it

    def create_entry(self, path: str) -> FileSystemEntry:
        return FileSystemEntry(path)

    def process_entry(self, de: "DirEntry | FileSystemEntry") -> None:
        print(de.path)

    def file_error(self, path: str, ex: Exception) -> None:
        if self.carry_on:
            print(ex)
            return True

    def _walk_breadth_first(self, src: str, depth: int = 0) -> Generator[DirEntry, None, None]:
        depth += 1
        for de in self.scan_directory(src):
            if self.check_accept(de, depth):
                self.process_entry(de)
            if self.check_enter(de, depth):
                self._walk_breadth_first(de.path, depth)

    def _walk_depth_first(self, src: str, depth: int = 0) -> Generator[DirEntry, None, None]:
        depth += 1
        for de in self.scan_directory(src):
            if self.check_enter(de, depth):
                self._walk_depth_first(de.path, depth)
            if self.check_accept(de, depth):
                self.process_entry(de)

    def _start_path(self, p: str):
        de: FileSystemEntry = self.create_entry(p)
        is_dir = None
        try:
            is_dir = de.is_dir()
        except Exception as ex:
            if self.file_error(p, ex) is None:
                raise ex
            return
        if is_dir:
            self._root_dir = de.path
            if self.depth_first:
                self._walk_depth_first(p)
            else:
                self._walk_breadth_first(p)
        else:
            self._root_dir = ""
            self.process_entry(de)

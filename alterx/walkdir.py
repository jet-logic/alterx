import re
from os import DirEntry, scandir, stat, stat_result
from os.path import basename, relpath
from typing import List, Optional, Callable, Generator


class FileSystemEntry:
    __slots__ = ("path", "name")

    def __init__(self, path: str) -> None:
        self.path: str = path
        self.name: str = basename(self.path)

    def inode(self) -> int:
        return self.stat(follow_symlinks=False).st_ino

    def stat(self, follow_symlinks: bool = True) -> stat_result:
        return stat(self.path, follow_symlinks=follow_symlinks)

    def is_symlink(self, follow_symlinks: bool = True) -> bool:
        return (
            self.stat(follow_symlinks=follow_symlinks).st_mode & 0o170000
        ) == 0o120000

    def is_dir(self, follow_symlinks: bool = True) -> bool:
        return (
            self.stat(follow_symlinks=follow_symlinks).st_mode & 0o170000
        ) == 0o040000

    def is_file(self, follow_symlinks: bool = True) -> bool:
        return (self.stat(follow_symlinks=follow_symlinks).st_mode & 0o170000) in (
            0o060000,
            0o100000,
            0o010000,
        )


class WalkDir:
    follow_symlinks: int = 0
    bottom_up: bool = False
    carry_on: bool = True
    excludes: Optional[List[re.Pattern[str]]] = None
    includes: Optional[List[re.Pattern[str]]] = None
    max_depth: int = -1  # Default to -1 for no limit
    _entry_filters: Optional[List[Callable[[DirEntry], bool]]] = None
    _root_dir: str = ""

    def check_accept(self, e: DirEntry) -> bool:
        if self.includes or self.excludes:
            r: str = relpath(e.path, self._root_dir)
            if self.includes:
                if not any(m.search(r) for m in self.includes):
                    return False
            if self.excludes:
                if any(m.search(r) for m in self.excludes):
                    return False

        if self._entry_filters:
            for f in self._entry_filters:
                if f(e) is False:
                    return False
        return True

    def check_enter(self, x: DirEntry, depth: Optional[int] = None) -> bool:
        if self.max_depth != -1 and depth is not None and depth > self.max_depth:
            return False

        if x.is_dir():
            return self.follow_symlinks > 0 if x.is_symlink() else True

        return False

    def scan_directory(self, src: str) -> Generator[DirEntry, None, None]:
        try:
            # enter_dir
            yield from scandir(src)
        except FileNotFoundError:
            pass
        except Exception:
            if self.carry_on:
                pass
            else:
                raise
        else:
            pass
            # entered_dir

    def walk_top_down(
        self, src: str, depth: int = 0
    ) -> Generator[DirEntry, None, None]:
        depth += 1
        for de in self.scan_directory(src):
            if self.check_accept(de):
                yield de
            if self.check_enter(de, depth=depth):
                yield from self.walk_top_down(de.path, depth)

    def walk_bottom_up(
        self, src: str, depth: int = 0
    ) -> Generator[DirEntry, None, None]:
        depth += 1
        for de in self.scan_directory(src):
            if self.check_enter(de, depth=depth):
                yield from self.walk_bottom_up(de.path, depth)
            if self.check_accept(de):
                yield de

    def create_entry(self, path: str) -> FileSystemEntry:
        return FileSystemEntry(path)

    def process_entry(self, de: DirEntry | FileSystemEntry) -> None:
        print(de.path)

    def iterate_paths(
        self, paths: List[str]
    ) -> Generator[DirEntry | FileSystemEntry, None, None]:
        for p in paths:
            de: FileSystemEntry = self.create_entry(p)
            if de.is_dir():
                self._root_dir: str = de.path
                yield from (
                    self.walk_bottom_up(p, depth=0)
                    if self.bottom_up
                    else self.walk_top_down(p, depth=0)
                )
            else:
                yield de

    def start_walk(self, dirs: List[str]) -> None:
        for x in self.iterate_paths(dirs):
            self.process_entry(x)

"""Link-safe text I/O on macOS/Linux, with legacy I/O elsewhere."""
from contextlib import contextmanager
import errno
import os
from pathlib import Path
import stat
import sys


@contextmanager
def _directory(path, create=False):
    path = Path(path)
    anchor = path.anchor or "."
    parts = path.parts[1:] if path.anchor else path.parts
    # These root-owned macOS aliases are trusted, unlike repository path components.
    if sys.platform == "darwin" and path.is_absolute() and parts and parts[0] in {"tmp", "var", "etc"}:
        anchor = str(Path("/") / parts[0])
        anchor = os.path.realpath(anchor)
        parts = parts[1:]
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    fd = os.open(anchor, flags)
    try:
        for part in parts:
            if create:
                try:
                    os.mkdir(part, dir_fd=fd)
                except FileExistsError:
                    pass
            child = os.open(part, flags, dir_fd=fd)
            os.close(fd)
            fd = child
        yield fd
    finally:
        os.close(fd)


def _regular(info, path):
    if not stat.S_ISREG(info.st_mode):
        raise OSError(errno.ELOOP, "Refusing linked or non-regular file", str(path))


@contextmanager
def open_text(path, mode="r", *, errors="strict"):
    """Validate the opened object before reading or truncating it."""
    if mode not in {"r", "w"}:
        raise ValueError("Only text read and write modes are supported")
    if os.name != "posix":
        # shortcut: legacy Windows I/O remains; add native handles when Windows remediation resumes.
        with open(path, mode, encoding="utf-8", errors=errors) as stream:
            yield stream
        return
    path = Path(path)
    with _directory(path.parent) as parent:
        flags = os.O_RDONLY if mode == "r" else os.O_WRONLY | os.O_CREAT
        fd = os.open(path.name, flags | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
                     0o666, dir_fd=parent)
        try:
            info = os.fstat(fd)
            _regular(info, path)
            if mode == "w":
                if info.st_nlink != 1:
                    raise OSError(errno.ELOOP, "Refusing multiply linked output", str(path))
                # Keep the existing inode's ownership, ACL and mode; never truncate by path.
                os.ftruncate(fd, 0)
        except BaseException:
            os.close(fd)
            raise
        with os.fdopen(fd, mode, encoding="utf-8", errors=errors) as stream:
            yield stream


def read_text(path, *, errors="strict"):
    with open_text(path, errors=errors) as stream:
        return stream.read()


def write_text(path, content):
    with open_text(path, "w") as stream:
        stream.write(content)


def make_directory(path):
    if os.name != "posix":
        Path(path).mkdir(parents=True, exist_ok=True)
    else:
        with _directory(path, create=True):
            pass


def remove_file(path):
    if os.name != "posix":
        return os.unlink(path)
    path = Path(path)
    with _directory(path.parent) as parent:
        os.unlink(path.name, dir_fd=parent)

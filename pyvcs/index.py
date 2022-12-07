import hashlib
import operator
import os
import pathlib
import struct
import typing as tp

from pyvcs.objects import hash_object


class GitIndexEntry(tp.NamedTuple):
    # @see: https://github.com/git/git/blob/master/Documentation/technical/index-format.txt
    ctime_s: int
    ctime_n: int
    mtime_s: int
    mtime_n: int
    dev: int
    ino: int
    mode: int
    uid: int
    gid: int
    size: int
    sha1: bytes
    flags: int
    name: str

    def pack(self) -> bytes:
        # pack the data
        return (
            struct.pack(
                f">LLLLLLLLLL20sH{len(self.name.encode())}s", *self[:-1], self.name.encode()
            )
            + b"\x00\x00\x00"
        )

    @staticmethod
    def unpack(data: bytes) -> "GitIndexEntry":
        size = struct.calcsize(">LLLLLLLLLL20sH")
        # unpack the data
        values = struct.unpack(f">LLLLLLLLLL20sH", data[:size])
        # add in tuple value below
        values += (data[size:].split(b"\x00\x00\x00")[0].decode(),)
        return GitIndexEntry(
            *values,
        )


def read_index(gitdir: pathlib.Path) -> tp.List[GitIndexEntry]:
    if not (gitdir / "index").exists():
        return []

    with (gitdir / "index").open("rb") as f:
        data = f.read()
        if data[:4] != b"DIRC":
            raise Exception("Not a valid index file")
        version, count = struct.unpack(">LL", data[4:12])
        if version != 2:
            raise Exception("Unsupported index version")
        entries = []
        offset = 12
        for _ in range(count):
            entry = GitIndexEntry.unpack(data[offset:])
            entries.append(entry)
            offset += 62 + len(entry.name.encode()) + 3
        return entries


def write_index(gitdir: pathlib.Path, entries: tp.List[GitIndexEntry]) -> None:
    data = b"DIRC" + struct.pack(">LL", 2, len(entries))
    for entry in entries:
        data += entry.pack()
    with (gitdir / "index").open("wb") as f:
        f.write(data)
        f.write(hashlib.sha1(data).digest())


def ls_files(gitdir: pathlib.Path, details: bool = False) -> None:
    entries = read_index(gitdir)
    for entry in entries:
        if details:
            print(f"{entry.mode:o} {entry.sha1.hex()} 0\t{entry.name}")
        else:
            print(entry.name)


def update_index(gitdir: pathlib.Path, paths: tp.List[pathlib.Path], write: bool = True) -> None:
    entries = read_index(gitdir)
    for path in paths:
        if not path.exists():
            raise Exception(f"Path {path} does not exist")
        with path.open("rb") as f:
            data = f.read()
        sha1 = hash_object(data, "blob", write=True)
        for entry in entries:
            if entry.name == str(path):
                entries.remove(entry)
                break
        entries.append(
            GitIndexEntry(
                int(path.stat().st_ctime),
                int(path.stat().st_ctime_ns % 1000000000),
                int(path.stat().st_mtime),
                int(path.stat().st_mtime_ns % 1000000000),
                path.stat().st_dev,
                path.stat().st_ino,
                path.stat().st_mode,
                path.stat().st_uid,
                path.stat().st_gid,
                path.stat().st_size,
                bytes.fromhex(sha1),
                0,
                str(path).replace("\\", "/"),
            )
        )
    if write:
        entries.sort(key=operator.attrgetter("name"))
        write_index(gitdir, entries)

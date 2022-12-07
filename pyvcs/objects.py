import hashlib
import os
import pathlib
import re
import stat
import typing as tp
import zlib

from pyvcs.refs import update_ref
from pyvcs.repo import repo_find


def hash_object(data: bytes, fmt: str, write: bool = False) -> str:
    header = f"{fmt} {len(data)}\0".encode()
    store = header + data
    sha = hashlib.sha1(store).hexdigest()
    if write:
        gitdir = repo_find()
        path = gitdir / "objects" / sha[:2] / sha[2:]
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("wb") as f:
            f.write(zlib.compress(store))
    return sha


def resolve_object(obj_name: str, gitdir: pathlib.Path) -> tp.List[str]:
    if len(obj_name) < 4 or len(obj_name) > 40:
        raise Exception(f"Not a valid object name {obj_name}")

    objects = []

    for i in (gitdir / "objects").iterdir():
        if i.is_dir() and i.name == obj_name[:2]:
            for j in i.iterdir():
                if obj_name[2:] in j.name:
                    objects.append(i.name + j.name)

    if len(objects) == 0:
        raise Exception(f"Not a valid object name {obj_name}")

    return objects


def find_object(obj_name: str, gitdir: pathlib.Path) -> str:
    object_new = resolve_object(obj_name, gitdir)
    if len(object_new) == 1:
        return object_new[0]
    else:
        raise Exception(f"Ambiguous object name {obj_name}")


def read_object(sha: str, gitdir: pathlib.Path) -> tp.Tuple[str, bytes]:
    object_new = find_object(sha, gitdir)
    path = gitdir / "objects" / object_new[:2] / object_new[2:]
    with path.open("rb") as f:
        data = zlib.decompress(f.read())
        return data.split(b" ", maxsplit=1)[0].decode(), data.split(b"\0", maxsplit=1)[1]


def read_tree(data: bytes) -> tp.List[tp.Tuple[int, str, str]]:
    result = []
    while data:
        mode, name_sha = data.split(b" ")[:2]
        name, sha = name_sha.split(b"\0")[:2]
        # print(f"Mode: {mode}, Name: {name}, SHA: {sha}")
        result.append((int(oct(int(mode, 8))[2:]), name.decode(), sha[:20].hex()))
        data = data[len(mode) + 2 + len(name) + 20 :]
    return result


def cat_file(obj_name: str, pretty: bool = True) -> None:
    object_new = read_object(obj_name, repo_find())
    if pretty:
        if object_new[0] == "commit":
            print(object_new[1].decode())
        elif object_new[0] == "tree":
            for i in read_tree(object_new[1]):
                print(f"{str(i[0]).zfill(6)} {read_object(i[2], repo_find())[0]} {i[2]}\t{i[1]}")
        elif object_new[0] == "blob":
            print(object_new[1].decode())
    else:
        print(object_new[1].decode())


def find_tree_files(tree_sha: str, gitdir: pathlib.Path) -> tp.List[tp.Tuple[str, str]]:
    result = []
    for mode, name, sha in read_tree(read_object(tree_sha, gitdir)[1]):
        if read_object(sha, gitdir)[0] == "tree":
            tree = find_tree_files(sha, gitdir)
            for i in tree:
                result.append((name + "/" + i[0], i[1]))
        else:
            result.append((name, sha))
    return result


def commit_parse(raw: bytes, start: int = 0, dct=None):
    if dct is None:
        dct = {}
    if start == 0:
        dct["tree"] = raw.split(b"\n", maxsplit=1)[0].decode()
    if start == 1:
        dct["parent"] = raw.split(b"\n", maxsplit=1)[0].decode()
    if start == 2:
        dct["author"] = raw.split(b"\n", maxsplit=1)[0].decode()
    if start == 3:
        dct["committer"] = raw.split(b"\n", maxsplit=1)[0].decode()
    if start == 4:
        dct["message"] = raw.split(b"\n", maxsplit=1)[0].decode()
    if start == 5:
        return dct
    return commit_parse(raw.split(b"\n", maxsplit=1)[1], start + 1, dct)

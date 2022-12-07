import os
import pathlib
import stat
import time
import typing as tp

from pyvcs.index import GitIndexEntry, read_index
from pyvcs.objects import hash_object
from pyvcs.refs import get_ref, is_detached, resolve_head, update_ref


def write_tree(gitdir: pathlib.Path, index: tp.List[GitIndexEntry], dirname: str = "") -> str:
    tree = b""
    for entry in index:
        position = entry.name.rfind("/")
        dirname = "" if position == -1 else entry.name[:position]
        # print(entry.name)
        # if dirname == "":
        # 	tree += f"{entry.mode} {entry.name}\0{bytes.hex(entry.sha1)}"
        # else:
        # 	tree += f"{entry.mode} {entry.name[len(dirname)+1:]}\0{entry.sha1}"
        if dirname == "":
            tree += oct(entry.mode)[2:].encode() + b" "
            tree += entry.name.encode() + b"\0"
            tree += entry.sha1
        else:
            temp_object = b""
            temp_object += oct(entry.mode)[2:].encode() + b" "
            temp_object += entry.name[len(dirname) + 1 :].encode() + b"\0"
            temp_object += entry.sha1
            sha1 = hash_object(temp_object, "tree", True)

            tree += oct(stat.S_IFDIR | 0o000)[2:].encode() + b" "
            tree += dirname.encode() + b"\0"
            tree += bytes.fromhex(sha1)

    return hash_object(tree, "tree", True)


def commit_tree(
    gitdir: pathlib.Path,
    tree: str,
    message: str,
    parent: tp.Optional[str] = None,
    author: tp.Optional[str] = None,
) -> str:
    if author is None:
        author = f"{os.environ['GIT_AUTHOR_NAME']} <{os.environ['GIT_AUTHOR_EMAIL']}>"

    timestamp = int(time.mktime(time.localtime()))

    commit = f"tree {tree}\n"
    if parent:
        commit += f"parent {parent}\n"
    commit += f"author {author} {timestamp} +0300\n"
    commit += f"committer {author} {timestamp} +0300\n\n"
    commit += f"{message}\n"
    return hash_object(commit.encode("ascii"), "commit", True)

import os
import pathlib
import shutil
import typing as tp

from pyvcs.index import read_index, update_index
from pyvcs.objects import (
    cat_file,
    commit_parse,
    find_object,
    find_tree_files,
    read_object,
)
from pyvcs.refs import get_ref, is_detached, resolve_head, update_ref
from pyvcs.tree import commit_tree, write_tree


def add(gitdir: pathlib.Path, paths: tp.List[pathlib.Path]) -> None:
    update_index(gitdir, paths)


def commit(gitdir: pathlib.Path, message: str, author: tp.Optional[str] = None) -> str:
    return commit_tree(gitdir, write_tree(gitdir, read_index(gitdir)), message, author=author)


def checkout(gitdir: pathlib.Path, obj_name: str) -> None:
    ref_file = gitdir / "refs" / "heads" / obj_name
    if ref_file.exists():
        with open(ref_file, "w") as f:
            obj_name = f.read()

    indexes = read_index(gitdir)
    for index in indexes:
        if pathlib.Path(index.name).is_file():
            name = index.name.split("/")
            if len(name) > 1:
                shutil.rmtree(name[0])
            else:
                os.remove(index.name)

    object_by_sha = read_object(obj_name, gitdir)
    sha = object_by_sha[1].decode().split("\n")[0].split()[1]

    for tree_obj in find_tree_files(sha, gitdir):
        name = tree_obj[0].split("/")

        if len(name) > 1:
            pathlib.Path(name[0]).absolute().mkdir()

        with open(tree_obj[0], "w") as f:
            f.write(read_object(tree_obj[1], gitdir)[1].decode())

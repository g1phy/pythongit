import os
import pathlib
import typing as tp


def repo_find(workdir: tp.Union[str, pathlib.Path] = ".") -> pathlib.Path:
    # Find repository directory
    workdir = pathlib.Path(workdir)
    if not workdir.is_dir():
        raise NotADirectoryError(workdir)
    gitdir = workdir / os.environ.get("GIT_DIR", ".git")
    while not gitdir.is_dir():
        if workdir.parent == workdir:
            raise Exception(f"Not a git repository")
        workdir = workdir.parent
        gitdir = workdir / os.environ.get("GIT_DIR", ".git")
    return gitdir


def repo_create(workdir: tp.Union[str, pathlib.Path]) -> pathlib.Path:
    # Create repository directory
    workdir = pathlib.Path(workdir)
    if not workdir.is_dir():
        raise Exception(f"{workdir} is not a directory")
    gitdir = workdir / os.environ.get("GIT_DIR", ".git")
    if gitdir.is_dir():
        raise FileExistsError(gitdir)
    os.makedirs(gitdir)
    os.makedirs(gitdir / "branches")
    os.makedirs(gitdir / "objects")
    os.makedirs(gitdir / "refs" / "tags")
    os.makedirs(gitdir / "refs" / "heads")
    with open(gitdir / "HEAD", "wt") as f:
        f.write("ref: refs/heads/master\n")
    with open(gitdir / "config", "wt") as f:
        f.write(
            "[core]\n\trepositoryformatversion = 0\n\tfilemode = true\n\tbare = false\n\tlogallrefupdates = false\n"
        )
    with open(gitdir / "description", "wt") as f:
        f.write("Unnamed pyvcs repository.\n")

    return gitdir

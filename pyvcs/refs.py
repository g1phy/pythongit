import pathlib
import typing as tp


def update_ref(gitdir: pathlib.Path, ref: tp.Union[str, pathlib.Path], new_value: str) -> None:
    path = gitdir / ref
    with open(path, "w") as f:
        f.write(new_value)


def symbolic_ref(gitdir: pathlib.Path, name: str, ref: str) -> None:
    path = gitdir / name
    with open(path, "w") as f:
        f.write("ref: " + ref)


def ref_resolve(gitdir: pathlib.Path, refname: str) -> tp.Optional[str]:
    if refname == "HEAD":
        refname = get_ref(gitdir)

    path = gitdir / refname
    if not path.exists():
        return None

    with open(path, "r") as f:
        ref = f.read().strip()
    return ref


def resolve_head(gitdir: pathlib.Path) -> tp.Optional[str]:
    return ref_resolve(gitdir, "HEAD")


def is_detached(gitdir: pathlib.Path) -> bool:
    path = gitdir / "HEAD"
    with open(path, "r") as f:
        ref = f.read().strip()

    if ref[:5] == "ref: ":
        return False

    return True


def get_ref(gitdir: pathlib.Path) -> str:
    path = gitdir / "HEAD"
    with open(path, "r") as f:
        ref = f.read().strip()

    if ref[:5] == "ref: ":
        return ref[5:]

    return ref

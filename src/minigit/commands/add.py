"""minigit add: stage file contents for the next commit.

For each file, ``add`` stores its content as a blob object and records
``path -> blob sha`` in the index.
"""

import argparse
from pathlib import Path

from minigit.changes import head_files
from minigit.errors import MinigitError
from minigit.index import Index, IndexEntry
from minigit.objects import FILE_MODE, write_object
from minigit.repo import Repository
from minigit.worktree import iter_files, repo_relative

NAME = "add"
HELP = "Add file contents to the staging area"


def configure(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("paths", nargs="+", help="files or directories to stage")


def run(args: argparse.Namespace, repo: Repository | None) -> int:
    assert repo is not None
    index = Index.load(repo)
    head = head_files(repo)
    old_index = {entry.path: entry.sha for entry in index}
    staged_results: dict[str, str] = {}

    for raw in args.paths:
        deleted = _stage_deletions(index, repo, raw)
        for path in deleted:
            staged_results[path] = "deleted"
        if not Path(raw).exists():
            continue
        is_explicit_file = not Path(raw).is_dir()
        for path in _expand(repo, raw):
            sha = write_object(repo, (repo.worktree / path).read_bytes(), "blob")
            index.add(IndexEntry(FILE_MODE, sha, path))
            if path not in head:
                status = "new file"
            elif sha != head[path]:
                status = "modified"
            else:
                status = None

            if status is not None:
                if is_explicit_file or path not in old_index or old_index[path] != sha:
                    staged_results[path] = status

    index.save(repo)
    for path in sorted(staged_results):
        print(f"staged: {path} ({staged_results[path]})")
    return 0


def _stage_deletions(index, repo, raw) -> list[str]:
    """Remove staged entries under ``raw`` whose files no longer exist on disk.

    Raises if ``raw`` doesn't exist and nothing staged matches it.
    """
    relative = repo_relative(repo, raw)
    deleted = [
        e.path
        for e in index
        if (relative == "" or e.path == relative or e.path.startswith(relative + "/"))
        and not (repo.worktree / e.path).exists()
    ]
    for path in deleted:
        index.remove(path)
    if not deleted and not Path(raw).exists():
        raise MinigitError(f"pathspec '{raw}' did not match any files")
    return deleted


def _expand(repo, raw):
    """Turn one path argument into the list of files it names."""
    path = Path(raw)
    relative = repo_relative(repo, path)
    if not path.is_dir():
        return [relative]
    prefix = f"{relative}/" if relative else ""
    return [f for f in iter_files(repo) if f.startswith(prefix)]

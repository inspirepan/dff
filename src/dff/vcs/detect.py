from __future__ import annotations

from pathlib import Path

from dff.vcs.base import Backend
from dff.vcs.git import GitBackend
from dff.vcs.jj import JjBackend


class DetectError(RuntimeError):
    pass


def find_repo_root(start: Path) -> Path:
    current = start.resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".jj").exists() or (candidate / ".git").exists():
            return candidate
    raise DetectError(f"No jj or git repo found from {start}")


def detect_backend(start: Path, preferred: str | None = None) -> Backend:
    root = find_repo_root(start)
    has_jj = (root / ".jj").exists()
    has_git = (root / ".git").exists()

    if preferred == "git":
        return GitBackend(root)
    if preferred == "jj":
        return JjBackend(root)
    if has_jj:
        return JjBackend(root)
    if has_git:
        return GitBackend(root)
    raise DetectError(f"No jj or git repo found from {start}")

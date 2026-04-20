from __future__ import annotations

import subprocess
from pathlib import Path

from dff.models import HunkStats
from dff.vcs.base import Backend
from dff.vcs.jj import JjBackend


def run(args: list[str], cwd: Path) -> None:
    subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True)


def jj_repo_with_feature_change(tmp_path: Path) -> Path:
    run(["jj", "git", "init", "."], tmp_path)
    (tmp_path / "base.txt").write_text("base\n")
    run(["jj", "file", "track", "base.txt"], tmp_path)
    run(["jj", "describe", "-m", "base"], tmp_path)
    run(["jj", "bookmark", "create", "trunk", "-r", "@"], tmp_path)
    run(["jj", "new", "trunk"], tmp_path)
    (tmp_path / "added.txt").write_text("added\n")
    run(["jj", "file", "track", "added.txt"], tmp_path)
    (tmp_path / "base.txt").write_text("base\nfeature\n")
    run(["jj", "describe", "-m", "feature"], tmp_path)
    return tmp_path


def test_jj_backend_satisfies_backend_protocol(tmp_path: Path) -> None:
    root = jj_repo_with_feature_change(tmp_path)

    backend = JjBackend(root)

    assert isinstance(backend, Backend)


def test_jj_backend_lists_requested_revset_for_tree(tmp_path: Path) -> None:
    root = jj_repo_with_feature_change(tmp_path)
    backend = JjBackend(root)

    changes = backend.list_changes(rev="@")

    assert [change.description for change in changes] == ["feature"]

    files = {file_change.path: file_change for file_change in changes[0].files}
    assert files["base.txt"].status == "M"
    assert files["base.txt"].stats == HunkStats(1, 0)
    assert files["added.txt"].status == "A"
    assert files["added.txt"].stats == HunkStats(1, 0)


def test_jj_backend_defaults_to_current_revset(tmp_path: Path) -> None:
    root = jj_repo_with_feature_change(tmp_path)

    changes = JjBackend(root).list_changes()

    assert changes
    assert changes[0].files

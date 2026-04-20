from __future__ import annotations

import subprocess
from pathlib import Path

from dff.models import Change, FileChange, HunkStats
from dff.vcs.base import BackendError


class GitBackend:
    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root

    def list_changes(self, *, rev: str | None = None) -> tuple[Change, ...]:
        staged = self._collect_change(
            description="Staged",
            change_id="git-staged",
            graph="●",
            name_status_args=["diff", "--cached", "--name-status", "-z", "-M"],
            numstat_args=["diff", "--cached", "--numstat", "-z", "-M"],
        )
        unstaged = self._collect_change(
            description="Unstaged",
            change_id="git-unstaged",
            graph="○",
            name_status_args=["diff", "--name-status", "-z", "-M"],
            numstat_args=["diff", "--numstat", "-z", "-M"],
        )
        return tuple(change for change in (staged, unstaged) if change is not None)

    def _collect_change(
        self,
        *,
        description: str,
        change_id: str,
        graph: str,
        name_status_args: list[str],
        numstat_args: list[str],
    ) -> Change | None:
        statuses = self._parse_name_status(self._run(*name_status_args))
        if not statuses:
            return None
        stats, binary_paths = self._parse_numstat(self._run(*numstat_args))
        files = tuple(
            FileChange(
                path=path,
                status=entry["status"],
                old_path=entry.get("old_path"),
                stats=stats.get(path, HunkStats()),
                is_binary=path in binary_paths,
            )
            for path, entry in statuses.items()
        )
        return Change(change_id=change_id, short_id=description, description=description, files=files, graph=graph)

    def _run(self, *args: str) -> str:
        try:
            completed = subprocess.run(
                ["git", *args],
                cwd=self.repo_root,
                check=True,
                capture_output=True,
                text=False,
            )
        except FileNotFoundError as exc:
            raise BackendError("git is not installed or not on PATH") from exc
        except subprocess.CalledProcessError as exc:
            raise BackendError(
                exc.stderr.decode().strip() or exc.stdout.decode().strip() or "git command failed"
            ) from exc
        return completed.stdout.decode()

    def _parse_name_status(self, output: str) -> dict[str, dict[str, str]]:
        parts = [part for part in output.split("\0") if part]
        statuses: dict[str, dict[str, str]] = {}
        index = 0
        while index < len(parts):
            token = parts[index]
            status = token[0]
            if status == "R":
                old_path = parts[index + 1]
                new_path = parts[index + 2]
                statuses[new_path] = {"status": "R", "old_path": old_path}
                index += 3
                continue
            path = parts[index + 1]
            statuses[path] = {"status": status}
            index += 2
        return statuses

    def _parse_numstat(self, output: str) -> tuple[dict[str, HunkStats], set[str]]:
        parts = [part for part in output.split("\0") if part]
        stats: dict[str, HunkStats] = {}
        binary_paths: set[str] = set()
        index = 0
        while index < len(parts):
            fields = parts[index].split("\t")
            added_text = fields[0]
            removed_text = fields[1]
            if len(fields) == 3 and fields[2]:
                path = fields[2]
                index += 1
            else:
                path = parts[index + 2]
                index += 3
            if added_text == "-" and removed_text == "-":
                binary_paths.add(path)
                continue
            stats[path] = HunkStats(int(added_text), int(removed_text))
        return stats, binary_paths

#!/usr/bin/env python3
"""Reject unsafe or generated files from the staged commit."""

from pathlib import PurePosixPath
import subprocess
import sys


FORBIDDEN_NAMES = {".env", ".env.local", ".env.production"}
FORBIDDEN_SUFFIXES = {
    ".db", ".sqlite", ".sqlite3", ".pem", ".key", ".p12", ".pfx",
}
FORBIDDEN_PARTS = {"target", "node_modules", ".venv", "secrets", ".secrets"}


def staged_paths():
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
        check=True,
        capture_output=True,
        text=True,
    )
    return [PurePosixPath(path) for path in result.stdout.splitlines() if path]


def is_forbidden(path):
    name = path.name.lower()
    parts = {part.lower() for part in path.parts}
    return (
        name in FORBIDDEN_NAMES
        or (name.startswith(".env.") and name != ".env.example")
        or path.suffix.lower() in FORBIDDEN_SUFFIXES
        or bool(parts & FORBIDDEN_PARTS)
        or name.endswith(("-credentials.json", "service-account.json"))
        or name.endswith((".db-wal", ".db-shm", ".sqlite-wal", ".sqlite-shm"))
    )


def main():
    blocked = [path.as_posix() for path in staged_paths() if is_forbidden(path)]
    if blocked:
        print("Refus: fichiers secrets ou générés dans l'index :", file=sys.stderr)
        print("\n".join(f"  {path}" for path in blocked), file=sys.stderr)
        return 1
    result = subprocess.run(["git", "diff", "--cached", "--check"], check=False)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())

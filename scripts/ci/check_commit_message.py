#!/usr/bin/env python3
"""Validate GenOS-style commit subjects and exact changed-file receipts."""

import re
import subprocess
import sys


RECEIPT_TAGS = {"FEAT", "FIX", "EVOLUTION", "REFACTOR"}
SUBJECT = re.compile(r"^\[([A-Z]+)\] .+")


def staged_paths():
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        check=True,
        capture_output=True,
        text=True,
    )
    return {path for path in result.stdout.splitlines() if path}


def read_receipt(message):
    lines = message.splitlines()
    for position, line in enumerate(lines):
        if line.strip().lower() != "receipt:":
            continue
        receipt = []
        for entry in lines[position + 1:]:
            if not entry.strip():
                break
            value = entry.strip()
            if value.startswith(("- ", "* ")):
                value = value[2:].strip()
            receipt.append(value)
        return receipt
    return None


def main():
    if len(sys.argv) != 2:
        print("Usage: check_commit_message.py <message-file>", file=sys.stderr)
        return 2
    with open(sys.argv[1], encoding="utf-8") as message_file:
        message = message_file.read()
    first_line = (message.splitlines() or [""])[0]
    match = SUBJECT.fullmatch(first_line)
    if not match:
        print("Le sujet doit commencer par un tag majuscule, ex. [FEAT].", file=sys.stderr)
        return 1
    if match.group(1) not in RECEIPT_TAGS:
        return 0
    declared = read_receipt(message)
    if declared is None:
        print("Bloc Receipt: requis pour ce type de commit.", file=sys.stderr)
        return 1
    actual = staged_paths()
    listed = set(declared)
    if len(declared) != len(listed) or listed != actual:
        print("Le bloc Receipt: doit lister exactement les fichiers staged.", file=sys.stderr)
        print(f"Attendus : {sorted(actual)}", file=sys.stderr)
        print(f"Déclarés : {sorted(listed)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

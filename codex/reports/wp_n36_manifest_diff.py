#!/usr/bin/env python3
"""Compare two Julia Manifest.toml files for WP-N36."""

from __future__ import annotations

import argparse
import sys
import tomllib
from pathlib import Path


def load_manifest(path: Path) -> dict[str, dict[str, object]]:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    deps = data.get("deps", {})
    packages: dict[str, dict[str, object]] = {}
    for name, entries in deps.items():
        if isinstance(entries, list):
            if len(entries) != 1:
                raise ValueError(f"{path}: dependency {name} has {len(entries)} entries")
            entry = entries[0]
        else:
            entry = entries
        if not isinstance(entry, dict):
            raise ValueError(f"{path}: dependency {name} is not a table")
        packages[name] = entry
    return packages


def value(entry: dict[str, object], key: str) -> str:
    item = entry.get(key, "")
    return "" if item is None else str(item)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("before", type=Path)
    parser.add_argument("after", type=Path)
    args = parser.parse_args()

    before = load_manifest(args.before)
    after = load_manifest(args.after)

    removed = sorted(set(before) - set(after))
    added = sorted(set(after) - set(before))
    remaining = sorted(set(before) & set(after))
    changed = []
    for name in remaining:
        old = before[name]
        new = after[name]
        if value(old, "version") != value(new, "version") or value(old, "git-tree-sha1") != value(new, "git-tree-sha1"):
            changed.append(
                (
                    name,
                    value(old, "version"),
                    value(new, "version"),
                    value(old, "git-tree-sha1"),
                    value(new, "git-tree-sha1"),
                )
            )

    print(f"removed_count: {len(removed)}")
    print(f"remaining_count: {len(remaining)}")
    print(f"added_count: {len(added)}")
    print(f"changed_version_or_hash_count: {len(changed)}")
    print()
    print("removed:")
    for name in removed:
        print(f"  {name}")
    print()
    print("added:")
    for name in added:
        print(f"  {name}")
    print()
    print("changed_version_or_hash:")
    for name, old_version, new_version, old_hash, new_hash in changed:
        print(f"  {name}: version {old_version} -> {new_version}; git-tree-sha1 {old_hash} -> {new_hash}")

    return 0 if not added and not changed else 1


if __name__ == "__main__":
    sys.exit(main())

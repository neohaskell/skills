#!/usr/bin/env python3
"""Compare a consumer installation with immutable release trees; never mutate it."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys

SOURCE = "neohaskell/skills"
ORIGINS = {"https://github.com/neohaskell/skills.git", "https://github.com/neohaskell/skills", "git@github.com:neohaskell/skills.git", "ssh://git@github.com/neohaskell/skills.git"}
EXCLUDED_FILES = {"metadata.json"}
EXCLUDED_DIRS = {".git", "__pycache__", "__pypackages__"}


def git(repo: Path, *args: str) -> bytes:
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, check=False)
    if result.returncode:
        raise ValueError(result.stderr.decode(errors="replace").strip())
    return result.stdout


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def release(repo: Path, ref: str | None) -> dict:
    if ref is None:
        return {}
    if not re.fullmatch(r"[0-9a-f]{40}", ref):
        raise ValueError("release identities must be full lowercase 40-character commit SHAs")
    if git(repo, "rev-parse", f"{ref}^{{commit}}").decode().strip() != ref:
        raise ValueError("release identity did not resolve to the specified commit")
    records = git(repo, "ls-tree", "-rz", ref, "--", "skills/").split(b"\0")
    groups: dict = {}
    for record in filter(None, records):
        meta, raw_path = record.split(b"\t", 1)
        mode, kind, blob = meta.decode().split()
        parts = raw_path.decode().split("/")
        if len(parts) < 3:
            continue
        name, relative = parts[1], "/".join(parts[2:])
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", name):
            raise ValueError(f"unsupported skill name: {name}")
        if parts[-1] in EXCLUDED_FILES or any(part in EXCLUDED_DIRS for part in parts[2:-1]):
            continue
        if kind != "blob" or mode not in {"100644", "100755"}:
            raise ValueError(f"release resource is not an ordinary file: {name}/{relative}")
        content = git(repo, "cat-file", "blob", blob)
        groups.setdefault(name, {})[relative] = {"kind": "file", "sha256": digest(content), "executable": mode == "100755"}
    groups = {name: files for name, files in groups.items() if "SKILL.md" in files}
    if not groups:
        raise ValueError(f"no skill entries in release {ref}")
    return groups


def fingerprint(path: Path):
    if path.is_symlink():
        return {"kind": "link", "target": os.readlink(path)}
    if not path.exists():
        return None
    mode = path.stat().st_mode
    if stat.S_ISREG(mode):
        return {"kind": "file", "sha256": digest(path.read_bytes()), "executable": bool(mode & 0o111)}
    if not stat.S_ISDIR(mode):
        raise ValueError(f"unsupported filesystem object: {path}")
    return {"kind": "directory", "entries": {child.name: fingerprint(child) for child in sorted(path.iterdir())}}


def flatten(tree, prefix=""):
    if not tree or tree.get("kind") != "directory":
        return None
    result = {}
    for name, entry in tree["entries"].items():
        relative = prefix + name
        if entry["kind"] == "directory":
            nested = flatten(entry, relative + "/")
            if not nested:
                result[relative + "/"] = {"kind": "empty-directory"}
            else:
                result.update(nested)
        else:
            result[relative] = entry
    return result


def read_lock(root: Path):
    path = root / "skills-lock.json"
    if path.is_symlink():
        raise ValueError("skills-lock.json must not be a symlink")
    if not path.exists():
        return {"version": 1, "skills": {}}
    def unique_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate lock key: {key}")
            result[key] = value
        return result
    lock = json.loads(path.read_text(), object_pairs_hook=unique_pairs)
    if not isinstance(lock, dict) or lock.get("version") != 1 or not isinstance(lock.get("skills"), dict):
        raise ValueError("unsupported or invalid skills-lock.json; preserve it and resolve its identity")
    if any(not isinstance(entry, dict) for entry in lock["skills"].values()):
        raise ValueError("invalid skill lock entry")
    return lock


def roots(root: Path):
    for relative in (".agents", ".agents/skills", ".claude", ".claude/skills"):
        path = root / relative
        if path.is_symlink() or (path.exists() and not path.is_dir()):
            raise ValueError(f"unsupported host path: {path}; preserve it and resolve the layout")
    return {host: {p.name: fingerprint(p) for p in sorted((root / host).iterdir())} if (root / host).exists() else {} for host in (".agents/skills", ".claude/skills")}


def valid_entry(entry, name, ref):
    return (entry.get("source") == SOURCE and entry.get("sourceType") == "github"
            and entry.get("ref") == ref and entry.get("skillPath") == f"skills/{name}/SKILL.md"
            and isinstance(entry.get("computedHash"), str)
            and re.fullmatch(r"[0-9a-f]{64}", entry["computedHash"]) is not None
            and entry.get("installMode") != "copy")


def inspect_release(names, ref, paths, lock, errors):
    for name, expected in names.items():
        actual = flatten(paths[".agents/skills"].get(name))
        if actual != expected:
            changed = sorted(set(expected) | set(actual or {}))
            changed = [p for p in changed if expected.get(p) != (actual or {}).get(p)]
            errors.append(f"{name}: canonical content differs or is missing: {', '.join(changed[:8])}")
        link = paths[".claude/skills"].get(name)
        if link != {"kind": "link", "target": f"../../.agents/skills/{name}"}:
            errors.append(f"{name}: expected relative Claude link is missing or customized")
        if not valid_entry(lock["skills"].get(name, {}), name, ref):
            errors.append(f"{name}: lock ownership/ref/path/hash shape is not established")


def unrelated(paths, lock, managed):
    return {
        "paths": {host: {name: value for name, value in entries.items() if name not in managed} for host, entries in paths.items()},
        "lock": {**lock, "skills": {name: value for name, value in lock["skills"].items() if name not in managed}},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("before", "after"))
    parser.add_argument("--consumer", type=Path, required=True)
    parser.add_argument("--source-repo", type=Path, required=True)
    parser.add_argument("--old")
    parser.add_argument("--new", required=True)
    parser.add_argument("--snapshot", type=Path, required=True)
    args = parser.parse_args()
    try:
        root, source, snapshot = args.consumer.resolve(), args.source_repo.resolve(), args.snapshot.resolve()
        if snapshot.is_relative_to(root):
            raise ValueError("put the temporary snapshot outside the consumer repository")
        if git(root, "rev-parse", "--show-toplevel").decode().strip() != str(root):
            raise ValueError("consumer must be its Git root")
        if git(source, "remote", "get-url", "origin").decode().strip() not in ORIGINS:
            raise ValueError("source repository origin is not the official collection")
        old, new = release(source, args.old), release(source, args.new)
        paths, lock, errors = roots(root), read_lock(root), []
        managed = set(old) | set(new)
        found_owned = {name for name, entry in lock["skills"].items() if entry.get("source") == SOURCE}
        if args.phase == "before":
            if found_owned != set(old):
                errors.append("collection lock names do not match the complete identified old release")
            inspect_release(old, args.old, paths, lock, errors)
            for name in sorted(set(new) - set(old)):
                if name in lock["skills"] or any(name in entries for entries in paths.values()):
                    errors.append(f"{name}: new-name collision; existing content is preserved")
            report = {"consumer": str(root), "old": args.old, "new": args.new,
                      "add": sorted(set(new) - set(old)), "remove": sorted(set(old) - set(new)),
                      "retain": sorted(set(old) & set(new)), "conflicts": errors}
            if not errors:
                report["unrelated"] = unrelated(paths, lock, managed)
                with snapshot.open("x", encoding="utf-8") as stream:
                    json.dump(report, stream, indent=2, sort_keys=True)
                    stream.write("\n")
        else:
            saved = json.loads(snapshot.read_text())
            if (saved.get("consumer"), saved.get("old"), saved.get("new"), saved.get("conflicts")) != (str(root), args.old, args.new, []):
                raise ValueError("snapshot does not identify this clear before-operation comparison")
            inspect_release(new, args.new, paths, lock, errors)
            if found_owned != set(new):
                errors.append("collection lock names do not match the complete target release")
            for name in sorted(set(old) - set(new)):
                if name in lock["skills"] or any(name in entries for entries in paths.values()):
                    errors.append(f"{name}: owned removal still needs explicit reconciliation")
            if unrelated(paths, lock, managed) != saved.get("unrelated"):
                errors.append("unrelated skill paths or lock data changed; preserve and reconcile them")
            report = {"consumer": str(root), "old": args.old, "new": args.new, "conflicts": errors}
        visible = {key: value for key, value in report.items() if key != "unrelated"}
        print(json.dumps(visible, indent=2))
        return 1 if errors else 0
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"comparison unavailable: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

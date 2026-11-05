#!/usr/bin/env python3
"""Validate reviewer JSON without treating prose as a verdict."""
import argparse
import json
from pathlib import Path
import sys


def validate(value):
    if not isinstance(value, dict) or set(value) != {"summary", "findings"}:
        raise ValueError("expected exactly summary and findings")
    if not isinstance(value["summary"], str) or not value["summary"].strip():
        raise ValueError("summary must be non-empty text")
    if not isinstance(value["findings"], list):
        raise ValueError("findings must be an array")
    for item in value["findings"]:
        if not isinstance(item, dict) or set(item) != {"severity", "file", "line", "message", "fix"}:
            raise ValueError("finding fields do not match the schema")
        if item["severity"] not in ("blocker", "major", "minor", "nit"):
            raise ValueError("unknown severity")
        if type(item["line"]) is not int or item["line"] < 1:
            raise ValueError("line must be a positive integer")
        for key in ("file", "message", "fix"):
            if not isinstance(item[key], str) or not item[key].strip():
                raise ValueError(f"{key} must be non-empty text")
    return value


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--reviewer-exit-code", type=int, required=True)
    args = parser.parse_args(argv)
    if args.reviewer_exit_code != 0:
        print(json.dumps({"status": "reviewer_failed", "exit_code": args.reviewer_exit_code}))
        return 3
    try:
        review = validate(json.loads(args.output.read_text(), object_pairs_hook=unique_object))
    except (OSError, UnicodeError, ValueError, TypeError) as error:
        print(json.dumps({"status": "malformed", "error": str(error)}))
        return 2
    blockers = sum(item["severity"] == "blocker" for item in review["findings"])
    print(json.dumps({"status": "blockers" if blockers else "clean", "blockers": blockers, **review}))
    return 1 if blockers else 0


if __name__ == "__main__":
    sys.exit(main())

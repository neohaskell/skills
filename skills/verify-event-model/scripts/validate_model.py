#!/usr/bin/env python3
"""Read-only v1 event-model validation for application use."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", type=Path)
    args = parser.parse_args()
    try:
        from jsonschema import Draft202012Validator
        schema_path = Path(__file__).resolve().parents[2] / "event-modeling/references/event-model.schema.json"
        schema = json.loads(schema_path.read_text())
        model = json.loads(args.model.read_text())
    except (ImportError, OSError, ValueError) as error:
        print(json.dumps({"status": "unavailable", "checks": {"schema": "not_run", "references": "not_run"}, "error": str(error)}))
        return 2
    findings = []

    def finding(category, identity, message, fix):
        findings.append({"category": category, "severity": "blocker", "id": identity, "message": message, "fix": fix})

    for error in Draft202012Validator(schema).iter_errors(model):
        location = "/" + "/".join(map(str, error.absolute_path))
        finding("schema", location, error.message, "Match the canonical v1 schema.")
    if findings:
        print(json.dumps({"status": "invalid", "checks": {"schema": "failed", "references": "not_run"}, "findings": findings}))
        return 1
    groups = ("submodels", "chapters", "entities", "slices", "nodes", "edges")
    ids = {group: {item["id"] for item in model.get(group, [])} for group in groups}
    for group in groups:
        for identity, count in Counter(item["id"] for item in model.get(group, [])).items():
            if count > 1:
                finding("duplicate_id", identity, f"Duplicate ID in {group}.", "Choose unique IDs and update their references.")
    for group, field, target in (("chapters", "submodelId", "submodels"), ("slices", "chapterId", "chapters"), ("nodes", "sliceId", "slices"), ("nodes", "entityId", "entities"), ("edges", "sourceId", "nodes"), ("edges", "targetId", "nodes")):
        for item in model.get(group, []):
            value = item.get(field)
            if value is not None and value not in ids[target]:
                finding("reference", item["id"], f"{field} references missing {target}: {value}", "Correct the reference or define the intended target.")
    types = {node["id"]: node["type"] for node in model["nodes"]}
    endpoints = {"commandProducesEvent": ("command", "event"), "eventFeedsQuery": ("event", "query"), "eventTriggersIntegration": ("event", "integration"), "integrationTriggersCommand": ("integration", "command"), "commandFromUI": ("uiPlaceholder", "command"), "queryToUI": ("query", "uiPlaceholder")}
    for edge in model["edges"]:
        actual = (types.get(edge["sourceId"]), types.get(edge["targetId"]))
        if actual != endpoints[edge["type"]]:
            finding("edge_type", edge["id"], f"Unexpected endpoint types: {actual}", f"Use {endpoints[edge['type']]} endpoints.")
    print(json.dumps({"status": "invalid" if findings else "valid", "checks": {"schema": "passed", "references": "failed" if findings else "passed", "methodology": "not_run"}, "findings": findings}))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())

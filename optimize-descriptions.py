#!/usr/bin/env python3
"""Turnkey driver: optimize every skill's frontmatter `description` for triggering.

Wraps skill-creator's run_loop.py across all skills, then AUTO-APPLIES each
winning description back into the SKILL.md frontmatter and re-validates.

Prerequisites (already in this repo):
  - .claude/skills/skill-creator/scripts/  (run_loop.py etc.)
  - .skill-eval/<skill>.json               (one trigger eval-set per skill)

Usage (from the repo root):
  python optimize-descriptions.py --model sonnet            # optimize all, apply winners
  python optimize-descriptions.py --model sonnet --dry-run  # show winners, don't write
  python optimize-descriptions.py --model opus --skills neohaskell-feature-pipeline write-unit-tests
  python optimize-descriptions.py --skip-preflight ...      # bypass the harness sanity check

IMPORTANT: run_eval spawns `claude -p` subprocesses. If the pre-flight check
reports 0 triggers on clear positives, the triggering harness is NOT firing in
your environment (it uses a .claude/commands/ proxy). Do not run the full batch
until the pre-flight passes, or you will burn hours on an all-zero signal.
"""

import argparse
import json
import re
import subprocess
import sys
import textwrap
from pathlib import Path

REPO = Path(__file__).resolve().parent
SKILL_CREATOR = REPO / ".claude" / "skills" / "skill-creator"
EVAL_DIR = REPO / ".skill-eval"
SKILLS_DIR = REPO / "skills"
ALLOWED_FM = {"name", "description", "license", "allowed-tools", "metadata", "compatibility"}


def all_skills():
    return sorted(d.name for d in SKILLS_DIR.iterdir() if d.is_dir() and (d / "SKILL.md").exists())


def run_loop_for(skill: str, model: str, iters: int, runs: int, workers: int) -> dict:
    """Run run_loop.py for one skill; return its JSON output (with best_description)."""
    eval_set = EVAL_DIR / f"{skill}.json"
    skill_path = SKILLS_DIR / skill
    if not eval_set.exists():
        raise FileNotFoundError(f"no eval-set: {eval_set}")
    cmd = [
        sys.executable, "-m", "scripts.run_loop",
        "--eval-set", str(eval_set),
        "--skill-path", str(skill_path),
        "--model", model,
        "--max-iterations", str(iters),
        "--runs-per-query", str(runs),
        "--num-workers", str(workers),
        "--report", "none",
    ]
    # cwd = skill-creator so `scripts` package imports; find_project_root() walks up to the repo.
    proc = subprocess.run(cmd, cwd=str(SKILL_CREATOR), capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"run_loop failed for {skill}:\n{proc.stderr[-2000:]}")
    # run_loop prints the JSON output to stdout (last JSON object).
    out = proc.stdout.strip()
    start = out.find("{")
    return json.loads(out[start:])


def preflight(model: str, runs: int, workers: int) -> bool:
    """Quick sanity check: do clear positives trigger at all in this environment?"""
    # pick a distinctive skill with strong positives
    skill = "neohaskell-code-review" if (EVAL_DIR / "neohaskell-code-review.json").exists() else all_skills()[0]
    eval_set = json.loads((EVAL_DIR / f"{skill}.json").read_text())
    positives = [e for e in eval_set if e["should_trigger"]][:3]
    tmp = EVAL_DIR / ".preflight.json"
    tmp.write_text(json.dumps(positives))
    cmd = [
        sys.executable, "-m", "scripts.run_eval",
        "--eval-set", str(tmp), "--skill-path", str(SKILLS_DIR / skill),
        "--model", model, "--runs-per-query", "2", "--num-workers", str(workers),
    ]
    proc = subprocess.run(cmd, cwd=str(SKILL_CREATOR), capture_output=True, text=True)
    tmp.unlink(missing_ok=True)
    try:
        res = json.loads(proc.stdout[proc.stdout.find("{"):])
        triggers = sum(r["triggers"] for r in res["results"])
        print(f"  pre-flight ({skill}): {triggers} triggers across {len(positives)} clear positives x2 runs")
        return triggers > 0
    except Exception:
        print(f"  pre-flight parse failed:\n{proc.stderr[-800:]}")
        return False


def read_frontmatter(md: Path):
    txt = md.read_text()
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", txt, re.DOTALL)
    if not m:
        raise ValueError(f"no frontmatter: {md}")
    return m.group(1), m.group(2)


def apply_description(skill: str, new_desc: str) -> None:
    """Rewrite the frontmatter `description` as a YAML folded block scalar, preserving other keys."""
    new_desc = " ".join(new_desc.split())  # normalize whitespace to one line
    if "<" in new_desc or ">" in new_desc:
        raise ValueError(f"{skill}: proposed description contains angle brackets; skipping")
    if len(new_desc) > 1024:
        raise ValueError(f"{skill}: proposed description too long ({len(new_desc)})")
    md = SKILLS_DIR / skill / "SKILL.md"
    fm, body = read_frontmatter(md)
    lines = fm.split("\n")
    # find the description key and the extent of its (possibly multi-line) value
    out, i = [], 0
    wrapped = "\n".join("  " + l for l in textwrap.wrap(new_desc, width=90))
    replaced = False
    while i < len(lines):
        line = lines[i]
        if line.startswith("description:"):
            out.append("description: >-")
            out.append(wrapped)
            i += 1
            # skip old continuation lines (indented) and old inline value
            while i < len(lines) and (lines[i].startswith("  ") or lines[i].startswith("\t")):
                i += 1
            replaced = True
            continue
        out.append(line)
        i += 1
    if not replaced:
        raise ValueError(f"{skill}: no description key found")
    md.write_text("---\n" + "\n".join(out) + "\n---\n" + body)


def validate(skill: str) -> str:
    fm, _ = read_frontmatter(SKILLS_DIR / skill / "SKILL.md")
    keys = set(re.findall(r"^([A-Za-z][\w-]*):", fm, re.MULTILINE))
    if keys - ALLOWED_FM:
        return f"unexpected keys {sorted(keys - ALLOWED_FM)}"
    dm = re.search(r"^description:\s*(.+)$", fm, re.MULTILINE)
    desc = dm.group(1).strip() if dm else ""
    if desc in (">", "|", ">-", "|-"):
        desc = " ".join(l.strip() for l in fm[dm.end():].splitlines() if l.startswith((" ", "\t")))
    if "<" in desc or ">" in desc:
        return "angle brackets in description"
    if len(desc) > 1024:
        return f"description too long ({len(desc)})"
    return "ok"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="opus",
                    help="model for eval + improve. Use your session model (opus). "
                         "NOTE: sonnet/haiku UNDER-TRIGGER skills, so they give a false 0-signal — use opus.")
    ap.add_argument("--max-iterations", type=int, default=3)
    ap.add_argument("--runs-per-query", type=int, default=3)
    ap.add_argument("--num-workers", type=int, default=8)
    ap.add_argument("--skills", nargs="*", default=None, help="subset of skill names (default: all)")
    ap.add_argument("--dry-run", action="store_true", help="print winners; do not write files")
    ap.add_argument("--skip-preflight", action="store_true")
    args = ap.parse_args()

    skills = args.skills or all_skills()
    print(f"Optimizing {len(skills)} skill description(s) with model={args.model}, "
          f"iters={args.max_iterations}, runs={args.runs_per_query}\n")

    if not args.skip_preflight:
        print("Pre-flight: checking the triggering harness fires in this environment...")
        if not preflight(args.model, args.runs_per_query, args.num_workers):
            print("\n  ABORT: 0 triggers on clear positives. The run_eval command-proxy is not\n"
                  "  firing here, so run_loop would produce an all-zero signal. Fix the harness\n"
                  "  (or run in an environment where it triggers) before optimizing. Use\n"
                  "  --skip-preflight to override.")
            sys.exit(2)
        print("  pre-flight OK.\n")

    summary = []
    for skill in skills:
        print(f"[{skill}] optimizing...")
        try:
            out = run_loop_for(skill, args.model, args.max_iterations, args.runs_per_query, args.num_workers)
        except Exception as e:
            print(f"  ERROR: {e}")
            summary.append((skill, "ERROR", ""))
            continue
        best = out["best_description"].strip()
        changed = best != out["original_description"].strip()
        print(f"  best score: {out.get('best_score')}  changed: {changed}")
        if changed and not args.dry_run:
            try:
                apply_description(skill, best)
                status = validate(skill)
                print(f"  applied. validation: {status}")
            except Exception as e:
                print(f"  APPLY SKIPPED: {e}")
                status = "apply-skipped"
        else:
            status = "dry-run" if args.dry_run else "unchanged"
        summary.append((skill, out.get("best_score"), status))

    print("\n=== summary ===")
    for skill, score, status in summary:
        print(f"  {skill:38s} score={score}  {status}")


if __name__ == "__main__":
    main()

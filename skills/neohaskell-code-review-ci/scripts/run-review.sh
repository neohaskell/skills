#!/usr/bin/env bash
set -euo pipefail
if [ "$#" -ne 4 ]; then
  echo 'usage: run-review.sh TRUSTED_WRAPPER PATCH CONTEXT OUTPUT_DIRECTORY' >&2
  exit 2
fi
review_wrapper=$1
review_patch=$2
review_context=$3
review_output=$4
review_scripts=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
case ${FAIL_ON_BLOCKERS:-false} in true|false) ;; *) echo 'FAIL_ON_BLOCKERS must be true or false' >&2; exit 2 ;; esac
mkdir -p -- "$review_output"
review_status=0
"$review_wrapper" "$review_patch" "$review_context" "$review_output/raw.json" > "$review_output/runner.stdout" 2> "$review_output/runner.stderr" || review_status=$?
parse_status=0
python3 "$review_scripts/parse_review.py" "$review_output/raw.json" --reviewer-exit-code "$review_status" > "$review_output/result.json" || parse_status=$?
if [ "$parse_status" -eq 1 ] && [ "${FAIL_ON_BLOCKERS:-false}" = false ]; then
  exit 0
fi
exit "$parse_status"

#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_DIR="${ROOT_DIR}/.tmp/harness-smoke"
OUT_DIR="${TMP_DIR}/offline"
FIXTURE="${ROOT_DIR}/.claude/skills/lease-eval/fixtures/golden_ol_a1/lease_state.json"

rm -rf "${TMP_DIR}"
mkdir -p "${OUT_DIR}"

pytest -q tests/test_eval.py
python -m leasegpt.cli run-from-json "${FIXTURE}" \
  --output-dir "${OUT_DIR}" \
  --property-type Retail \
  --audience AssetManagement

required=(
  extraction.json
  conformance_report.json
  lease_abstract.md
  lease_abstract.pdf
  critical_dates.ics
  calendar_manifest.json
  diff_report.md
  diff_manifest.json
  risk_register.md
  risk_manifest.json
)

for file in "${required[@]}"; do
  if [[ ! -f "${OUT_DIR}/${file}" ]]; then
    echo "missing expected artifact: ${file}" >&2
    exit 1
  fi
done

echo "Harness smoke passed; artifacts in ${OUT_DIR}"

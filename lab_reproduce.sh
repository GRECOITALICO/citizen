#!/usr/bin/env bash
# Birth Lab — Destroy → Birth → evidence of a new life
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="${ROOT}/runtime${PYTHONPATH:+:$PYTHONPATH}"
export CITIZEN_HOME="${CITIZEN_HOME:-${ROOT}/.citizen}"

echo "== INT-CITIZEN-BIRTH-LAB-001 reproduce =="

if [[ -d "${CITIZEN_HOME}" ]]; then
  echo "Destroying previous Citizen (export first)..."
  python3 -m citizen_seed destroy --home "${CITIZEN_HOME}"
fi

echo "Birth..."
python3 -m citizen_seed install --home "${CITIZEN_HOME}"
python3 -m citizen_seed boot --home "${CITIZEN_HOME}"
python3 -m citizen_seed update --home "${CITIZEN_HOME}" || true
python3 -m citizen_seed export-birth --home "${CITIZEN_HOME}"
python3 -m citizen_seed lab-report --home "${CITIZEN_HOME}"

echo ""
echo "Reproducibility cycle complete. Packages under lab/exports/"
ls -la "${ROOT}/lab/exports/" | tail -n 20

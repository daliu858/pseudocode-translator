#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

echo
echo " PRISM - local CAIE pseudocode IDE"
echo " Starting from: $(pwd)"
echo

pick_python() {
  local candidate
  for candidate in "${PYTHON:-}" python3 python; do
    if [[ -z "$candidate" ]]; then
      continue
    fi
    if ! command -v "$candidate" >/dev/null 2>&1 && [[ ! -x "$candidate" ]]; then
      continue
    fi
    if "$candidate" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1; then
      echo "$candidate"
      return 0
    fi
  done
  return 1
}

if ! PY="$(pick_python)"; then
  echo " Could not find Python 3.10 or newer."
  echo " Install Python 3, then run: ./start.sh"
  exit 1
fi

echo " Using: $PY"
echo " Browser should open at http://127.0.0.1:8765/"
echo " Press Ctrl+C to stop."
echo
exec "$PY" -m ide.server "$@"

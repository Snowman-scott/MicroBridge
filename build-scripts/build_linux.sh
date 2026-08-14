#!/usr/bin/env bash
# MicroBridge: Unified Test & Build (Linux)
set -euo pipefail

if [[ "$(uname -s)" != "Linux" ]]; then
    echo "ERROR: This script must be run on Linux. (PyInstaller cannot cross-compile)"
    exit 1
fi

if command -v python3 >/dev/null 2>&1; then PY=python3; else PY=python; fi
echo "============================================================"
echo " MicroBridge: Unified Test & Build (Linux)"
echo "============================================================"
echo

if [[ -n "${CI:-}" ]]; then
    echo "CI detected: skipping unit tests (they run in the test stage)."
    echo
else
    echo "[1/3] Running Unit Tests with Real Test Data..."
    export PYTHONPATH="$(pwd)/src${PYTHONPATH:+:$PYTHONPATH}"
    "$PY" -m pytest tests -v

    echo "SUCCESS: All tests passed."

    echo
fi

echo "[2/3] Cleaning previous build artifacts..."
rm -rf build dist
echo "Done."

echo
echo "[3/3] Building Unified MicroBridge Executable..."
echo "(Supports both GUI and CLI modes)"
echo

"$PY" -m PyInstaller \
    --name="MicroBridge" \
    --onedir \
    --windowed \
    --add-data="src/MicroBridge_Icon.ico:." \
    --distpath="dist" \
    --workpath="build" \
    --noconfirm \
    "src/MicroBridge/main.py"

echo
echo "Creating CLI shim next to the executable..."
cat > "dist/MicroBridge/microbridge" <<'EOF'
#!/usr/bin/env bash
exec "$(dirname "$0")/MicroBridge" "$@"
EOF
chmod +x "dist/MicroBridge/microbridge"

echo
echo "============================================================"
echo " DONE: Build successful!"
echo "============================================================"
echo "Location: dist/MicroBridge/MicroBridge"
echo
echo "Usage:"
echo "  - Run dist/MicroBridge/MicroBridge: Launches GUI"
echo "  - Terminal CLI: dist/MicroBridge/microbridge filename.ndpa"
echo "    (run from the repo root, or add dist/MicroBridge/ to your PATH)"
echo "============================================================"
if [[ -z "${CI:-}" ]]; then
    read -r -p "Press Enter to exit..."
fi

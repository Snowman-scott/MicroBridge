#!/usr/bin/env bash
# MicroBridge: Unified Test & Build (macOS)
set -euo pipefail

if [[ "$(uname -s)" != "Darwin" ]]; then
    echo "ERROR: This script must be run on macOS. (PyInstaller cannot cross-compile)"
    exit 1
fi

if command -v python3 >/dev/null 2>&1; then PY=python3; else PY=python; fi
echo "============================================================"
echo " MicroBridge: Unified Test & Build (macOS)"
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
echo "[3/3] Building Unified MicroBridge Application..."
echo "(Supports both GUI and CLI modes)"
echo

ICON_ARGS=()
ICNS="src/MicroBridge/resources/MicroBridge_Icon.icns"
ICO="src/MicroBridge/resources/MicroBridge_Icon.ico"
if [[ ! -f "$ICNS" ]] && command -v sips >/dev/null 2>&1 && command -v iconutil >/dev/null 2>&1; then
    echo "Converting $ICO to $ICNS..."
    workdir="$(mktemp -d)"
    iconset="$workdir/icon.iconset"
    mkdir -p "$iconset"
    # Only these slot names are valid to iconutil, and -s format png is
    # required or sips emits .ico data under a .png name. Source art is
    # 256x256, so 512@2x is omitted rather than upscaled.
    for pair in "16x16:16" "16x16@2x:32" "32x32:32" "32x32@2x:64" \
                "128x128:128" "128x128@2x:256" "256x256:256"; do
        name="${pair%%:*}"
        px="${pair##*:}"
        sips -s format png -z "$px" "$px" "$ICO" \
            --out "$iconset/icon_${name}.png" >/dev/null
    done
    iconutil -c icns "$iconset" -o "$ICNS"
    rm -rf "$workdir"
fi
if [[ -f "$ICNS" ]]; then
    ICON_ARGS+=(--icon "$ICNS")
fi

"$PY" -m PyInstaller \
    --name="MicroBridge" \
    --onedir \
    --windowed \
    "${ICON_ARGS[@]}" \
    --add-data="src/MicroBridge/resources/MicroBridge_Icon.ico:." \
    --distpath="dist" \
    --workpath="build" \
    --noconfirm \
    "src/MicroBridge/main.py"

echo
echo "Creating CLI shim next to the app..."
cat > "dist/microbridge" <<'EOF'
#!/usr/bin/env bash
exec "$(dirname "$0")/MicroBridge.app/Contents/MacOS/MicroBridge" "$@"
EOF
chmod +x "dist/microbridge"

echo
echo "============================================================"
echo " DONE: Build successful!"
echo "============================================================"
echo "Location: dist/MicroBridge.app"
echo
echo "Usage:"
echo "  - Double-click MicroBridge.app: Launches GUI"
echo "  - Terminal CLI: dist/microbridge filename.ndpa"
echo "    (run from the repo root, or add dist/ to your PATH)"
echo "============================================================"
if [[ -z "${CI:-}" ]]; then
    read -r -p "Press Enter to exit..."
fi

"""Installs a desktop launcher into the user's own directories.

Homebrew formulae cannot do this: brew overrides HOME during post_install and
sandboxes the process, so a formula gets EPERM writing anywhere near the real
home. Doing it from the CLI instead runs as the user, unsandboxed, and needs
no admin or sudo because everything lands under ~.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

APP_NAME = "MicroBridge"
BUNDLE_ID = "io.github.snowman-scott.microbridge"

# iconutil accepts only these slot names. The source art is 256x256, so the
# 512@2x slot is omitted rather than upscaled.
ICNS_SLOTS = {
    "16x16": 16,
    "16x16@2x": 32,
    "32x32": 32,
    "32x32@2x": 64,
    "128x128": 128,
    "128x128@2x": 256,
    "256x256": 256,
}

INFO_PLIST = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleName</key><string>{name}</string>
  <key>CFBundleDisplayName</key><string>{name}</string>
  <key>CFBundleExecutable</key><string>{name}</string>
  <key>CFBundleIdentifier</key><string>{bundle_id}</string>
  <key>CFBundleIconFile</key><string>{name}</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>NSHighResolutionCapable</key><true/>
</dict>
</plist>
"""

DESKTOP_ENTRY = """[Desktop Entry]
Type=Application
Name={name}
Comment=NDP/CSV to LMD Converter
Exec={exec_path}
Icon={icon}
Terminal=false
Categories=Science;Utility;
"""


def packaged_icon() -> Path | None:
    """The .ico shipped inside the installed package, if present."""
    icon = Path(__file__).parent / "resources" / "MicroBridge_Icon.ico"
    return icon if icon.is_file() else None


def launcher_target() -> str:
    """The command the launcher should run.

    Prefers the installed `microbridge` console script, since that is stable
    across upgrades. Falls back to re-running this interpreter with -m.
    """
    script = shutil.which("microbridge")
    if script:
        return script
    return f"{sys.executable} -m MicroBridge.main"


def _build_icns(ico: Path, dest: Path) -> bool:
    """Convert .ico to .icns via sips + iconutil. Returns True on success."""
    if not (shutil.which("sips") and shutil.which("iconutil")):
        return False

    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        iconset = Path(tmp) / f"{APP_NAME}.iconset"
        iconset.mkdir()
        for slot, px in ICNS_SLOTS.items():
            # -s format png is required: sips otherwise keeps the .ico format
            # regardless of the output suffix and iconutil rejects it.
            result = subprocess.run(
                ["sips", "-s", "format", "png", "-z", str(px), str(px),
                 str(ico), "--out", str(iconset / f"icon_{slot}.png")],
                capture_output=True,
            )
            if result.returncode != 0:
                return False
        dest.parent.mkdir(parents=True, exist_ok=True)
        return subprocess.run(
            ["iconutil", "-c", "icns", str(iconset), "-o", str(dest)],
            capture_output=True,
        ).returncode == 0


def _install_macos() -> Path:
    # ~/Applications, not /Applications: the latter is root:admin, so a user
    # without admin rights cannot write to it. Launchpad indexes both.
    app = Path.home() / "Applications" / f"{APP_NAME}.app"
    if app.exists():
        shutil.rmtree(app)
    (app / "Contents" / "MacOS").mkdir(parents=True)
    (app / "Contents" / "Resources").mkdir(parents=True)

    stub = app / "Contents" / "MacOS" / APP_NAME
    # No arguments, which is the branch main.py routes to the GUI.
    stub.write_text(f'#!/bin/sh\nexec {launcher_target()}\n')
    stub.chmod(0o755)

    (app / "Contents" / "Info.plist").write_text(
        INFO_PLIST.format(name=APP_NAME, bundle_id=BUNDLE_ID)
    )

    ico = packaged_icon()
    if ico:
        _build_icns(ico, app / "Contents" / "Resources" / f"{APP_NAME}.icns")

    # Spotlight does not index symlinked bundles, which is why this is a real
    # directory; nudge it to pick the new one up so Launchpad shows it.
    if shutil.which("mdimport"):
        subprocess.run(["mdimport", str(app)], capture_output=True)
    return app


def _install_linux() -> Path:
    data = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))

    icon_value = APP_NAME.lower()
    ico = packaged_icon()
    if ico:
        icon_dir = data / "icons"
        icon_dir.mkdir(parents=True, exist_ok=True)
        icon_path = icon_dir / f"{icon_value}.ico"
        shutil.copyfile(ico, icon_path)
        icon_value = str(icon_path)

    apps = data / "applications"
    apps.mkdir(parents=True, exist_ok=True)
    entry = apps / "microbridge.desktop"
    entry.write_text(
        DESKTOP_ENTRY.format(
            name=APP_NAME, exec_path=launcher_target(), icon=icon_value
        )
    )
    entry.chmod(0o755)

    if shutil.which("update-desktop-database"):
        subprocess.run(["update-desktop-database", str(apps)], capture_output=True)
    return entry


def install_launcher() -> Path:
    """Install the launcher for the current platform.

    Returns the path created. Raises NotImplementedError on unsupported
    platforms.
    """
    if sys.platform == "darwin":
        return _install_macos()
    if sys.platform.startswith("linux"):
        return _install_linux()
    raise NotImplementedError(
        f"--install-launcher is not supported on {sys.platform}"
    )

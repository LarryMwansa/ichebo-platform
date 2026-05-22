#!/usr/bin/env bash
# build_macos.sh — Build Ichebo Desktop as a macOS .dmg.
#
# Requirements:
#   - Flutter SDK on PATH (macOS host only)
#   - Go 1.21+ on PATH
#   - Xcode command line tools (codesign, hdiutil, create-dmg optional)
#   - Apple Developer certificate in Keychain for notarisation
#
# Usage:
#   cd ichebo-desktop
#   bash scripts/build_macos.sh [--skip-go]
#
# Output: dist/IcheboDesktop.dmg

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$SCRIPT_DIR/.."
DIST="$ROOT/dist"

echo "==> Ichebo Desktop — macOS .dmg build"

# ── 1. Rebuild sync engine dylib ──────────────────────────────────────────────
if [[ "${1:-}" != "--skip-go" ]]; then
  echo "--> Building libichebo_sync.dylib"
  pushd "$ROOT/../ichebo-sync" > /dev/null
  go build -buildmode=c-shared \
    -o "$ROOT/macos/Runner/libichebo_sync.dylib" \
    ./ffi/
  popd > /dev/null
fi

# ── 2. Flutter release build ──────────────────────────────────────────────────
echo "--> flutter build macos --release"
pushd "$ROOT" > /dev/null
flutter build macos --release
popd > /dev/null

APP="$ROOT/build/macos/Build/Products/Release/ichebo_desktop.app"
mkdir -p "$DIST"

# ── 3. Optional: codesign (requires Developer ID cert in Keychain) ────────────
if command -v codesign &>/dev/null && security find-identity -v -p codesigning | grep -q "Developer ID"; then
  echo "--> Codesigning .app"
  codesign --deep --force --verify --verbose \
    --sign "Developer ID Application" "$APP"
fi

# ── 4. Package as .dmg ────────────────────────────────────────────────────────
echo "--> Creating .dmg"
DMG="$DIST/IcheboDesktop.dmg"

if command -v create-dmg &>/dev/null; then
  create-dmg \
    --volname "Ichebo Desktop" \
    --window-size 600 400 \
    --icon-size 128 \
    --app-drop-link 450 175 \
    "$DMG" "$APP"
else
  # Fallback: plain hdiutil
  hdiutil create -volname "Ichebo Desktop" -srcfolder "$APP" \
    -ov -format UDZO "$DMG"
fi

echo ""
echo "==> Done: $DMG"
echo "    $(du -sh "$DMG" | cut -f1)"

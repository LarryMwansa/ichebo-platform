#!/usr/bin/env bash
# build_linux.sh — Build Ichebo Desktop as a self-contained Linux AppImage.
#
# Requirements:
#   - Flutter SDK on PATH
#   - appimagetool on PATH (https://appimage.github.io/appimagetool/)
#   - Go 1.21+ on PATH (for rebuilding libichebo_sync.so)
#
# Usage:
#   cd ichebo-desktop
#   bash scripts/build_linux.sh [--skip-go]
#
# Output: dist/IcheboDesktop-x86_64.AppImage

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$SCRIPT_DIR/.."
DIST="$ROOT/dist"
APPDIR="$DIST/IcheboDesktop.AppDir"

echo "==> Ichebo Desktop — Linux AppImage build"

# ── 1. Rebuild Go sync engine ─────────────────────────────────────────────────
if [[ "${1:-}" != "--skip-go" ]]; then
  echo "--> Building libichebo_sync.so"
  pushd "$ROOT/../ichebo-sync" > /dev/null
  go build -buildmode=c-shared \
    -o "$ROOT/linux/bundle/lib/libichebo_sync.so" \
    ./ffi/
  popd > /dev/null
  echo "    Done: $(du -sh "$ROOT/linux/bundle/lib/libichebo_sync.so" | cut -f1)"
fi

# ── 2. Flutter release build ──────────────────────────────────────────────────
echo "--> flutter build linux --release"
pushd "$ROOT" > /dev/null
flutter build linux --release
popd > /dev/null

BUNDLE="$ROOT/build/linux/x64/release/bundle"

# ── 3. Assemble AppDir ────────────────────────────────────────────────────────
echo "--> Assembling AppDir"
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin" "$APPDIR/usr/lib" "$APPDIR/usr/share/applications" "$DIST"

# Binary and data
cp -r "$BUNDLE/"* "$APPDIR/usr/bin/"

# Sync engine .so (already embedded in bundle/lib but copy explicitly for clarity)
cp "$ROOT/linux/bundle/lib/libichebo_sync.so" "$APPDIR/usr/lib/"

# Desktop entry
cat > "$APPDIR/ichebo_desktop.desktop" << 'EOF'
[Desktop Entry]
Type=Application
Name=Ichebo Desktop
Exec=ichebo_desktop
Icon=ichebo
Categories=Office;
Comment=Ichebo Community Operating System
EOF
cp "$APPDIR/ichebo_desktop.desktop" "$APPDIR/usr/share/applications/"

# Icon — use placeholder if not present
ICON_SRC="$ROOT/assets/images/ichebo_icon.png"
if [[ -f "$ICON_SRC" ]]; then
  cp "$ICON_SRC" "$APPDIR/ichebo.png"
else
  # Create a minimal 64×64 red PNG as stand-in using python3
  python3 - << 'PYEOF'
import struct, zlib
def png_chunk(name, data):
    c = zlib.crc32(name + data) & 0xFFFFFFFF
    return struct.pack('>I', len(data)) + name + data + struct.pack('>I', c)
w = h = 64
raw = b''.join(b'\x00' + bytes([0xAF, 0x32, 0x36, 0xFF] * w) for _ in range(h))
compressed = zlib.compress(raw)
data = (b'\x89PNG\r\n\x1a\n'
        + png_chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
        + png_chunk(b'IDAT', compressed)
        + png_chunk(b'IEND', b''))
with open('/tmp/ichebo_icon.png', 'wb') as f:
    f.write(data)
PYEOF
  cp /tmp/ichebo_icon.png "$APPDIR/ichebo.png"
fi

# AppRun entry point
cat > "$APPDIR/AppRun" << 'EOF'
#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")"
export LD_LIBRARY_PATH="$HERE/usr/lib:$HERE/usr/bin/lib:${LD_LIBRARY_PATH:-}"
exec "$HERE/usr/bin/ichebo_desktop" "$@"
EOF
chmod +x "$APPDIR/AppRun"

# ── 4. Package as AppImage ────────────────────────────────────────────────────
echo "--> Packaging AppImage"
ARCH=x86_64 appimagetool "$APPDIR" "$DIST/IcheboDesktop-x86_64.AppImage"

echo ""
echo "==> Done: $DIST/IcheboDesktop-x86_64.AppImage"
echo "    $(du -sh "$DIST/IcheboDesktop-x86_64.AppImage" | cut -f1)"

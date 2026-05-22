#!/usr/bin/env bash
# build_android_so.sh — Compile libichebo_sync.so for Android via gomobile.
#
# Requirements:
#   - Go 1.21+ on PATH
#   - gomobile installed: go install golang.org/x/mobile/cmd/gomobile@latest
#   - Android NDK configured (gomobile init handles this)
#   - ANDROID_HOME set to your Android SDK root
#
# Usage:
#   cd ichebo-mobile
#   bash scripts/build_android_so.sh
#
# Output: android/app/src/main/jniLibs/{abi}/libichebo_sync.so

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$SCRIPT_DIR/.."
SYNC_DIR="$ROOT/../ichebo-sync"
JNILIBS="$ROOT/android/app/src/main/jniLibs"

echo "==> Ichebo Mobile — Android .so build (gomobile)"

# ── 1. Ensure gomobile is initialised ────────────────────────────────────────
if ! command -v gomobile &>/dev/null; then
  echo "--> Installing gomobile"
  go install golang.org/x/mobile/cmd/gomobile@latest
  gomobile init
fi

# ── 2. Build .so for all Android ABIs ────────────────────────────────────────
echo "--> gomobile bind -target android"
pushd "$SYNC_DIR" > /dev/null

# gomobile bind produces a .aar — we extract the .so files from it.
STAGING="$(mktemp -d)"
gomobile bind \
  -target android \
  -o "$STAGING/ichebo_sync.aar" \
  -ldflags "-s -w" \
  ./ffi/

popd > /dev/null

# ── 3. Extract .so per ABI into jniLibs ──────────────────────────────────────
echo "--> Extracting .so files from .aar"
ABIS=(arm64-v8a armeabi-v7a x86_64)
for ABI in "${ABIS[@]}"; do
  DEST="$JNILIBS/$ABI"
  mkdir -p "$DEST"
  # .aar is a ZIP; jni/<abi>/libichebo_sync.so lives inside it.
  unzip -o "$STAGING/ichebo_sync.aar" "jni/$ABI/libichebo_sync.so" -d "$STAGING/extract" 2>/dev/null || true
  if [[ -f "$STAGING/extract/jni/$ABI/libichebo_sync.so" ]]; then
    cp "$STAGING/extract/jni/$ABI/libichebo_sync.so" "$DEST/libichebo_sync.so"
    echo "    $ABI: $(du -sh "$DEST/libichebo_sync.so" | cut -f1)"
  else
    echo "    $ABI: not produced by gomobile (skipped)"
  fi
done

rm -rf "$STAGING"

echo ""
echo "==> Done. .so files in $JNILIBS"
echo "    Run: flutter build apk --release"

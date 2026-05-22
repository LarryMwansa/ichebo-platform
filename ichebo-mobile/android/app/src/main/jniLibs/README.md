# jniLibs

This directory holds the compiled Go sync engine shared libraries.

**These files are NOT committed to git.** They are build artefacts.

To populate them, run from `ichebo-mobile/`:

```
bash scripts/build_android_so.sh
```

This requires:
- Go 1.21+
- gomobile (`go install golang.org/x/mobile/cmd/gomobile@latest`)
- Android NDK (via Android Studio or `sdkmanager`)
- `ichebo-sync/` checked out at the same level as `ichebo-mobile/`

Expected output structure:

```
jniLibs/
  arm64-v8a/libichebo_sync.so    ← 64-bit ARM (most modern Android devices)
  armeabi-v7a/libichebo_sync.so  ← 32-bit ARM (older devices)
  x86_64/libichebo_sync.so       ← Emulator / x86 devices
```

**Before Layer 5 (ichebo-sync) is complete:** the app runs without the .so.
`SyncEngine.isLoaded` returns false. All screens read from SQLite normally;
writes are queued locally and synced when the engine is loaded on next launch.

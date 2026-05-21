import 'dart:convert';
import 'dart:ffi';
import 'dart:io';
import 'package:ffi/ffi.dart';

// ── Native function typedefs ──────────────────────────────────────────────────

typedef _SyncStartNative = Int32 Function(Pointer<Utf8> configJson);
typedef _SyncStartDart = int Function(Pointer<Utf8> configJson);

typedef _SyncStopNative = Void Function();
typedef _SyncStopDart = void Function();

typedef _SyncNowNative = Void Function();
typedef _SyncNowDart = void Function();

typedef _SyncStatusNative = Pointer<Utf8> Function();
typedef _SyncStatusDart = Pointer<Utf8> Function();

typedef _SyncConflictCountNative = Int32 Function();
typedef _SyncConflictCountDart = int Function();

typedef _SyncResolveConflictNative = Int32 Function(
    Pointer<Utf8> conflictId, Int32 choice);
typedef _SyncResolveConflictDart = int Function(
    Pointer<Utf8> conflictId, int choice);

// ── SyncConfig ────────────────────────────────────────────────────────────────

class SyncConfig {
  const SyncConfig({
    required this.baseUrl,
    required this.authToken,
    required this.deviceId,
    required this.tenantId,
    required this.dbPath,
  });

  final String baseUrl;
  final String authToken;
  final String deviceId;
  final String tenantId;
  final String dbPath;

  Map<String, dynamic> toJson() => {
        'base_url': baseUrl,
        'auth_token': authToken,
        'device_id': deviceId,
        'tenant_id': tenantId,
        'db_path': dbPath,
      };
}

// ── SyncStatusModel ───────────────────────────────────────────────────────────

enum SyncState { synced, offline, syncing, conflict, blocked }

class SyncStatusModel {
  const SyncStatusModel({
    this.state = SyncState.offline,
    this.pendingCount = 0,
    this.conflictCount = 0,
    this.message = '',
    this.lastSyncedAt,
  });

  final SyncState state;
  final int pendingCount;
  final int conflictCount;
  final String message;
  final DateTime? lastSyncedAt;

  factory SyncStatusModel.fromJson(Map<String, dynamic> json) {
    final stateStr = json['state'] as String? ?? 'offline';
    final state = switch (stateStr) {
      'synced' => SyncState.synced,
      'syncing' => SyncState.syncing,
      'conflict' => SyncState.conflict,
      'blocked' => SyncState.blocked,
      _ => SyncState.offline,
    };
    return SyncStatusModel(
      state: state,
      pendingCount: (json['pending'] as int?) ?? 0,
      conflictCount: (json['conflict_count'] as int?) ?? 0,
      message: (json['message'] as String?) ?? '',
    );
  }

  static const offline = SyncStatusModel();
}

// ── SyncEngine ────────────────────────────────────────────────────────────────

class SyncEngine {
  SyncEngine._();

  static SyncEngine? _instance;
  static SyncEngine get instance => _instance ??= SyncEngine._();

  DynamicLibrary? _lib;
  _SyncStartDart? _syncStart;
  _SyncStopDart? _syncStop;
  _SyncNowDart? _syncNow;
  _SyncStatusDart? _syncStatus;
  _SyncConflictCountDart? _syncConflictCount;
  _SyncResolveConflictDart? _syncResolveConflict;

  bool get isLoaded => _lib != null;

  // Loads the shared library. Returns true on success.
  // On Linux the .so lives next to the Flutter bundle.
  bool load() {
    if (_lib != null) return true;
    try {
      final libPath = _resolveLibPath();
      _lib = DynamicLibrary.open(libPath);
      _syncStart = _lib!
          .lookup<NativeFunction<_SyncStartNative>>('SyncStart')
          .asFunction();
      _syncStop = _lib!
          .lookup<NativeFunction<_SyncStopNative>>('SyncStop')
          .asFunction();
      _syncNow = _lib!
          .lookup<NativeFunction<_SyncNowNative>>('SyncNow')
          .asFunction();
      _syncStatus = _lib!
          .lookup<NativeFunction<_SyncStatusNative>>('SyncStatus')
          .asFunction();
      _syncConflictCount = _lib!
          .lookup<NativeFunction<_SyncConflictCountNative>>('SyncConflictCount')
          .asFunction();
      _syncResolveConflict = _lib!
          .lookup<NativeFunction<_SyncResolveConflictNative>>(
              'SyncResolveConflict')
          .asFunction();
      return true;
    } catch (e) {
      // Library not available — app runs in offline-only mode.
      return false;
    }
  }

  String _resolveLibPath() {
    if (Platform.isLinux) return 'lib/libichebo_sync.so';
    if (Platform.isMacOS) return 'libichebo_sync.dylib';
    if (Platform.isWindows) return 'ichebo_sync.dll';
    throw UnsupportedError('Unsupported platform: ${Platform.operatingSystem}');
  }

  // Starts the sync daemon. Call once on app init after DB is ready.
  // Returns 0 on success.
  int start(SyncConfig config) {
    if (_syncStart == null) return -99;
    final json = jsonEncode(config.toJson());
    final ptr = json.toNativeUtf8();
    try {
      return _syncStart!(ptr);
    } finally {
      malloc.free(ptr);
    }
  }

  // Gracefully shuts down the sync daemon. Call on app termination.
  void stop() => _syncStop?.call();

  // Triggers an immediate sync cycle in the background.
  void syncNow() => _syncNow?.call();

  // Returns the current sync status. Safe to call from any isolate.
  SyncStatusModel getStatus() {
    if (_syncStatus == null) return SyncStatusModel.offline;
    final ptr = _syncStatus!();
    try {
      final json = ptr.toDartString();
      final decoded = jsonDecode(json) as Map<String, dynamic>;
      return SyncStatusModel.fromJson(decoded);
    } catch (_) {
      return SyncStatusModel.offline;
    }
    // Note: SyncStatus returns a C.CString owned by Go's C heap.
    // Go's CGo runtime manages this memory; we must NOT call malloc.free on it.
  }

  int conflictCount() => _syncConflictCount?.call() ?? 0;

  // Resolves a conflict. keepLocal=true keeps the local version.
  int resolveConflict(String conflictId, {required bool keepLocal}) {
    if (_syncResolveConflict == null) return -99;
    final ptr = conflictId.toNativeUtf8();
    try {
      return _syncResolveConflict!(ptr, keepLocal ? 0 : 1);
    } finally {
      malloc.free(ptr);
    }
  }
}

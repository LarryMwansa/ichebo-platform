import 'dart:convert';
import 'package:ffi/ffi.dart';
import '../core/ffi/sync_bridge.dart';

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
    'base_url':   baseUrl,
    'auth_token': authToken,
    'device_id':  deviceId,
    'tenant_id':  tenantId,
    'db_path':    dbPath,
  };
}

// ── SyncStatusModel ───────────────────────────────────────────────────────────

enum SyncState { synced, offline, syncing, conflict, blocked }

class SyncStatusModel {
  const SyncStatusModel({
    this.state        = SyncState.offline,
    this.pendingCount  = 0,
    this.conflictCount = 0,
    this.message       = '',
    this.lastSyncedAt,
  });

  final SyncState  state;
  final int        pendingCount;
  final int        conflictCount;
  final String     message;
  final DateTime?  lastSyncedAt;

  factory SyncStatusModel.fromJson(Map<String, dynamic> json) {
    final stateStr = json['state'] as String? ?? 'offline';
    final state = switch (stateStr) {
      'synced'   => SyncState.synced,
      'syncing'  => SyncState.syncing,
      'conflict' => SyncState.conflict,
      'blocked'  => SyncState.blocked,
      _          => SyncState.offline,
    };
    return SyncStatusModel(
      state:         state,
      pendingCount:  (json['pending']        as int?) ?? 0,
      conflictCount: (json['conflict_count'] as int?) ?? 0,
      message:       (json['message']        as String?) ?? '',
    );
  }

  static const offline = SyncStatusModel();
}

// ── SyncEngine ────────────────────────────────────────────────────────────────

class SyncEngine {
  SyncEngine._();

  static SyncEngine? _instance;
  static SyncEngine get instance => _instance ??= SyncEngine._();

  SyncBridge? _bridge;

  bool get isLoaded => _bridge != null;

  // Attempts to load libichebo_sync.so from jniLibs. Safe to call at startup;
  // returns false if the .so is not yet bundled (pre-Layer-5 builds).
  bool load() {
    if (_bridge != null) return true;
    _bridge = SyncBridge.tryLoad();
    return _bridge != null;
  }

  // Starts the sync daemon. Returns 0 on success, negative on error,
  // -99 if the engine library is not loaded.
  int start(SyncConfig config) {
    final b = _bridge;
    if (b == null) return -99;
    final json = jsonEncode(config.toJson());
    final ptr  = json.toNativeUtf8();
    try {
      return b.syncStart(ptr);
    } finally {
      malloc.free(ptr);
    }
  }

  void stop() => _bridge?.syncStop();

  void syncNow() => _bridge?.syncNow();

  SyncStatusModel getStatus() {
    final b = _bridge;
    if (b == null) return SyncStatusModel.offline;
    final ptr = b.syncStatus();
    try {
      final decoded = jsonDecode(ptr.toDartString()) as Map<String, dynamic>;
      return SyncStatusModel.fromJson(decoded);
    } catch (_) {
      return SyncStatusModel.offline;
    }
    // Go owns the C string memory — do not free ptr.
  }

  int conflictCount() => _bridge?.syncConflictCount() ?? 0;

  int resolveConflict(String conflictId, {required bool keepLocal}) {
    final b = _bridge;
    if (b == null) return -99;
    final ptr = conflictId.toNativeUtf8();
    try {
      return b.syncResolveConflict(ptr, keepLocal ? 0 : 1);
    } finally {
      malloc.free(ptr);
    }
  }

  // Write helpers — all return 0 on success, negative on error, -99 if unloaded.
  int memberCreate(String jsonPayload)   => _write(_bridge?.memberCreate,   jsonPayload);
  int memberUpdate(String jsonPayload)   => _write(_bridge?.memberUpdate,   jsonPayload);
  int activityCreate(String jsonPayload) => _write(_bridge?.activityCreate, jsonPayload);
  int gatheringCreate(String jsonPayload)=> _write(_bridge?.gatheringCreate,jsonPayload);
  int attendanceSave(String jsonPayload) => _write(_bridge?.attendanceSave, jsonPayload);

  int _write(WriteDart? fn, String payload) {
    if (fn == null) return -99;
    final ptr = payload.toNativeUtf8();
    try {
      return fn(ptr);
    } finally {
      malloc.free(ptr);
    }
  }
}

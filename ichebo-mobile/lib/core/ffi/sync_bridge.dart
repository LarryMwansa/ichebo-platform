import 'dart:ffi';
import 'package:ffi/ffi.dart';

// ── Native function typedefs ──────────────────────────────────────────────────

typedef SyncStartNative  = Int32 Function(Pointer<Utf8> configJson);
typedef SyncStartDart    = int   Function(Pointer<Utf8> configJson);

typedef SyncStopNative   = Void Function();
typedef SyncStopDart     = void Function();

typedef SyncNowNative    = Void Function();
typedef SyncNowDart      = void Function();

typedef SyncStatusNative = Pointer<Utf8> Function();
typedef SyncStatusDart   = Pointer<Utf8> Function();

typedef SyncConflictCountNative = Int32 Function();
typedef SyncConflictCountDart   = int   Function();

typedef SyncResolveConflictNative = Int32 Function(
    Pointer<Utf8> conflictId, Int32 choice);
typedef SyncResolveConflictDart   = int Function(
    Pointer<Utf8> conflictId, int   choice);

typedef WriteNative = Int32 Function(Pointer<Utf8> jsonPtr);
typedef WriteDart   = int   Function(Pointer<Utf8> jsonPtr);

// ── Bridge — wraps DynamicLibrary lookup ─────────────────────────────────────

class SyncBridge {
  SyncBridge._(this._lib);

  final DynamicLibrary _lib;

  late final SyncStartDart            syncStart            = _lib.lookupFunction<SyncStartNative,            SyncStartDart>           ('SyncStart');
  late final SyncStopDart             syncStop             = _lib.lookupFunction<SyncStopNative,             SyncStopDart>            ('SyncStop');
  late final SyncNowDart              syncNow              = _lib.lookupFunction<SyncNowNative,              SyncNowDart>             ('SyncNow');
  late final SyncStatusDart           syncStatus           = _lib.lookupFunction<SyncStatusNative,           SyncStatusDart>          ('SyncStatus');
  late final SyncConflictCountDart    syncConflictCount    = _lib.lookupFunction<SyncConflictCountNative,    SyncConflictCountDart>   ('SyncConflictCount');
  late final SyncResolveConflictDart  syncResolveConflict  = _lib.lookupFunction<SyncResolveConflictNative,  SyncResolveConflictDart> ('SyncResolveConflict');
  late final WriteDart                memberCreate         = _lib.lookupFunction<WriteNative, WriteDart>('MemberCreate');
  late final WriteDart                memberUpdate         = _lib.lookupFunction<WriteNative, WriteDart>('MemberUpdate');
  late final WriteDart                activityCreate       = _lib.lookupFunction<WriteNative, WriteDart>('ActivityCreate');
  late final WriteDart                gatheringCreate      = _lib.lookupFunction<WriteNative, WriteDart>('GatheringCreate');
  late final WriteDart                attendanceSave       = _lib.lookupFunction<WriteNative, WriteDart>('AttendanceSave');

  // Tries to open the .so from the Android jniLibs location.
  // Returns null if the library is not present (pre-Layer-5 builds).
  static SyncBridge? tryLoad() {
    try {
      final lib = DynamicLibrary.open('libichebo_sync.so');
      return SyncBridge._(lib);
    } catch (_) {
      return null;
    }
  }
}

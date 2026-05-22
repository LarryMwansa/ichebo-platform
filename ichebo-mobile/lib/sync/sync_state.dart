import 'dart:async';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'sync_engine.dart';

// Polls SyncStatus() every 5 seconds while the engine is loaded.
// Stays in offline state silently when the .so is not present.

class SyncStateNotifier extends StateNotifier<SyncStatusModel> {
  SyncStateNotifier() : super(SyncStatusModel.offline) {
    _start();
  }

  Timer? _timer;

  void _start() {
    _poll();
    _timer = Timer.periodic(const Duration(seconds: 5), (_) => _poll());
  }

  void _poll() {
    if (!SyncEngine.instance.isLoaded) return;
    try {
      state = SyncEngine.instance.getStatus();
    } catch (_) {
      // Engine started but not yet ready — stay in current state.
    }
  }

  void triggerSync() {
    SyncEngine.instance.syncNow();
    state = SyncStatusModel(
      state:         SyncState.syncing,
      pendingCount:  state.pendingCount,
      conflictCount: state.conflictCount,
    );
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }
}

final syncStateProvider =
    StateNotifierProvider<SyncStateNotifier, SyncStatusModel>(
  (_) => SyncStateNotifier(),
);

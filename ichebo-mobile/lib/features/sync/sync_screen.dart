import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../../core/theme/tokens.dart';
import '../../sync/sync_engine.dart';
import '../../sync/sync_state.dart';

class SyncScreen extends ConsumerWidget {
  const SyncScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final status = ref.watch(syncStateProvider);

    return Scaffold(
      backgroundColor: IcsColors.inkBg,
      appBar: AppBar(
        backgroundColor: IcsColors.stone1,
        title: const Text('Sync'),
      ),
      body: ListView(
        padding: const EdgeInsets.all(IcsSpacing.m),
        children: [
          _StatusCard(status: status),
          const SizedBox(height: IcsSpacing.m),
          _SyncButton(status: status, ref: ref),
          const SizedBox(height: IcsSpacing.m),
          _EngineInfoCard(status: status),
          if (status.conflictCount > 0) ...[
            const SizedBox(height: IcsSpacing.m),
            _ConflictCard(count: status.conflictCount),
          ],
          const SizedBox(height: IcsSpacing.xl),
        ],
      ),
    );
  }
}

// ── Status card ───────────────────────────────────────────────────────────────

class _StatusCard extends StatelessWidget {
  const _StatusCard({required this.status});
  final SyncStatusModel status;

  @override
  Widget build(BuildContext context) {
    final (color, icon, label) = _stateProps(status.state);

    return Container(
      padding: const EdgeInsets.all(IcsSpacing.m),
      decoration: BoxDecoration(
        color: IcsColors.stone1,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withAlpha(77)),
      ),
      child: Row(
        children: [
          Container(
            width: 48,
            height: 48,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: color.withAlpha(26),
            ),
            child: Icon(icon, color: color, size: 24),
          ),
          const SizedBox(width: IcsSpacing.m),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  label,
                  style: TextStyle(
                      color: color,
                      fontSize: 16,
                      fontWeight: FontWeight.w600),
                ),
                if (status.message.isNotEmpty)
                  Text(
                    status.message,
                    style: const TextStyle(
                        color: IcsColors.textMuted, fontSize: 12),
                  ),
                if (status.lastSyncedAt != null)
                  Text(
                    'Last synced ${_fmtRelative(status.lastSyncedAt!)}',
                    style: const TextStyle(
                        color: IcsColors.textMuted, fontSize: 12),
                  ),
              ],
            ),
          ),
          if (status.state == SyncState.syncing)
            const SizedBox(
              width: 20,
              height: 20,
              child: CircularProgressIndicator(strokeWidth: 2),
            ),
        ],
      ),
    );
  }

  static (Color, IconData, String) _stateProps(SyncState s) => switch (s) {
    SyncState.synced   => (IcsColors.accentGreen,  Icons.cloud_done_outlined,   'Synced'),
    SyncState.syncing  => (IcsColors.accentBlue,   Icons.sync,                  'Syncing…'),
    SyncState.conflict => (IcsColors.accentAmber,  Icons.warning_amber_outlined, 'Conflicts'),
    SyncState.blocked  => (IcsColors.accentRed,    Icons.block_outlined,        'Blocked'),
    SyncState.offline  => (IcsColors.textMuted,    Icons.cloud_off_outlined,    'Offline'),
  };
}

// ── Sync button ───────────────────────────────────────────────────────────────

class _SyncButton extends StatelessWidget {
  const _SyncButton({required this.status, required this.ref});
  final SyncStatusModel status;
  final WidgetRef       ref;

  @override
  Widget build(BuildContext context) {
    final engineLoaded = SyncEngine.instance.isLoaded;
    final isSyncing    = status.state == SyncState.syncing;

    return SizedBox(
      width: double.infinity,
      child: FilledButton.icon(
        icon: const Icon(Icons.sync, size: 18),
        label: Text(
          engineLoaded
              ? (isSyncing ? 'Syncing…' : 'Sync Now')
              : 'Engine not loaded',
        ),
        onPressed: engineLoaded && !isSyncing
            ? () => ref.read(syncStateProvider.notifier).triggerSync()
            : null,
        style: FilledButton.styleFrom(
          backgroundColor: IcsColors.accentBlue,
        ),
      ),
    );
  }
}

// ── Engine info card ──────────────────────────────────────────────────────────

class _EngineInfoCard extends StatelessWidget {
  const _EngineInfoCard({required this.status});
  final SyncStatusModel status;

  @override
  Widget build(BuildContext context) {
    final loaded = SyncEngine.instance.isLoaded;
    final rows   = [
      ('Engine',   loaded ? 'Loaded' : 'Not loaded (pre-Layer 5)'),
      ('Pending',  '${status.pendingCount} changes'),
      ('Conflicts','${status.conflictCount}'),
    ];

    return Container(
      decoration: BoxDecoration(
        color: IcsColors.stone1,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: IcsColors.borderDark),
      ),
      child: Column(
        children: rows.indexed.map((entry) {
          final (i, row) = entry;
          final (label, value) = row;
          return Column(
            children: [
              if (i > 0)
                const Divider(height: 1, color: IcsColors.borderDark),
              Padding(
                padding: const EdgeInsets.symmetric(
                    horizontal: IcsSpacing.m, vertical: IcsSpacing.s + 2),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(label,
                        style: const TextStyle(
                            color: IcsColors.textMuted, fontSize: 13)),
                    Text(value,
                        style: TextStyle(
                            color: loaded ? Colors.white : IcsColors.textMuted,
                            fontSize: 13)),
                  ],
                ),
              ),
            ],
          );
        }).toList(),
      ),
    );
  }
}

// ── Conflict card ─────────────────────────────────────────────────────────────

class _ConflictCard extends StatelessWidget {
  const _ConflictCard({required this.count});
  final int count;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(IcsSpacing.m),
      decoration: BoxDecoration(
        color: IcsColors.stone1,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: IcsColors.accentAmber.withAlpha(77)),
      ),
      child: Row(
        children: [
          const Icon(Icons.warning_amber_outlined,
              color: IcsColors.accentAmber, size: 20),
          const SizedBox(width: IcsSpacing.s),
          Expanded(
            child: Text(
              '$count conflict${count == 1 ? '' : 's'} need resolution. '
              'Conflicts can be resolved from the desktop app.',
              style: const TextStyle(
                  color: IcsColors.accentAmber, fontSize: 13),
            ),
          ),
        ],
      ),
    );
  }
}

// ── Helpers ───────────────────────────────────────────────────────────────────

String _fmtRelative(DateTime dt) {
  final diff = DateTime.now().difference(dt);
  if (diff.inSeconds < 60)  return 'just now';
  if (diff.inMinutes < 60)  return '${diff.inMinutes}m ago';
  if (diff.inHours   < 24)  return '${diff.inHours}h ago';
  return DateFormat('MMM d').format(dt);
}

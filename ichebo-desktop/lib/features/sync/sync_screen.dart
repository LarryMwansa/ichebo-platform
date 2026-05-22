import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/theme/tokens.dart';
import '../../sync/sync_engine.dart';
import '../../sync/sync_state.dart';
import 'conflict_tile.dart';
import 'sync_providers.dart';

class SyncScreen extends ConsumerWidget {
  const SyncScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final status    = ref.watch(syncStateProvider);
    final notifier  = ref.read(syncStateProvider.notifier);
    final conflicts = ref.watch(conflictsProvider);
    final isDark    = Theme.of(context).brightness == Brightness.dark;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        _StatusHero(status: status, notifier: notifier, isDark: isDark),
        const SizedBox(height: IcsSpacing.m),
        _StatsStrip(status: status, isDark: isDark),
        const SizedBox(height: IcsSpacing.l),
        _ConflictQueue(conflicts: conflicts, isDark: isDark),
      ],
    );
  }
}

// ── Status hero card ──────────────────────────────────────────────────────────

class _StatusHero extends StatelessWidget {
  const _StatusHero({
    required this.status,
    required this.notifier,
    required this.isDark,
  });
  final SyncStatusModel status;
  final SyncStateNotifier notifier;
  final bool isDark;

  static const _stateLabel = {
    SyncState.synced:   'Up to date',
    SyncState.syncing:  'Syncing…',
    SyncState.conflict: 'Conflicts need attention',
    SyncState.blocked:  'Sync blocked',
    SyncState.offline:  'Offline',
  };

  static const _stateDescription = {
    SyncState.synced:   'All local changes have been pushed to the network.',
    SyncState.syncing:  'Exchanging data with the Ichebo network now.',
    SyncState.conflict: 'Some records were changed in two places at once. Review each conflict below.',
    SyncState.blocked:  'The sync engine cannot connect. Check your network or licence key.',
    SyncState.offline:  'No connection to the Ichebo network. Changes are saved locally and will sync when reconnected.',
  };

  Color _stateColor(SyncState s) => switch (s) {
        SyncState.synced   => IcsColors.success,
        SyncState.syncing  => IcsColors.info,
        SyncState.conflict => IcsColors.warning,
        SyncState.blocked  => IcsColors.error,
        SyncState.offline  => const Color(0xFF666666),
      };

  @override
  Widget build(BuildContext context) {
    final color = _stateColor(status.state);
    final label = _stateLabel[status.state] ?? 'Unknown';
    final desc  = _stateDescription[status.state] ?? '';

    return Container(
      decoration: BoxDecoration(
        color: isDark ? IcsColors.ink2 : Colors.white,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: isDark ? IcsColors.borderDark : IcsColors.borderLight),
      ),
      padding: const EdgeInsets.all(IcsSpacing.l),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'SYNC STATUS',
            style: TextStyle(
              fontSize: 10, fontWeight: FontWeight.w700, letterSpacing: 0.8,
              color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted,
            ),
          ),
          const SizedBox(height: IcsSpacing.m),
          Row(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              // State indicator
              if (status.state == SyncState.syncing)
                SizedBox(
                  width: 14, height: 14,
                  child: CircularProgressIndicator(strokeWidth: 2, color: color),
                )
              else
                Container(
                  width: 10, height: 10,
                  decoration: BoxDecoration(
                    color: color, shape: BoxShape.circle,
                    boxShadow: status.state == SyncState.synced
                        ? [BoxShadow(color: color.withValues(alpha: 0.4), blurRadius: 6)]
                        : null,
                  ),
                ),
              const SizedBox(width: IcsSpacing.s),
              Text(
                label,
                style: TextStyle(
                  fontSize: 20, fontWeight: FontWeight.w700,
                  color: isDark ? Colors.white : IcsColors.inkBg,
                ),
              ),
            ],
          ),
          const SizedBox(height: IcsSpacing.xs),
          Text(
            desc,
            style: TextStyle(
              fontSize: 13,
              color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted,
            ),
          ),
          if (status.lastSyncedAt != null) ...[
            const SizedBox(height: IcsSpacing.s),
            Text(
              'Last synced: ${_fmtDateTime(status.lastSyncedAt!)}',
              style: TextStyle(
                fontSize: 12,
                color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted,
              ),
            ),
          ],
          const SizedBox(height: IcsSpacing.m),
          SizedBox(
            child: ElevatedButton.icon(
              onPressed: status.state == SyncState.syncing ? null : notifier.triggerSync,
              icon: const Icon(Icons.sync, size: 14),
              label: const Text('Sync now'),
              style: ElevatedButton.styleFrom(
                backgroundColor: IcsColors.accentRed,
                foregroundColor: Colors.white,
                disabledBackgroundColor: IcsColors.accentRed.withValues(alpha: 0.4),
                padding: const EdgeInsets.symmetric(horizontal: IcsSpacing.m, vertical: 8),
                textStyle: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
              ),
            ),
          ),
        ],
      ),
    );
  }

  String _fmtDateTime(DateTime dt) {
    final months = ['Jan','Feb','Mar','Apr','May','Jun',
                    'Jul','Aug','Sep','Oct','Nov','Dec'];
    final h = dt.hour.toString().padLeft(2, '0');
    final m = dt.minute.toString().padLeft(2, '0');
    return '${dt.day} ${months[dt.month - 1]} ${dt.year}  $h:$m';
  }
}

// ── Stats strip ───────────────────────────────────────────────────────────────

class _StatsStrip extends StatelessWidget {
  const _StatsStrip({required this.status, required this.isDark});
  final SyncStatusModel status;
  final bool isDark;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(child: _StatTile(
          icon: Icons.upload_outlined,
          label: 'Pending',
          value: status.pendingCount.toString(),
          color: status.pendingCount > 0 ? IcsColors.info : null,
          isDark: isDark,
        )),
        const SizedBox(width: IcsSpacing.s),
        Expanded(child: _StatTile(
          icon: Icons.warning_amber_outlined,
          label: 'Conflicts',
          value: status.conflictCount.toString(),
          color: status.conflictCount > 0 ? IcsColors.warning : null,
          isDark: isDark,
        )),
        const SizedBox(width: IcsSpacing.s),
        Expanded(child: _StatTile(
          icon: SyncEngine.instance.isLoaded ? Icons.link : Icons.link_off,
          label: 'Engine',
          value: SyncEngine.instance.isLoaded ? 'Loaded' : 'Offline',
          color: SyncEngine.instance.isLoaded ? IcsColors.success : const Color(0xFF666666),
          isDark: isDark,
        )),
      ],
    );
  }
}

class _StatTile extends StatelessWidget {
  const _StatTile({
    required this.icon,
    required this.label,
    required this.value,
    required this.isDark,
    this.color,
  });
  final IconData icon;
  final String label;
  final String value;
  final bool isDark;
  final Color? color;

  @override
  Widget build(BuildContext context) {
    final fg = color ?? (isDark ? IcsColors.textMutedDark : IcsColors.textMuted);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: IcsSpacing.m, vertical: IcsSpacing.s),
      decoration: BoxDecoration(
        color: isDark ? IcsColors.ink2 : Colors.white,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: isDark ? IcsColors.borderDark : IcsColors.borderLight),
      ),
      child: Row(
        children: [
          Icon(icon, size: 16, color: fg),
          const SizedBox(width: IcsSpacing.s),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                value,
                style: TextStyle(
                  fontSize: 16, fontWeight: FontWeight.w700,
                  color: fg,
                ),
              ),
              Text(
                label,
                style: TextStyle(
                  fontSize: 10,
                  color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

// ── Conflict queue ────────────────────────────────────────────────────────────

class _ConflictQueue extends StatelessWidget {
  const _ConflictQueue({required this.conflicts, required this.isDark});
  final AsyncValue<List<ConflictEntry>> conflicts;
  final bool isDark;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: IcsSpacing.xs),
          child: Text(
            'CONFLICT QUEUE',
            style: TextStyle(
              fontSize: 10, fontWeight: FontWeight.w700, letterSpacing: 0.8,
              color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted,
            ),
          ),
        ),
        const SizedBox(height: IcsSpacing.s),
        conflicts.when(
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (e, _) => Center(
            child: Text('Could not load conflicts: $e',
                style: const TextStyle(fontSize: 13, color: IcsColors.error)),
          ),
          data: (entries) {
            if (entries.isEmpty) {
              return _EmptyConflicts(isDark: isDark);
            }
            return Column(
              children: entries
                  .map((e) => ConflictTile(entry: e, isDark: isDark))
                  .toList(),
            );
          },
        ),
      ],
    );
  }
}

// ── Empty state ───────────────────────────────────────────────────────────────

class _EmptyConflicts extends StatelessWidget {
  const _EmptyConflicts({required this.isDark});
  final bool isDark;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(IcsSpacing.xl),
      decoration: BoxDecoration(
        color: isDark ? IcsColors.ink2 : Colors.white,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: isDark ? IcsColors.borderDark : IcsColors.borderLight),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            Icons.check_circle_outline,
            size: 40,
            color: IcsColors.success.withValues(alpha: 0.6),
          ),
          const SizedBox(height: IcsSpacing.m),
          Text(
            'No conflicts',
            style: TextStyle(
              fontSize: 14, fontWeight: FontWeight.w600,
              color: isDark ? Colors.white : IcsColors.inkBg,
            ),
          ),
          const SizedBox(height: IcsSpacing.xs),
          Text(
            'All records are in agreement. Nothing needs your attention.',
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 12,
              color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted,
            ),
          ),
        ],
      ),
    );
  }
}

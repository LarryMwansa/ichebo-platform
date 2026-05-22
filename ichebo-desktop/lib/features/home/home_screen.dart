import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/theme/tokens.dart';
import '../../sync/sync_engine.dart';
import '../../sync/sync_state.dart';
import 'home_providers.dart';

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        _SyncHeroBanner(isDark: isDark),
        const SizedBox(height: IcsSpacing.l),
        _SnapshotStrip(isDark: isDark),
        const SizedBox(height: IcsSpacing.l),
        Expanded(
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(child: _UpcomingGatheringsCard(isDark: isDark)),
              const SizedBox(width: IcsSpacing.m),
              Expanded(child: _RecentActivityCard(isDark: isDark)),
            ],
          ),
        ),
      ],
    );
  }
}

// ── Sync hero banner ──────────────────────────────────────────────────────────

class _SyncHeroBanner extends ConsumerWidget {
  const _SyncHeroBanner({required this.isDark});
  final bool isDark;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final status  = ref.watch(syncStateProvider);
    final notifier = ref.read(syncStateProvider.notifier);

    final (dotColor, label) = switch (status.state) {
      SyncState.synced   => (IcsColors.success,          'Up to date'),
      SyncState.syncing  => (IcsColors.info,              'Syncing…'),
      SyncState.conflict => (IcsColors.warning,           'Conflicts need attention'),
      SyncState.blocked  => (IcsColors.error,             'Sync blocked'),
      SyncState.offline  => (const Color(0xFF666666),    'Offline'),
    };

    return Container(
      padding: const EdgeInsets.symmetric(
          horizontal: IcsSpacing.m, vertical: IcsSpacing.s),
      decoration: BoxDecoration(
        color: isDark ? IcsColors.ink2 : Colors.white,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: isDark ? IcsColors.borderDark : IcsColors.borderLight),
      ),
      child: Row(children: [
        if (status.state == SyncState.syncing)
          SizedBox(width: 10, height: 10,
              child: CircularProgressIndicator(strokeWidth: 1.5, color: dotColor))
        else
          Container(width: 8, height: 8,
              decoration: BoxDecoration(color: dotColor, shape: BoxShape.circle,
                  boxShadow: status.state == SyncState.synced
                      ? [BoxShadow(color: dotColor.withValues(alpha: 0.4), blurRadius: 4)]
                      : null)),
        const SizedBox(width: IcsSpacing.s),
        Text(label,
            style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600,
                color: isDark ? Colors.white : IcsColors.inkBg)),
        if (status.lastSyncedAt != null) ...[
          const SizedBox(width: IcsSpacing.s),
          Text('· Last synced ${_relTime(status.lastSyncedAt!)}',
              style: TextStyle(fontSize: 11,
                  color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted)),
        ],
        const Spacer(),
        if (status.conflictCount > 0) ...[
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
            decoration: BoxDecoration(
              color: IcsColors.warning.withValues(alpha: 0.15),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Text('${status.conflictCount} conflict${status.conflictCount == 1 ? '' : 's'}',
                style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w700,
                    color: IcsColors.warning)),
          ),
          const SizedBox(width: IcsSpacing.s),
        ],
        GestureDetector(
          onTap: status.state == SyncState.syncing ? null : notifier.triggerSync,
          child: Text('Sync now',
              style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600,
                  color: status.state == SyncState.syncing
                      ? (isDark ? IcsColors.textMutedDark : IcsColors.textMuted)
                      : IcsColors.accentRed)),
        ),
      ]),
    );
  }

  static String _relTime(DateTime dt) {
    final diff = DateTime.now().difference(dt);
    if (diff.inMinutes < 1) return 'just now';
    if (diff.inMinutes < 60) return '${diff.inMinutes}m ago';
    if (diff.inHours < 24) return '${diff.inHours}h ago';
    return '${diff.inDays}d ago';
  }
}

// ── Snapshot strip ────────────────────────────────────────────────────────────

class _SnapshotStrip extends ConsumerWidget {
  const _SnapshotStrip({required this.isDark});
  final bool isDark;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final snapshotAsync = ref.watch(communitySnapshotProvider);

    return snapshotAsync.when(
      loading: () => const SizedBox(height: 64, child: Center(child: CircularProgressIndicator())),
      error: (e, _) => const SizedBox.shrink(),
      data: (snapshot) => Row(children: [
        Expanded(child: _StatCard(
          icon: Icons.groups_outlined,
          label: 'Members',
          value: snapshot.totalMembers.toString(),
          isDark: isDark,
        )),
        const SizedBox(width: IcsSpacing.s),
        Expanded(child: _StatCard(
          icon: Icons.trending_up_outlined,
          label: 'Active this month',
          value: snapshot.activeThisMonth.toString(),
          isDark: isDark,
        )),
        const SizedBox(width: IcsSpacing.s),
        Expanded(child: _StatCard(
          icon: Icons.school_outlined,
          label: 'In formation',
          value: snapshot.formationInProgress.toString(),
          isDark: isDark,
        )),
        const SizedBox(width: IcsSpacing.s),
        Expanded(child: _StatCard(
          icon: SyncEngine.instance.isLoaded ? Icons.cloud_done_outlined : Icons.cloud_off_outlined,
          label: 'Engine',
          value: SyncEngine.instance.isLoaded ? 'Online' : 'Offline',
          color: SyncEngine.instance.isLoaded ? IcsColors.success : const Color(0xFF666666),
          isDark: isDark,
        )),
      ]),
    );
  }
}

class _StatCard extends StatelessWidget {
  const _StatCard({
    required this.icon, required this.label,
    required this.value, required this.isDark, this.color,
  });
  final IconData icon;
  final String label, value;
  final bool isDark;
  final Color? color;

  @override
  Widget build(BuildContext context) {
    final fg = color ?? (isDark ? Colors.white : IcsColors.inkBg);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: IcsSpacing.m, vertical: IcsSpacing.s),
      decoration: BoxDecoration(
        color: isDark ? IcsColors.ink2 : Colors.white,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: isDark ? IcsColors.borderDark : IcsColors.borderLight),
      ),
      child: Row(children: [
        Icon(icon, size: 18, color: fg.withValues(alpha: 0.7)),
        const SizedBox(width: IcsSpacing.s),
        Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(value, style: TextStyle(
              fontSize: 18, fontWeight: FontWeight.w700, color: fg)),
          Text(label, style: TextStyle(fontSize: 10,
              color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted)),
        ]),
      ]),
    );
  }
}

// ── Upcoming gatherings card ──────────────────────────────────────────────────

class _UpcomingGatheringsCard extends ConsumerWidget {
  const _UpcomingGatheringsCard({required this.isDark});
  final bool isDark;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final gatheringsAsync = ref.watch(upcomingGatheringsProvider);

    return _HomeCard(
      title: 'Upcoming Gatherings',
      icon: Icons.event_outlined,
      isDark: isDark,
      child: gatheringsAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Text('Error: $e',
            style: const TextStyle(fontSize: 12, color: IcsColors.error)),
        data: (gatherings) {
          if (gatherings.isEmpty) {
            return _EmptyCard(
              message: 'No upcoming gatherings.',
              isDark: isDark,
            );
          }
          return Column(
            children: gatherings.map((g) => _GatheringRow(g: g, isDark: isDark)).toList(),
          );
        },
      ),
    );
  }
}

class _GatheringRow extends StatelessWidget {
  const _GatheringRow({required this.g, required this.isDark});
  final UpcomingGathering g;
  final bool isDark;

  @override
  Widget build(BuildContext context) {
    final dt = DateTime.tryParse(g.scheduledAt)?.toLocal();
    final months = ['Jan','Feb','Mar','Apr','May','Jun',
                    'Jul','Aug','Sep','Oct','Nov','Dec'];
    final dateLabel = dt != null
        ? '${dt.day} ${months[dt.month - 1]}  '
          '${dt.hour.toString().padLeft(2,'0')}:${dt.minute.toString().padLeft(2,'0')}'
        : '—';

    return Padding(
      padding: const EdgeInsets.only(bottom: IcsSpacing.s),
      child: Row(children: [
        Expanded(child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(g.title, maxLines: 1, overflow: TextOverflow.ellipsis,
                style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600,
                    color: isDark ? Colors.white : IcsColors.inkBg)),
            Text(dateLabel, style: TextStyle(fontSize: 11,
                color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted)),
          ],
        )),
        if (g.attendanceCount > 0)
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
            decoration: BoxDecoration(
              color: IcsColors.success.withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Text('${g.attendanceCount} present',
                style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w600,
                    color: IcsColors.success)),
          ),
      ]),
    );
  }
}

// ── Recent activity card ──────────────────────────────────────────────────────

class _RecentActivityCard extends ConsumerWidget {
  const _RecentActivityCard({required this.isDark});
  final bool isDark;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final eventsAsync = ref.watch(recentEventsProvider);

    return _HomeCard(
      title: 'Recent Activity',
      icon: Icons.history_outlined,
      isDark: isDark,
      child: eventsAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Text('Error: $e',
            style: const TextStyle(fontSize: 12, color: IcsColors.error)),
        data: (events) {
          if (events.isEmpty) {
            return _EmptyCard(message: 'No recent activity.', isDark: isDark);
          }
          return Column(
            children: events.map((e) => _EventRow(event: e, isDark: isDark)).toList(),
          );
        },
      ),
    );
  }
}

class _EventRow extends StatelessWidget {
  const _EventRow({required this.event, required this.isDark});
  final RecentEvent event;
  final bool isDark;

  static String _statusVerb(String s) => switch (s) {
        'completed'   => 'completed',
        'in_progress' => 'started',
        'cancelled'   => 'cancelled',
        'deferred'    => 'deferred',
        _             => s,
      };

  @override
  Widget build(BuildContext context) {
    final dt = DateTime.tryParse(event.changedAt)?.toLocal();
    final timeLabel = dt != null ? _relTime(dt) : '—';

    return Padding(
      padding: const EdgeInsets.only(bottom: IcsSpacing.s),
      child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Container(
          width: 6, height: 6, margin: const EdgeInsets.only(top: 5, right: 8),
          decoration: const BoxDecoration(
              color: IcsColors.accentRed, shape: BoxShape.circle),
        ),
        Expanded(child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('${event.activityTitle} ${_statusVerb(event.toStatus)}',
                maxLines: 2, overflow: TextOverflow.ellipsis,
                style: TextStyle(fontSize: 12,
                    color: isDark ? Colors.white.withValues(alpha: 0.9) : IcsColors.inkBg)),
            Text(timeLabel, style: TextStyle(fontSize: 10,
                color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted)),
          ],
        )),
      ]),
    );
  }

  static String _relTime(DateTime dt) {
    final diff = DateTime.now().difference(dt);
    if (diff.inMinutes < 1) return 'just now';
    if (diff.inMinutes < 60) return '${diff.inMinutes}m ago';
    if (diff.inHours < 24) return '${diff.inHours}h ago';
    if (diff.inDays == 1) return 'yesterday';
    return '${diff.inDays} days ago';
  }
}

// ── Shared home card chrome ───────────────────────────────────────────────────

class _HomeCard extends StatelessWidget {
  const _HomeCard({
    required this.title, required this.icon,
    required this.isDark, required this.child,
  });
  final String title;
  final IconData icon;
  final bool isDark;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: isDark ? IcsColors.ink2 : Colors.white,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: isDark ? IcsColors.borderDark : IcsColors.borderLight),
      ),
      child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(
              IcsSpacing.m, IcsSpacing.m, IcsSpacing.m, IcsSpacing.s),
          child: Row(children: [
            Icon(icon, size: 14,
                color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted),
            const SizedBox(width: IcsSpacing.xs),
            Text(title.toUpperCase(),
                style: TextStyle(fontSize: 10, fontWeight: FontWeight.w700,
                    letterSpacing: 0.8,
                    color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted)),
          ]),
        ),
        Divider(height: 1, color: isDark ? IcsColors.borderDark : IcsColors.borderLight),
        Padding(padding: const EdgeInsets.all(IcsSpacing.m), child: child),
      ]),
    );
  }
}

class _EmptyCard extends StatelessWidget {
  const _EmptyCard({required this.message, required this.isDark});
  final String message;
  final bool isDark;

  @override
  Widget build(BuildContext context) => Text(message,
      style: TextStyle(fontSize: 12,
          color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted));
}

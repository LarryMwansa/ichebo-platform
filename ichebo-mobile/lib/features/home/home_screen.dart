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
    return Scaffold(
      appBar: AppBar(
        title: const Text('Ichebo'),
        actions: [
          _SyncDot(isDark: isDark),
          const SizedBox(width: IcsSpacing.s),
        ],
      ),
      body: RefreshIndicator(
        color: IcsColors.accentRed,
        onRefresh: () async {
          ref.invalidate(communitySnapshotProvider);
          ref.invalidate(upcomingGatheringsProvider);
          ref.invalidate(recentEventsProvider);
        },
        child: ListView(
          padding: const EdgeInsets.all(IcsSpacing.m),
          children: [
            _SyncBanner(isDark: isDark),
            const SizedBox(height: IcsSpacing.m),
            _SnapshotStrip(isDark: isDark),
            const SizedBox(height: IcsSpacing.m),
            _UpcomingGatheringsCard(isDark: isDark),
            const SizedBox(height: IcsSpacing.m),
            _RecentActivityCard(isDark: isDark),
            const SizedBox(height: IcsSpacing.l),
          ],
        ),
      ),
    );
  }
}

// ── Sync dot in app bar ───────────────────────────────────────────────────────

class _SyncDot extends ConsumerWidget {
  const _SyncDot({required this.isDark});
  final bool isDark;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final status = ref.watch(syncStateProvider);
    final color = switch (status.state) {
      SyncState.synced   => IcsColors.accentGreen,
      SyncState.syncing  => IcsColors.accentBlue,
      SyncState.conflict => IcsColors.accentAmber,
      SyncState.blocked  => const Color(0xFFDC2626),
      SyncState.offline  => const Color(0xFF666666),
    };
    if (status.state == SyncState.syncing) {
      return Padding(
        padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 4),
        child: SizedBox(
          width: 16, height: 16,
          child: CircularProgressIndicator(strokeWidth: 2, color: color),
        ),
      );
    }
    return Container(
      width: 8, height: 8,
      margin: const EdgeInsets.symmetric(vertical: 20, horizontal: 4),
      decoration: BoxDecoration(color: color, shape: BoxShape.circle),
    );
  }
}

// ── Sync banner ───────────────────────────────────────────────────────────────

class _SyncBanner extends ConsumerWidget {
  const _SyncBanner({required this.isDark});
  final bool isDark;

  static String _relTime(DateTime dt) {
    final diff = DateTime.now().difference(dt);
    if (diff.inMinutes < 1)  return 'just now';
    if (diff.inMinutes < 60) return '${diff.inMinutes}m ago';
    if (diff.inHours < 24)   return '${diff.inHours}h ago';
    return '${diff.inDays}d ago';
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final status   = ref.watch(syncStateProvider);
    final notifier = ref.read(syncStateProvider.notifier);

    final (color, label) = switch (status.state) {
      SyncState.synced   => (IcsColors.accentGreen,         'Up to date'),
      SyncState.syncing  => (IcsColors.accentBlue,          'Syncing…'),
      SyncState.conflict => (IcsColors.accentAmber,         'Conflicts need attention'),
      SyncState.blocked  => (const Color(0xFFDC2626),       'Sync blocked'),
      SyncState.offline  => (const Color(0xFF666666),       'Offline'),
    };

    return Container(
      padding: const EdgeInsets.symmetric(
          horizontal: IcsSpacing.m, vertical: IcsSpacing.s),
      decoration: BoxDecoration(
        color: isDark ? IcsColors.stone1 : Colors.white,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
            color: isDark ? IcsColors.borderDark : IcsColors.borderLight),
      ),
      child: Row(children: [
        Container(
          width: 8, height: 8,
          decoration: BoxDecoration(color: color, shape: BoxShape.circle),
        ),
        const SizedBox(width: IcsSpacing.s),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(label,
                  style: TextStyle(
                    fontSize: 13, fontWeight: FontWeight.w600,
                    color: isDark ? Colors.white : IcsColors.inkBg,
                  )),
              if (status.lastSyncedAt != null)
                Text('Last synced ${_relTime(status.lastSyncedAt!)}',
                    style: TextStyle(fontSize: 11,
                        color: isDark
                            ? IcsColors.textMutedDark
                            : IcsColors.textMuted)),
            ],
          ),
        ),
        if (status.conflictCount > 0) ...[
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
            decoration: BoxDecoration(
              color: IcsColors.accentAmber.withValues(alpha: 0.15),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Text(
              '${status.conflictCount} conflict${status.conflictCount == 1 ? '' : 's'}',
              style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w700,
                  color: IcsColors.accentAmber),
            ),
          ),
          const SizedBox(width: IcsSpacing.s),
        ],
        TextButton(
          onPressed:
              status.state == SyncState.syncing ? null : notifier.triggerSync,
          style: TextButton.styleFrom(
            padding: const EdgeInsets.symmetric(horizontal: IcsSpacing.s),
            minimumSize: Size.zero,
            tapTargetSize: MaterialTapTargetSize.shrinkWrap,
          ),
          child: Text('Sync now',
              style: TextStyle(
                fontSize: 12, fontWeight: FontWeight.w600,
                color: status.state == SyncState.syncing
                    ? (isDark ? IcsColors.textMutedDark : IcsColors.textMuted)
                    : IcsColors.accentRed,
              )),
        ),
      ]),
    );
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
      loading: () => const SizedBox(
          height: 72,
          child: Center(child: CircularProgressIndicator())),
      error: (_, st) => const SizedBox.shrink(),
      data: (s) => Row(children: [
        Expanded(child: _StatTile(
          icon: Icons.groups_outlined,
          label: 'Members',
          value: s.totalMembers.toString(),
          isDark: isDark,
        )),
        const SizedBox(width: IcsSpacing.s),
        Expanded(child: _StatTile(
          icon: Icons.trending_up_outlined,
          label: 'Active',
          value: s.activeThisMonth.toString(),
          isDark: isDark,
        )),
        const SizedBox(width: IcsSpacing.s),
        Expanded(child: _StatTile(
          icon: Icons.school_outlined,
          label: 'Formation',
          value: s.formationInProgress.toString(),
          isDark: isDark,
        )),
        const SizedBox(width: IcsSpacing.s),
        Expanded(child: _StatTile(
          icon: SyncEngine.instance.isLoaded
              ? Icons.cloud_done_outlined
              : Icons.cloud_off_outlined,
          label: 'Engine',
          value: SyncEngine.instance.isLoaded ? 'On' : 'Off',
          color: SyncEngine.instance.isLoaded
              ? IcsColors.accentGreen
              : const Color(0xFF666666),
          isDark: isDark,
        )),
      ]),
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
  final String   label, value;
  final bool     isDark;
  final Color?   color;

  @override
  Widget build(BuildContext context) {
    final fg = color ?? (isDark ? Colors.white : IcsColors.inkBg);
    return Container(
      padding: const EdgeInsets.symmetric(
          horizontal: IcsSpacing.s, vertical: IcsSpacing.s),
      decoration: BoxDecoration(
        color: isDark ? IcsColors.stone1 : Colors.white,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
            color: isDark ? IcsColors.borderDark : IcsColors.borderLight),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, size: 16, color: fg.withValues(alpha: 0.7)),
          const SizedBox(height: 4),
          Text(value,
              style: TextStyle(
                  fontSize: 18, fontWeight: FontWeight.w700, color: fg)),
          Text(label,
              style: TextStyle(
                  fontSize: 10,
                  color: isDark
                      ? IcsColors.textMutedDark
                      : IcsColors.textMuted)),
        ],
      ),
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
    return _Card(
      title: 'Upcoming Gatherings',
      icon: Icons.event_outlined,
      isDark: isDark,
      child: gatheringsAsync.when(
        loading: () => const _CardLoading(),
        error:   (e, _) => _CardError(message: e.toString()),
        data: (gatherings) {
          if (gatherings.isEmpty) {
            return _CardEmpty(
                message: 'No upcoming gatherings.', isDark: isDark);
          }
          return Column(
            children: gatherings
                .map((g) => _GatheringRow(g: g, isDark: isDark))
                .toList(),
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
    const months = [
      'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
    ];
    final dateLabel = dt != null
        ? '${dt.day} ${months[dt.month - 1]}  '
          '${dt.hour.toString().padLeft(2, '0')}:'
          '${dt.minute.toString().padLeft(2, '0')}'
        : '—';

    return Padding(
      padding: const EdgeInsets.only(bottom: IcsSpacing.s),
      child: Row(children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(g.title,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w600,
                      color: isDark ? Colors.white : IcsColors.inkBg)),
              Text(dateLabel,
                  style: TextStyle(
                      fontSize: 11,
                      color: isDark
                          ? IcsColors.textMutedDark
                          : IcsColors.textMuted)),
            ],
          ),
        ),
        if (g.attendanceCount > 0)
          Container(
            padding:
                const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
            decoration: BoxDecoration(
              color: IcsColors.accentGreen.withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Text('${g.attendanceCount}',
                style: const TextStyle(
                    fontSize: 10,
                    fontWeight: FontWeight.w600,
                    color: IcsColors.accentGreen)),
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
    return _Card(
      title: 'Recent Activity',
      icon: Icons.history_outlined,
      isDark: isDark,
      child: eventsAsync.when(
        loading: () => const _CardLoading(),
        error:   (e, _) => _CardError(message: e.toString()),
        data:    (events) {
          if (events.isEmpty) {
            return _CardEmpty(
                message: 'No recent activity.', isDark: isDark);
          }
          return Column(
            children: events
                .map((e) => _EventRow(event: e, isDark: isDark))
                .toList(),
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

  static String _verb(String s) => switch (s) {
    'completed'   => 'completed',
    'in_progress' => 'started',
    'cancelled'   => 'cancelled',
    'deferred'    => 'deferred',
    _             => s,
  };

  static String _relTime(DateTime dt) {
    final diff = DateTime.now().difference(dt);
    if (diff.inMinutes < 1)  return 'just now';
    if (diff.inMinutes < 60) return '${diff.inMinutes}m ago';
    if (diff.inHours < 24)   return '${diff.inHours}h ago';
    if (diff.inDays == 1)    return 'yesterday';
    return '${diff.inDays}d ago';
  }

  @override
  Widget build(BuildContext context) {
    final dt        = DateTime.tryParse(event.changedAt)?.toLocal();
    final timeLabel = dt != null ? _relTime(dt) : '—';

    return Padding(
      padding: const EdgeInsets.only(bottom: IcsSpacing.s),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 6, height: 6,
            margin: const EdgeInsets.only(top: 5, right: 8),
            decoration: const BoxDecoration(
                color: IcsColors.accentRed, shape: BoxShape.circle),
          ),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '${event.activityTitle} ${_verb(event.toStatus)}',
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(
                      fontSize: 13,
                      color: isDark
                          ? Colors.white.withValues(alpha: 0.9)
                          : IcsColors.inkBg),
                ),
                Text(timeLabel,
                    style: TextStyle(
                        fontSize: 11,
                        color: isDark
                            ? IcsColors.textMutedDark
                            : IcsColors.textMuted)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// ── Shared card chrome ────────────────────────────────────────────────────────

class _Card extends StatelessWidget {
  const _Card({
    required this.title,
    required this.icon,
    required this.isDark,
    required this.child,
  });
  final String   title;
  final IconData icon;
  final bool     isDark;
  final Widget   child;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: isDark ? IcsColors.stone1 : Colors.white,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
            color: isDark ? IcsColors.borderDark : IcsColors.borderLight),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(
                IcsSpacing.m, IcsSpacing.m, IcsSpacing.m, IcsSpacing.s),
            child: Row(children: [
              Icon(icon,
                  size: 14,
                  color: isDark
                      ? IcsColors.textMutedDark
                      : IcsColors.textMuted),
              const SizedBox(width: IcsSpacing.xs),
              Text(
                title.toUpperCase(),
                style: TextStyle(
                    fontSize: 10,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 0.8,
                    color: isDark
                        ? IcsColors.textMutedDark
                        : IcsColors.textMuted),
              ),
            ]),
          ),
          Divider(
              height: 1,
              color: isDark ? IcsColors.borderDark : IcsColors.borderLight),
          Padding(
              padding: const EdgeInsets.all(IcsSpacing.m), child: child),
        ],
      ),
    );
  }
}

class _CardLoading extends StatelessWidget {
  const _CardLoading();
  @override
  Widget build(BuildContext context) => const Padding(
    padding: EdgeInsets.symmetric(vertical: IcsSpacing.m),
    child: Center(child: CircularProgressIndicator()),
  );
}

class _CardError extends StatelessWidget {
  const _CardError({required this.message});
  final String message;
  @override
  Widget build(BuildContext context) => Text('Error: $message',
      style: const TextStyle(fontSize: 12, color: Color(0xFFDC2626)));
}

class _CardEmpty extends StatelessWidget {
  const _CardEmpty({required this.message, required this.isDark});
  final String message;
  final bool   isDark;
  @override
  Widget build(BuildContext context) => Text(message,
      style: TextStyle(
          fontSize: 13,
          color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted));
}

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/services/activity_service.dart';
import '../../core/theme/tokens.dart';
import '../../shared/activity_type_badge.dart';
import '../../shared/member_list_tile.dart';
import '../people/people_providers.dart';
import 'activity_form.dart';
import 'activity_providers.dart';
import 'attendance_flow.dart';

class ActivityDetail extends ConsumerWidget {
  const ActivityDetail({super.key, required this.activityId});
  final String activityId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final actAsync = ref.watch(activityByIdProvider(activityId));
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return actAsync.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (e, _) => Center(child: Text('Error: $e')),
      data: (activity) {
        if (activity == null) {
          return Center(
            child: Text('Activity not found.',
                style: TextStyle(color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted)),
          );
        }
        return SingleChildScrollView(
          padding: const EdgeInsets.all(IcsSpacing.l),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              _ActivityHeader(activity: activity, isDark: isDark),
              const SizedBox(height: IcsSpacing.l),
              _DetailsCard(activity: activity, isDark: isDark),
              if (activity.activityType == 'gathering') ...[
                const SizedBox(height: IcsSpacing.m),
                _GatheringCard(activity: activity, isDark: isDark),
              ],
              const SizedBox(height: IcsSpacing.l),
              _ActionBar(activity: activity, isDark: isDark),
            ],
          ),
        );
      },
    );
  }
}

// ── Header ────────────────────────────────────────────────────────────────────

class _ActivityHeader extends StatelessWidget {
  const _ActivityHeader({required this.activity, required this.isDark});
  final ActivityModel activity;
  final bool isDark;

  static Color _statusColor(String s) => switch (s) {
        'completed'   => IcsColors.success,
        'in_progress' => IcsColors.info,
        'cancelled'   => IcsColors.error,
        'deferred'    => IcsColors.warning,
        _             => const Color(0xFF9E9E9E),
      };

  static String _statusLabel(String s) => switch (s) {
        'completed'   => 'Completed',
        'in_progress' => 'In progress',
        'cancelled'   => 'Cancelled',
        'deferred'    => 'Deferred',
        _             => 'Pending',
      };

  @override
  Widget build(BuildContext context) {
    final dot = _statusColor(activity.status);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        ActivityTypeBadge(type: activity.activityType, large: true),
        const SizedBox(height: IcsSpacing.s),
        Text(
          activity.title,
          style: TextStyle(
            fontFamily: 'Playfair Display', fontSize: 20, fontWeight: FontWeight.w700,
            color: isDark ? Colors.white : IcsColors.inkBg,
          ),
        ),
        const SizedBox(height: IcsSpacing.xs),
        Row(
          children: [
            Container(width: 7, height: 7,
                decoration: BoxDecoration(color: dot, shape: BoxShape.circle)),
            const SizedBox(width: 4),
            Text(_statusLabel(activity.status),
                style: TextStyle(fontSize: 12, color: dot)),
          ],
        ),
      ],
    );
  }
}

// ── Details card ──────────────────────────────────────────────────────────────

class _DetailsCard extends ConsumerWidget {
  const _DetailsCard({required this.activity, required this.isDark});
  final ActivityModel activity;
  final bool isDark;

  String _fmtDate(String? iso) {
    if (iso == null || iso.isEmpty) return '—';
    try {
      final dt = DateTime.parse(iso).toLocal();
      final months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
      final h = dt.hour.toString().padLeft(2, '0');
      final m = dt.minute.toString().padLeft(2, '0');
      return '${dt.day} ${months[dt.month - 1]} ${dt.year}  $h:$m';
    } catch (_) {
      return iso;
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final assignedAsync = activity.assignedTo != null
        ? ref.watch(memberByIdProvider(activity.assignedTo!))
        : const AsyncData<MemberModel?>(null);

    return _DetailCard(
      title: 'Details',
      isDark: isDark,
      child: Column(
        children: [
          if (activity.scheduledAt != null && activity.scheduledAt!.isNotEmpty)
            _Row('Scheduled', _fmtDate(activity.scheduledAt), isDark),
          if (activity.dueAt != null && activity.dueAt!.isNotEmpty) ...[
            const SizedBox(height: IcsSpacing.s),
            _Row('Due', _fmtDate(activity.dueAt), isDark),
          ],
          if (activity.completedAt != null && activity.completedAt!.isNotEmpty) ...[
            const SizedBox(height: IcsSpacing.s),
            _Row('Completed', _fmtDate(activity.completedAt), isDark),
          ],
          const SizedBox(height: IcsSpacing.s),
          _RowWidget(
            label: 'Assigned to',
            isDark: isDark,
            child: assignedAsync.when(
              loading: () => const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(strokeWidth: 2)),
              error: (_, st) => Text('—', style: TextStyle(fontSize: 13, color: isDark ? Colors.white : IcsColors.inkBg)),
              data: (member) => member != null
                  ? MemberListTile(
                      displayName: member.displayName, email: member.email,
                      competenceLevel: member.competenceLevel, compact: true)
                  : Text('—', style: TextStyle(fontSize: 13, color: isDark ? Colors.white : IcsColors.inkBg)),
            ),
          ),
          if (activity.description.isNotEmpty) ...[
            const SizedBox(height: IcsSpacing.s),
            _Row('Description', activity.description, isDark),
          ],
        ],
      ),
    );
  }
}

// ── Gathering card ────────────────────────────────────────────────────────────

class _GatheringCard extends ConsumerWidget {
  const _GatheringCard({required this.activity, required this.isDark});
  final ActivityModel activity;
  final bool isDark;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final countAsync = ref.watch(attendanceCountProvider(activity.id));
    final totalAsync = ref.watch(membersProvider);

    final formatLabel = switch (activity.format ?? 'in_person') {
      'digital' => 'Digital',
      'hybrid'  => 'Hybrid',
      _         => 'In person',
    };

    return _DetailCard(
      title: 'Gathering',
      isDark: isDark,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _Row('Format', formatLabel, isDark),
          if (activity.location != null && activity.location!.isNotEmpty) ...[
            const SizedBox(height: IcsSpacing.s),
            _Row('Location', activity.location!, isDark),
          ],
          if (activity.durationMinutes != null) ...[
            const SizedBox(height: IcsSpacing.s),
            _Row('Duration', '${activity.durationMinutes} min', isDark),
          ],
          const SizedBox(height: IcsSpacing.m),
          countAsync.when(
            loading: () => const SizedBox(height: 20, child: LinearProgressIndicator()),
            error: (_, st) => const SizedBox.shrink(),
            data: (count) {
              final total = totalAsync.maybeWhen(data: (l) => l.length, orElse: () => 0);
              return Row(
                children: [
                  Icon(Icons.people_outline, size: 16,
                      color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted),
                  const SizedBox(width: IcsSpacing.s),
                  Text(
                    count > 0 ? '$count of $total members attended' : 'Attendance not yet recorded',
                    style: TextStyle(fontSize: 13,
                        fontWeight: count > 0 ? FontWeight.w600 : FontWeight.w400,
                        color: count > 0 ? (isDark ? Colors.white : IcsColors.inkBg)
                            : (isDark ? IcsColors.textMutedDark : IcsColors.textMuted)),
                  ),
                ],
              );
            },
          ),
          const SizedBox(height: IcsSpacing.m),
          SizedBox(
            width: double.infinity,
            child: OutlinedButton.icon(
              onPressed: () async {
                await Navigator.of(context).push<void>(
                  MaterialPageRoute(
                    fullscreenDialog: true,
                    builder: (_) => AttendanceFlow(activity: activity),
                  ),
                );
                ref.invalidate(attendanceCountProvider(activity.id));
                ref.invalidate(activityByIdProvider(activity.id));
              },
              icon: const Icon(Icons.how_to_reg_outlined, size: 16),
              label: const Text('Mark attendance'),
              style: OutlinedButton.styleFrom(
                foregroundColor: IcsColors.accentRed,
                side: const BorderSide(color: IcsColors.accentRed),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// ── Action bar ────────────────────────────────────────────────────────────────

class _ActionBar extends ConsumerWidget {
  const _ActionBar({required this.activity, required this.isDark});
  final ActivityModel activity;
  final bool isDark;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final isComplete = activity.status == 'completed';

    return Row(
      children: [
        OutlinedButton.icon(
          onPressed: () async {
            final result = await showDialog<bool>(
              context: context,
              builder: (_) => ActivityForm(mode: ActivityFormMode.edit, activity: activity),
            );
            if (result == true) {
              ref.invalidate(activityByIdProvider(activity.id));
              ref.invalidate(activitiesProvider);
            }
          },
          icon: const Icon(Icons.edit_outlined, size: 14),
          label: const Text('Edit'),
          style: OutlinedButton.styleFrom(
            foregroundColor: isDark ? Colors.white : IcsColors.inkBg,
            side: BorderSide(color: isDark ? IcsColors.borderDark : IcsColors.borderLight),
          ),
        ),
        const SizedBox(width: IcsSpacing.s),
        OutlinedButton.icon(
          onPressed: isComplete ? null : () async {
            final now = DateTime.now().toIso8601String();
            final updated = activity.copyWith(status: 'completed', completedAt: now);
            final result = await ActivityService.updateActivity(updated);
            if (result == 0 || result == -99) {
              ref.invalidate(activityByIdProvider(activity.id));
              ref.invalidate(activitiesProvider);
            }
          },
          icon: const Icon(Icons.check_circle_outline, size: 14),
          label: Text(isComplete ? 'Completed' : 'Mark complete'),
          style: OutlinedButton.styleFrom(
            foregroundColor: isComplete ? IcsColors.success : (isDark ? Colors.white : IcsColors.inkBg),
            side: BorderSide(
              color: isComplete ? IcsColors.success : (isDark ? IcsColors.borderDark : IcsColors.borderLight),
            ),
          ),
        ),
      ],
    );
  }
}

// ── Shared card chrome ────────────────────────────────────────────────────────

class _DetailCard extends StatelessWidget {
  const _DetailCard({required this.title, required this.isDark, required this.child});
  final String title;
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
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(IcsSpacing.m, IcsSpacing.m, IcsSpacing.m, IcsSpacing.s),
            child: Text(
              title.toUpperCase(),
              style: TextStyle(fontSize: 10, fontWeight: FontWeight.w700,
                  letterSpacing: 0.8,
                  color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted),
            ),
          ),
          Divider(height: 1, color: isDark ? IcsColors.borderDark : IcsColors.borderLight),
          Padding(padding: const EdgeInsets.all(IcsSpacing.m), child: child),
        ],
      ),
    );
  }
}

class _Row extends StatelessWidget {
  const _Row(this.label, this.value, this.isDark);
  final String label;
  final String value;
  final bool isDark;

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SizedBox(
          width: 110,
          child: Text(label,
              style: TextStyle(fontSize: 12, color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted)),
        ),
        Expanded(
          child: Text(value,
              style: TextStyle(fontSize: 13, color: isDark ? Colors.white : IcsColors.inkBg)),
        ),
      ],
    );
  }
}

class _RowWidget extends StatelessWidget {
  const _RowWidget({required this.label, required this.child, required this.isDark});
  final String label;
  final Widget child;
  final bool isDark;

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        SizedBox(
          width: 110,
          child: Text(label,
              style: TextStyle(fontSize: 12, color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted)),
        ),
        Expanded(child: child),
      ],
    );
  }
}

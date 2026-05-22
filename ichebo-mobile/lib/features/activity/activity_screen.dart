import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../../core/theme/tokens.dart';
import '../../sync/sync_engine.dart';
import 'activity_providers.dart';

class ActivityScreen extends ConsumerWidget {
  const ActivityScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final selectedId = ref.watch(selectedActivityIdProvider);
    if (selectedId != null) {
      return _ActivityDetailScreen(activityId: selectedId);
    }
    return const _ActivityListScreen();
  }
}

// ── List screen ───────────────────────────────────────────────────────────────

class _ActivityListScreen extends ConsumerWidget {
  const _ActivityListScreen();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final filtered = ref.watch(filteredActivitiesProvider);

    return Scaffold(
      backgroundColor: IcsColors.inkBg,
      appBar: AppBar(
        backgroundColor: IcsColors.stone1,
        title: const Text('Activity'),
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(108),
          child: Column(
            children: [
              _SearchBar(
                onChanged: (v) =>
                    ref.read(activitySearchProvider.notifier).state = v,
              ),
              _TypeChips(),
            ],
          ),
        ),
      ),
      body: filtered.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error:   (e, st) => Center(
          child: Text('Error: $e',
              style: const TextStyle(color: IcsColors.accentRed)),
        ),
        data: (list) {
          if (list.isEmpty) {
            return const Center(
              child: Text('No activities',
                  style: TextStyle(color: IcsColors.textMuted)),
            );
          }
          return RefreshIndicator(
            onRefresh: () async =>
                ref.invalidate(activitiesProvider),
            child: ListView.separated(
              padding: const EdgeInsets.all(IcsSpacing.m),
              itemCount: list.length,
              separatorBuilder: (_, i) =>
                  const SizedBox(height: IcsSpacing.s),
              itemBuilder: (_, i) => _ActivityTile(
                activity: list[i],
                onTap: () => ref
                    .read(selectedActivityIdProvider.notifier)
                    .state = list[i].id,
              ),
            ),
          );
        },
      ),
    );
  }
}

// ── Search bar ────────────────────────────────────────────────────────────────

class _SearchBar extends StatefulWidget {
  const _SearchBar({required this.onChanged});
  final ValueChanged<String> onChanged;

  @override
  State<_SearchBar> createState() => _SearchBarState();
}

class _SearchBarState extends State<_SearchBar> {
  final _ctrl = TextEditingController();

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(
          IcsSpacing.m, 0, IcsSpacing.m, IcsSpacing.s),
      child: TextField(
        controller: _ctrl,
        onChanged: widget.onChanged,
        style: const TextStyle(color: Colors.white),
        decoration: InputDecoration(
          hintText: 'Search activities…',
          hintStyle: const TextStyle(color: IcsColors.textMuted),
          prefixIcon:
              const Icon(Icons.search, color: IcsColors.textMuted, size: 18),
          suffixIcon: _ctrl.text.isNotEmpty
              ? IconButton(
                  icon: const Icon(Icons.clear,
                      color: IcsColors.textMuted, size: 18),
                  onPressed: () {
                    _ctrl.clear();
                    widget.onChanged('');
                  },
                )
              : null,
          filled: true,
          fillColor: IcsColors.stone2,
          contentPadding:
              const EdgeInsets.symmetric(vertical: IcsSpacing.s),
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(8),
            borderSide: BorderSide.none,
          ),
        ),
      ),
    );
  }
}

// ── Type filter chips ─────────────────────────────────────────────────────────

const _kTypes = [
  ('gathering', 'Gathering'),
  ('event',     'Event'),
  ('task',      'Task'),
  ('campaign',  'Campaign'),
  ('goal',      'Goal'),
  ('habit',     'Habit'),
];

class _TypeChips extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final current = ref.watch(activityFilterTypeProvider);
    return SizedBox(
      height: 48,
      child: ListView(
        padding: const EdgeInsets.symmetric(
            horizontal: IcsSpacing.m, vertical: IcsSpacing.xs),
        scrollDirection: Axis.horizontal,
        children: _kTypes.map((entry) {
          final (type, label) = entry;
          final selected = current == type;
          return Padding(
            padding: const EdgeInsets.only(right: IcsSpacing.s),
            child: FilterChip(
              label: Text(label),
              selected: selected,
              onSelected: (v) => ref
                  .read(activityFilterTypeProvider.notifier)
                  .state = v ? type : null,
              selectedColor: IcsColors.accentBlue.withAlpha(51),
              checkmarkColor: IcsColors.accentBlue,
              labelStyle: TextStyle(
                color: selected
                    ? IcsColors.accentBlue
                    : IcsColors.textMuted,
                fontSize: 12,
              ),
              backgroundColor: IcsColors.stone2,
              side: BorderSide(
                color: selected
                    ? IcsColors.accentBlue
                    : IcsColors.borderDark,
              ),
            ),
          );
        }).toList(),
      ),
    );
  }
}

// ── Activity tile ─────────────────────────────────────────────────────────────

class _ActivityTile extends ConsumerWidget {
  const _ActivityTile({required this.activity, required this.onTap});
  final ActivityModel activity;
  final VoidCallback  onTap;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Card(
      color: IcsColors.stone1,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8),
        side: const BorderSide(color: IcsColors.borderDark),
      ),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(8),
        child: Padding(
          padding: const EdgeInsets.all(IcsSpacing.m),
          child: Row(
            children: [
              _TypeDot(type: activity.activityType),
              const SizedBox(width: IcsSpacing.m),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      activity.title,
                      style: const TextStyle(
                          color: Colors.white,
                          fontWeight: FontWeight.w500),
                    ),
                    if (activity.scheduledAt != null &&
                        activity.scheduledAt!.isNotEmpty) ...[
                      const SizedBox(height: 2),
                      Text(
                        _fmtDate(activity.scheduledAt!),
                        style: const TextStyle(
                            color: IcsColors.textMuted, fontSize: 12),
                      ),
                    ],
                  ],
                ),
              ),
              if (activity.isGathering)
                _AttendanceBadge(activityId: activity.id),
              const SizedBox(width: IcsSpacing.s),
              _StatusDot(status: activity.status),
              const Icon(Icons.chevron_right,
                  color: IcsColors.textMuted, size: 18),
            ],
          ),
        ),
      ),
    );
  }
}

// ── Attendance badge (for gatherings) ─────────────────────────────────────────

class _AttendanceBadge extends ConsumerWidget {
  const _AttendanceBadge({required this.activityId});
  final String activityId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final count = ref.watch(attendanceCountProvider(activityId));
    return count.maybeWhen(
      data: (n) => Container(
        padding: const EdgeInsets.symmetric(
            horizontal: IcsSpacing.s, vertical: 2),
        decoration: BoxDecoration(
          color: IcsColors.accentBlue.withAlpha(26),
          borderRadius: BorderRadius.circular(10),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.people_outline,
                size: 12, color: IcsColors.accentBlue),
            const SizedBox(width: 3),
            Text('$n',
                style: const TextStyle(
                    color: IcsColors.accentBlue, fontSize: 11)),
          ],
        ),
      ),
      orElse: () => const SizedBox.shrink(),
    );
  }
}

// ── Type dot ──────────────────────────────────────────────────────────────────

class _TypeDot extends StatelessWidget {
  const _TypeDot({required this.type});
  final String type;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 10,
      height: 10,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        color: _color(type),
      ),
    );
  }

  static Color _color(String type) => switch (type) {
    'gathering' => IcsColors.accentBlue,
    'event'     => IcsColors.accentAmber,
    'task'      => IcsColors.accentGreen,
    'campaign'  => IcsColors.accentRed,
    'goal'      => Colors.purple,
    'habit'     => Colors.teal,
    _           => IcsColors.textMuted,
  };
}

// ── Status dot ────────────────────────────────────────────────────────────────

class _StatusDot extends StatelessWidget {
  const _StatusDot({required this.status});
  final String status;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 8,
      height: 8,
      margin: const EdgeInsets.only(right: 4),
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        color: _color(status),
      ),
    );
  }

  static Color _color(String s) => switch (s) {
    'completed'  => IcsColors.accentGreen,
    'cancelled'  => IcsColors.accentRed,
    'active'     => IcsColors.accentBlue,
    'scheduled'  => IcsColors.accentAmber,
    _            => IcsColors.textMuted,
  };
}

// ── Detail screen ─────────────────────────────────────────────────────────────

class _ActivityDetailScreen extends ConsumerWidget {
  const _ActivityDetailScreen({required this.activityId});
  final String activityId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(activityByIdProvider(activityId));

    return async.when(
      loading: () => const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      ),
      error: (e, st) => Scaffold(
        appBar: AppBar(
          leading: _BackButton(ref: ref),
        ),
        body: Center(
          child: Text('Error: $e',
              style: const TextStyle(color: IcsColors.accentRed)),
        ),
      ),
      data: (activity) {
        if (activity == null) {
          return Scaffold(
            appBar: AppBar(leading: _BackButton(ref: ref)),
            body: const Center(child: Text('Activity not found')),
          );
        }
        return _ActivityDetail(activity: activity, ref: ref);
      },
    );
  }
}

class _BackButton extends StatelessWidget {
  const _BackButton({required this.ref});
  final WidgetRef ref;

  @override
  Widget build(BuildContext context) {
    return IconButton(
      icon: const Icon(Icons.arrow_back),
      onPressed: () =>
          ref.read(selectedActivityIdProvider.notifier).state = null,
    );
  }
}

class _ActivityDetail extends StatelessWidget {
  const _ActivityDetail({required this.activity, required this.ref});
  final ActivityModel activity;
  final WidgetRef     ref;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: IcsColors.inkBg,
      appBar: AppBar(
        backgroundColor: IcsColors.stone1,
        leading: _BackButton(ref: ref),
        title: Text(
          activity.typeLabel,
          style: const TextStyle(fontSize: 14, color: IcsColors.textMuted),
        ),
        actions: [
          _StatusBadge(status: activity.status),
          const SizedBox(width: IcsSpacing.m),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(IcsSpacing.m),
        children: [
          _HeaderCard(activity: activity),
          const SizedBox(height: IcsSpacing.m),
          _DetailsCard(activity: activity),
          if (activity.isGathering) ...[
            const SizedBox(height: IcsSpacing.m),
            _GatheringCard(activity: activity, ref: ref),
          ],
          const SizedBox(height: IcsSpacing.m),
          _ActionBar(activity: activity, ref: ref),
          const SizedBox(height: IcsSpacing.xl),
        ],
      ),
    );
  }
}

// ── Header card ───────────────────────────────────────────────────────────────

class _HeaderCard extends StatelessWidget {
  const _HeaderCard({required this.activity});
  final ActivityModel activity;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(IcsSpacing.m),
      decoration: BoxDecoration(
        color: IcsColors.stone1,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: IcsColors.borderDark),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              _TypeDot(type: activity.activityType),
              const SizedBox(width: IcsSpacing.s),
              Text(
                activity.typeLabel.toUpperCase(),
                style: const TextStyle(
                    color: IcsColors.textMuted,
                    fontSize: 11,
                    letterSpacing: 1.2),
              ),
            ],
          ),
          const SizedBox(height: IcsSpacing.s),
          Text(
            activity.title,
            style: const TextStyle(
                color: Colors.white,
                fontSize: 20,
                fontWeight: FontWeight.w600),
          ),
          if (activity.description.isNotEmpty) ...[
            const SizedBox(height: IcsSpacing.s),
            Text(
              activity.description,
              style: const TextStyle(
                  color: IcsColors.textMuted, fontSize: 14),
            ),
          ],
          if (activity.progress > 0) ...[
            const SizedBox(height: IcsSpacing.m),
            Row(
              children: [
                Expanded(
                  child: LinearProgressIndicator(
                    value: activity.progress / 100,
                    backgroundColor: IcsColors.stone2,
                    valueColor: const AlwaysStoppedAnimation(
                        IcsColors.accentGreen),
                  ),
                ),
                const SizedBox(width: IcsSpacing.s),
                Text(
                  '${activity.progress}%',
                  style: const TextStyle(
                      color: IcsColors.textMuted, fontSize: 12),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }
}

// ── Details card ──────────────────────────────────────────────────────────────

class _DetailsCard extends StatelessWidget {
  const _DetailsCard({required this.activity});
  final ActivityModel activity;

  @override
  Widget build(BuildContext context) {
    final rows = <(String, String)>[];

    if (activity.scheduledAt != null && activity.scheduledAt!.isNotEmpty) {
      rows.add(('Scheduled', _fmtDateFull(activity.scheduledAt!)));
    }
    if (activity.dueAt != null && activity.dueAt!.isNotEmpty) {
      rows.add(('Due', _fmtDateFull(activity.dueAt!)));
    }
    if (activity.completedAt != null && activity.completedAt!.isNotEmpty) {
      rows.add(('Completed', _fmtDateFull(activity.completedAt!)));
    }
    if (activity.location != null) {
      rows.add(('Location', activity.location!));
    }
    if (activity.format != null) {
      rows.add(('Format', activity.format!));
    }
    if (activity.durationMinutes != null) {
      rows.add(('Duration', '${activity.durationMinutes} min'));
    }

    if (rows.isEmpty) return const SizedBox.shrink();

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
                        style: const TextStyle(
                            color: Colors.white, fontSize: 13)),
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

// ── Gathering card ────────────────────────────────────────────────────────────

class _GatheringCard extends ConsumerWidget {
  const _GatheringCard({required this.activity, required this.ref});
  final ActivityModel activity;
  final WidgetRef     ref;

  @override
  Widget build(BuildContext context, WidgetRef parentRef) {
    final countAsync = ref.watch(attendanceCountProvider(activity.id));

    return Container(
      padding: const EdgeInsets.all(IcsSpacing.m),
      decoration: BoxDecoration(
        color: IcsColors.stone1,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: IcsColors.borderDark),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.people_outline,
                  color: IcsColors.textMuted, size: 16),
              const SizedBox(width: IcsSpacing.s),
              const Text('Attendance',
                  style: TextStyle(
                      color: Colors.white,
                      fontWeight: FontWeight.w500)),
              const Spacer(),
              countAsync.maybeWhen(
                data: (n) => Text(
                  '$n attended',
                  style: const TextStyle(
                      color: IcsColors.accentBlue, fontSize: 13),
                ),
                orElse: () => const SizedBox.shrink(),
              ),
            ],
          ),
          const SizedBox(height: IcsSpacing.m),
          SizedBox(
            width: double.infinity,
            child: OutlinedButton.icon(
              icon: const Icon(Icons.how_to_reg_outlined, size: 16),
              label: const Text('Mark attendance'),
              onPressed: SyncEngine.instance.isLoaded ? () => _markAttendance(context) : null,
              style: OutlinedButton.styleFrom(
                foregroundColor: IcsColors.accentBlue,
                side: const BorderSide(color: IcsColors.accentBlue),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Future<void> _markAttendance(BuildContext context) async {
    final prefs    = await SharedPreferences.getInstance();
    final memberId = prefs.getString('ics_auth_email') ?? '';
    final payload  = jsonEncode({
      'activity_id': activity.id,
      'member_id':   memberId,
      'status':      'attendance',
    });
    SyncEngine.instance.attendanceSave(payload);
    ref.invalidate(attendanceCountProvider(activity.id));
  }
}

// ── Action bar ────────────────────────────────────────────────────────────────

class _ActionBar extends ConsumerStatefulWidget {
  const _ActionBar({required this.activity, required this.ref});
  final ActivityModel activity;
  final WidgetRef     ref;

  @override
  ConsumerState<_ActionBar> createState() => _ActionBarState();
}

class _ActionBarState extends ConsumerState<_ActionBar> {
  bool _completing = false;

  @override
  Widget build(BuildContext context) {
    final canComplete = !widget.activity.isCompleted &&
        SyncEngine.instance.isLoaded;

    return SizedBox(
      width: double.infinity,
      child: FilledButton(
        onPressed: canComplete && !_completing ? _markComplete : null,
        style: FilledButton.styleFrom(
          backgroundColor:
              widget.activity.isCompleted ? IcsColors.stone2 : IcsColors.accentGreen,
        ),
        child: _completing
            ? const SizedBox(
                width: 18,
                height: 18,
                child: CircularProgressIndicator(
                    strokeWidth: 2, color: Colors.white),
              )
            : Text(
                widget.activity.isCompleted ? 'Completed' : 'Mark complete',
                style: const TextStyle(color: Colors.white),
              ),
      ),
    );
  }

  Future<void> _markComplete() async {
    setState(() => _completing = true);
    final payload = jsonEncode({
      'id':     widget.activity.id,
      'status': 'completed',
    });
    SyncEngine.instance.activityCreate(payload);
    widget.ref.invalidate(activityByIdProvider(widget.activity.id));
    widget.ref.invalidate(activitiesProvider);
    setState(() => _completing = false);
  }
}

// ── Status badge ──────────────────────────────────────────────────────────────

class _StatusBadge extends StatelessWidget {
  const _StatusBadge({required this.status});
  final String status;

  @override
  Widget build(BuildContext context) {
    final color = switch (status) {
      'completed' => IcsColors.accentGreen,
      'cancelled' => IcsColors.accentRed,
      'active'    => IcsColors.accentBlue,
      'scheduled' => IcsColors.accentAmber,
      _           => IcsColors.textMuted,
    };
    return Container(
      padding:
          const EdgeInsets.symmetric(horizontal: IcsSpacing.s, vertical: 3),
      decoration: BoxDecoration(
        color: color.withAlpha(26),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: color.withAlpha(77)),
      ),
      child: Text(
        status.toUpperCase(),
        style: TextStyle(color: color, fontSize: 10, letterSpacing: 1),
      ),
    );
  }
}

// ── Helpers ───────────────────────────────────────────────────────────────────

String _fmtDate(String iso) {
  try {
    final dt = DateTime.parse(iso).toLocal();
    return DateFormat('MMM d, yyyy').format(dt);
  } catch (_) {
    return iso;
  }
}

String _fmtDateFull(String iso) {
  try {
    final dt = DateTime.parse(iso).toLocal();
    return DateFormat('EEE, MMM d yyyy · h:mm a').format(dt);
  } catch (_) {
    return iso;
  }
}


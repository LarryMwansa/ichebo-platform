import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/theme/tokens.dart';
import '../../shared/activity_list_tile.dart';
import '../../shared/activity_type_badge.dart';
import 'activity_form.dart';
import 'activity_providers.dart';

const _kFilterTypes = [
  null,           // All
  'gathering',
  'event',
  'task',
  'campaign',
  'goal',
  'habit',
];

const _kFilterLabels = {
  null:        'All',
  'gathering': 'Gathering',
  'event':     'Event',
  'task':      'Task',
  'campaign':  'Campaign',
  'goal':      'Goal',
  'habit':     'Habit',
};

class ActivityList extends ConsumerWidget {
  const ActivityList({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final filtered    = ref.watch(filteredActivitiesProvider);
    final search      = ref.watch(activitySearchProvider);
    final typeFilter  = ref.watch(activityFilterTypeProvider);
    final selectedId  = ref.watch(selectedActivityIdProvider);
    final isDark      = Theme.of(context).brightness == Brightness.dark;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        // ── Toolbar ──────────────────────────────────────────────────────
        Padding(
          padding: const EdgeInsets.fromLTRB(IcsSpacing.m, IcsSpacing.m, IcsSpacing.m, IcsSpacing.s),
          child: Row(
            children: [
              Expanded(
                child: _SearchBar(
                  value: search,
                  isDark: isDark,
                  onChanged: (v) => ref.read(activitySearchProvider.notifier).state = v,
                ),
              ),
              const SizedBox(width: IcsSpacing.s),
              _NewButton(isDark: isDark, typeFilter: typeFilter),
            ],
          ),
        ),
        // ── Type filter chips ────────────────────────────────────────────
        SizedBox(
          height: 32,
          child: ListView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: IcsSpacing.m),
            children: _kFilterTypes.map((t) => _TypeChip(
              type: t,
              selected: typeFilter == t,
              isDark: isDark,
              onTap: () => ref.read(activityFilterTypeProvider.notifier).state =
                  (typeFilter == t && t != null) ? null : t,
            )).toList(),
          ),
        ),
        const SizedBox(height: IcsSpacing.xs),
        Divider(height: 1, color: isDark ? IcsColors.borderDark : IcsColors.borderLight),
        // ── List ──────────────────────────────────────────────────────────
        Expanded(
          child: filtered.when(
            loading: () => const Center(child: CircularProgressIndicator()),
            error: (e, _) => Center(child: Text('Error: $e')),
            data: (activities) {
              if (activities.isEmpty) {
                return Center(
                  child: Text(
                    search.isNotEmpty ? 'No activities match "$search".' : 'No activities yet.',
                    style: TextStyle(fontSize: 13,
                        color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted),
                  ),
                );
              }
              return ListView.builder(
                itemCount: activities.length,
                itemBuilder: (context, i) {
                  final a = activities[i];
                  return Consumer(
                    builder: (context, ref, _) {
                      final countAsync = a.activityType == 'gathering'
                          ? ref.watch(attendanceCountProvider(a.id))
                          : null;
                      final count = countAsync?.maybeWhen(data: (c) => c, orElse: () => null);
                      return ActivityListTile(
                        activityType: a.activityType,
                        title: a.title,
                        status: a.status,
                        scheduledAt: a.scheduledAt,
                        dueAt: a.dueAt,
                        attendanceCount: count,
                        selected: a.id == selectedId,
                        onTap: () => ref.read(selectedActivityIdProvider.notifier).state = a.id,
                      );
                    },
                  );
                },
              );
            },
          ),
        ),
        // ── Footer count ─────────────────────────────────────────────────
        filtered.maybeWhen(
          data: (activities) => Container(
            height: 28,
            padding: const EdgeInsets.symmetric(horizontal: IcsSpacing.m),
            decoration: BoxDecoration(
              border: Border(
                top: BorderSide(color: isDark ? IcsColors.borderDark : IcsColors.borderLight),
              ),
            ),
            alignment: Alignment.centerLeft,
            child: Text(
              '${activities.length} ${activities.length == 1 ? 'activity' : 'activities'}',
              style: TextStyle(fontSize: 11,
                  color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted),
            ),
          ),
          orElse: () => const SizedBox.shrink(),
        ),
      ],
    );
  }
}

// ── Search bar ────────────────────────────────────────────────────────────────

class _SearchBar extends StatefulWidget {
  const _SearchBar({required this.value, required this.isDark, required this.onChanged});
  final String value;
  final bool isDark;
  final ValueChanged<String> onChanged;

  @override
  State<_SearchBar> createState() => _SearchBarState();
}

class _SearchBarState extends State<_SearchBar> {
  late final TextEditingController _ctrl;

  @override
  void initState() {
    super.initState();
    _ctrl = TextEditingController(text: widget.value);
  }

  @override
  void dispose() { _ctrl.dispose(); super.dispose(); }

  @override
  Widget build(BuildContext context) {
    return TextField(
      controller: _ctrl,
      onChanged: widget.onChanged,
      style: TextStyle(fontSize: 13, color: widget.isDark ? Colors.white : IcsColors.inkBg),
      decoration: InputDecoration(
        isDense: true,
        hintText: 'Search activities…',
        hintStyle: TextStyle(fontSize: 13,
            color: widget.isDark ? IcsColors.textMutedDark : IcsColors.textMuted),
        prefixIcon: Icon(Icons.search, size: 16,
            color: widget.isDark ? IcsColors.textMutedDark : IcsColors.textMuted),
        filled: true,
        fillColor: widget.isDark ? const Color(0xFF1A1A1A) : IcsColors.stone2,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(6),
          borderSide: BorderSide(color: widget.isDark ? IcsColors.borderDark : IcsColors.borderLight),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(6),
          borderSide: const BorderSide(color: IcsColors.accentRed, width: 1.5),
        ),
        contentPadding: const EdgeInsets.symmetric(horizontal: IcsSpacing.m, vertical: 8),
        suffixIcon: _ctrl.text.isNotEmpty
            ? IconButton(
                icon: const Icon(Icons.close, size: 14),
                onPressed: () { _ctrl.clear(); widget.onChanged(''); },
                color: widget.isDark ? IcsColors.textMutedDark : IcsColors.textMuted,
              )
            : null,
      ),
    );
  }
}

// ── New activity button ───────────────────────────────────────────────────────

class _NewButton extends ConsumerWidget {
  const _NewButton({required this.isDark, required this.typeFilter});
  final bool isDark;
  final String? typeFilter;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return ElevatedButton.icon(
      onPressed: () async {
        final result = await showDialog<bool>(
          context: context,
          builder: (_) => ActivityForm(
            mode: ActivityFormMode.add,
            initialType: typeFilter,
          ),
        );
        if (result == true) ref.invalidate(activitiesProvider);
      },
      icon: const Icon(Icons.add, size: 14),
      label: const Text('New activity'),
      style: ElevatedButton.styleFrom(
        backgroundColor: IcsColors.accentRed,
        foregroundColor: Colors.white,
        padding: const EdgeInsets.symmetric(horizontal: IcsSpacing.m, vertical: 8),
        textStyle: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
      ),
    );
  }
}

// ── Type filter chip ──────────────────────────────────────────────────────────

class _TypeChip extends StatelessWidget {
  const _TypeChip({
    required this.type,
    required this.selected,
    required this.isDark,
    required this.onTap,
  });

  final String? type;
  final bool selected;
  final bool isDark;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final label = _kFilterLabels[type] ?? 'Other';

    return GestureDetector(
      onTap: onTap,
      child: Container(
        margin: const EdgeInsets.only(right: IcsSpacing.xs),
        padding: const EdgeInsets.symmetric(horizontal: IcsSpacing.s, vertical: 4),
        decoration: BoxDecoration(
          color: selected
              ? IcsColors.accentRed
              : isDark ? const Color(0xFF1A1A1A) : IcsColors.stone2,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: selected
                ? IcsColors.accentRed
                : (isDark ? IcsColors.borderDark : IcsColors.borderLight),
          ),
        ),
        child: type != null && !selected
            ? ActivityTypeBadge(type: type!)
            : Text(
                label,
                style: TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w600,
                  color: selected
                      ? Colors.white
                      : (isDark ? IcsColors.textMutedDark : IcsColors.textMuted),
                ),
              ),
      ),
    );
  }
}

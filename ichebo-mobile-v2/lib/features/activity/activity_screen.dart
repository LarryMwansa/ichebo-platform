import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/api/api_client.dart';
import '../../core/api/providers.dart';
import '../../shared/tokens/tokens.dart';
import '../../shared/widgets/badges.dart';
import '../../shared/widgets/empty_state.dart';
import '../../shared/widgets/ichebo_app_bar.dart';
import '../../shared/widgets/ichebo_button.dart';
import '../../shared/widgets/ichebo_card.dart';

final _activityFilterProvider = StateProvider.autoDispose<String>((ref) => 'task');

const _activityTypes = [
  ('task', 'Tasks'),
  ('habit', 'Habits'),
  ('goal', 'Goals'),
  ('reminder', 'Reminders'),
  ('skill', 'Skills'),
];

class ActivityScreen extends ConsumerWidget {
  const ActivityScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final filter = ref.watch(_activityFilterProvider);

    return Scaffold(
      appBar: const IcheboAppBar(title: 'Activity', watermarkText: 'ACTIVITY'),
      body: Column(
        children: [
          _FilterChips(current: filter, onSelect: (t) => ref.read(_activityFilterProvider.notifier).state = t),
          Expanded(child: _ActivityList(filter: filter)),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => _showCreateSheet(context, ref, filter),
        backgroundColor: IcheboColors.primary,
        foregroundColor: Colors.white,
        child: const Icon(Icons.add),
      ),
    );
  }

  void _showCreateSheet(BuildContext context, WidgetRef ref, String currentType) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(borderRadius: IcheboRadius.xl2),
      builder: (_) => _CreateActivitySheet(initialType: currentType, ref: ref),
    );
  }
}

class _FilterChips extends StatelessWidget {
  const _FilterChips({required this.current, required this.onSelect});
  final String current;
  final ValueChanged<String> onSelect;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 48,
      child: ListView(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: IcheboSpacing.s, vertical: IcheboSpacing.xs3),
        children: _activityTypes.map((t) {
          final active = t.$1 == current;
          return Padding(
            padding: const EdgeInsets.only(right: IcheboSpacing.xs3),
            child: FilterChip(
              label: Text(t.$2),
              selected: active,
              onSelected: (_) => onSelect(t.$1),
              selectedColor: IcheboColors.primaryLight,
              labelStyle: IcheboTextStyles.labelLarge.copyWith(
                color: active ? IcheboColors.primary : IcheboColors.muted,
              ),
              checkmarkColor: IcheboColors.primary,
              side: BorderSide(
                color: active ? IcheboColors.primary : IcheboColors.lightBorder,
              ),
              shape: const StadiumBorder(),
              padding: const EdgeInsets.symmetric(horizontal: IcheboSpacing.xs3),
            ),
          );
        }).toList(),
      ),
    );
  }
}

class _ActivityList extends ConsumerWidget {
  const _ActivityList({required this.filter});
  final String filter;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final activitiesAsync = ref.watch(activitiesProvider({'activity_type': filter}));

    return activitiesAsync.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (e, _) => EmptyState(message: e.toString()),
      data: (activities) => activities.isEmpty
          ? EmptyState(
              icon: _iconFor(filter),
              message: 'No ${filter}s found.',
            )
          : ListView.builder(
              padding: const EdgeInsets.fromLTRB(
                IcheboSpacing.s, IcheboSpacing.xs3, IcheboSpacing.s, IcheboSpacing.xl),
              itemCount: activities.length,
              itemBuilder: (context, i) => Padding(
                padding: const EdgeInsets.only(bottom: IcheboSpacing.xs3),
                child: _ActivityCard(activity: activities[i]),
              ),
            ),
    );
  }

  IconData _iconFor(String type) {
    switch (type) {
      case 'habit': return Icons.loop;
      case 'goal': return Icons.flag_outlined;
      case 'reminder': return Icons.notifications_outlined;
      case 'skill': return Icons.star_outline;
      default: return Icons.check_circle_outline;
    }
  }
}

class _ActivityCard extends ConsumerWidget {
  const _ActivityCard({required this.activity});
  final ActivityItem activity;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final isComplete = activity.status == 'completed';

    return IcheboCard(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          GestureDetector(
            onTap: isComplete ? null : () => _markComplete(context, ref),
            child: Padding(
              padding: const EdgeInsets.only(right: IcheboSpacing.xs, top: 2),
              child: Icon(
                isComplete ? Icons.check_circle : Icons.radio_button_unchecked,
                size: 20,
                color: isComplete ? IcheboColors.success : IcheboColors.mutedLight,
              ),
            ),
          ),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  activity.title,
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        decoration: isComplete ? TextDecoration.lineThrough : null,
                        color: isComplete ? IcheboColors.muted : null,
                      ),
                ),
                if (activity.description != null && activity.description!.isNotEmpty)
                  Padding(
                    padding: const EdgeInsets.only(top: IcheboSpacing.xs3),
                    child: Text(
                      activity.description!,
                      style: Theme.of(context).textTheme.bodySmall,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                if (activity.dueAt != null)
                  Padding(
                    padding: const EdgeInsets.only(top: IcheboSpacing.xs3),
                    child: Row(
                      children: [
                        const Icon(Icons.schedule, size: 12, color: IcheboColors.muted),
                        const SizedBox(width: 4),
                        Text(
                          _formatDate(activity.dueAt!),
                          style: Theme.of(context).textTheme.bodySmall,
                        ),
                      ],
                    ),
                  ),
              ],
            ),
          ),
          _statusBadge(activity.status),
        ],
      ),
    );
  }

  Widget _statusBadge(String status) {
    switch (status) {
      case 'completed': return const StatusBadge(label: 'Done', variant: StatusVariant.success);
      case 'in_progress': return const StatusBadge(label: 'Active', variant: StatusVariant.active);
      case 'deferred': return const StatusBadge(label: 'Deferred', variant: StatusVariant.warning);
      case 'cancelled': return const StatusBadge(label: 'Cancelled', variant: StatusVariant.danger);
      default: return const StatusBadge(label: 'Pending', variant: StatusVariant.muted);
    }
  }

  String _formatDate(String iso) {
    try {
      final dt = DateTime.parse(iso).toLocal();
      return '${dt.day}/${dt.month}/${dt.year}';
    } catch (_) {
      return iso;
    }
  }

  Future<void> _markComplete(BuildContext context, WidgetRef ref) async {
    final client = ref.read(apiClientProvider);
    try {
      await client.patch<void>('activities/${activity.id}/', data: {'status': 'completed'});
      ref.invalidate(activitiesProvider);
    } catch (_) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Could not update. Please try again.')),
        );
      }
    }
  }
}

// ── Create activity bottom sheet ──────────────────────────────────────────────

class _CreateActivitySheet extends StatefulWidget {
  const _CreateActivitySheet({required this.initialType, required this.ref});
  final String initialType;
  final WidgetRef ref;

  @override
  State<_CreateActivitySheet> createState() => _CreateActivitySheetState();
}

class _CreateActivitySheetState extends State<_CreateActivitySheet> {
  final _titleCtrl = TextEditingController();
  final _descCtrl = TextEditingController();
  final _form = GlobalKey<FormState>();
  late String _type;
  DateTime? _dueAt;
  bool _saving = false;

  static const _typeOptions = [
    ('task', 'Task'),
    ('habit', 'Habit'),
    ('goal', 'Goal'),
    ('reminder', 'Reminder'),
  ];

  @override
  void initState() {
    super.initState();
    // Habits and reminders are valid create types; fall back to task otherwise.
    _type = _typeOptions.any((t) => t.$1 == widget.initialType)
        ? widget.initialType
        : 'task';
  }

  @override
  void dispose() {
    _titleCtrl.dispose();
    _descCtrl.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    if (!_form.currentState!.validate()) return;
    setState(() => _saving = true);
    final data = <String, dynamic>{
      'title': _titleCtrl.text.trim(),
      'activity_type': _type,
      if (_descCtrl.text.trim().isNotEmpty) 'description': _descCtrl.text.trim(),
      if (_dueAt != null) 'due_at': _dueAt!.toUtc().toIso8601String(),
    };
    try {
      await widget.ref.read(apiClientProvider).post<void>('activities/', data: data);
      widget.ref.invalidate(activitiesProvider);
      if (mounted) Navigator.pop(context);
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Could not create. Please try again.')),
        );
      }
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  Future<void> _pickDate() async {
    final now = DateTime.now();
    final picked = await showDatePicker(
      context: context,
      initialDate: _dueAt ?? now,
      firstDate: now,
      lastDate: now.add(const Duration(days: 365 * 3)),
    );
    if (picked != null) setState(() => _dueAt = picked);
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(
        left: IcheboSpacing.s,
        right: IcheboSpacing.s,
        top: IcheboSpacing.s,
        bottom: MediaQuery.of(context).viewInsets.bottom + IcheboSpacing.m,
      ),
      child: Form(
        key: _form,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // ── Header ────────────────────────────────────────────────────
            Row(
              children: [
                Expanded(
                  child: Text('New activity',
                      style: IcheboTextStyles.titleLarge),
                ),
                IconButton(
                  icon: const Icon(Icons.close),
                  onPressed: () => Navigator.pop(context),
                ),
              ],
            ),
            const SizedBox(height: IcheboSpacing.xs),

            // ── Type chips ────────────────────────────────────────────────
            SizedBox(
              height: 40,
              child: ListView(
                scrollDirection: Axis.horizontal,
                children: _typeOptions.map((t) {
                  final active = t.$1 == _type;
                  return Padding(
                    padding: const EdgeInsets.only(right: IcheboSpacing.xs3),
                    child: FilterChip(
                      label: Text(t.$2),
                      selected: active,
                      onSelected: (_) => setState(() => _type = t.$1),
                      selectedColor: IcheboColors.primaryLight,
                      labelStyle: IcheboTextStyles.labelLarge.copyWith(
                        color: active ? IcheboColors.primary : IcheboColors.muted,
                        fontSize: 13,
                      ),
                      checkmarkColor: IcheboColors.primary,
                      side: BorderSide(
                        color: active ? IcheboColors.primary : IcheboColors.lightBorder,
                      ),
                      shape: const StadiumBorder(),
                      padding: const EdgeInsets.symmetric(horizontal: IcheboSpacing.xs3),
                    ),
                  );
                }).toList(),
              ),
            ),
            const SizedBox(height: IcheboSpacing.xs),

            // ── Title ─────────────────────────────────────────────────────
            TextFormField(
              controller: _titleCtrl,
              textInputAction: TextInputAction.next,
              decoration: const InputDecoration(
                labelText: 'Title',
                border: OutlineInputBorder(borderRadius: IcheboRadius.m),
              ),
              validator: (v) =>
                  (v == null || v.trim().isEmpty) ? 'Title is required' : null,
            ),
            const SizedBox(height: IcheboSpacing.xs),

            // ── Description ───────────────────────────────────────────────
            TextFormField(
              controller: _descCtrl,
              textInputAction: TextInputAction.newline,
              maxLines: 2,
              decoration: const InputDecoration(
                labelText: 'Description (optional)',
                border: OutlineInputBorder(borderRadius: IcheboRadius.m),
              ),
            ),
            const SizedBox(height: IcheboSpacing.xs),

            // ── Due date ──────────────────────────────────────────────────
            InkWell(
              onTap: _pickDate,
              borderRadius: IcheboRadius.m,
              child: InputDecorator(
                decoration: InputDecoration(
                  labelText: 'Due date (optional)',
                  border: const OutlineInputBorder(borderRadius: IcheboRadius.m),
                  suffixIcon: _dueAt != null
                      ? IconButton(
                          icon: const Icon(Icons.clear, size: 18),
                          onPressed: () => setState(() => _dueAt = null),
                        )
                      : const Icon(Icons.calendar_today_outlined, size: 18),
                ),
                child: Text(
                  _dueAt != null
                      ? '${_dueAt!.day}/${_dueAt!.month}/${_dueAt!.year}'
                      : 'No due date',
                  style: _dueAt != null
                      ? IcheboTextStyles.bodyMedium
                      : IcheboTextStyles.bodyMedium.copyWith(
                          color: IcheboColors.mutedLight),
                ),
              ),
            ),
            const SizedBox(height: IcheboSpacing.s),

            // ── Save ──────────────────────────────────────────────────────
            IcheboButton(label: 'Create', onPressed: _save, loading: _saving),
          ],
        ),
      ),
    );
  }
}

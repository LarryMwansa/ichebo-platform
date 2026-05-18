import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/api/api_client.dart';
import '../../core/api/providers.dart';
import '../../shared/tokens/tokens.dart';
import '../../shared/widgets/badges.dart';
import '../../shared/widgets/empty_state.dart';
import '../../shared/widgets/ichebo_app_bar.dart';
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

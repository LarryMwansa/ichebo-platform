import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/api/providers.dart';
import '../../core/auth/auth_provider.dart';
import '../../shared/tokens/tokens.dart';
import '../../shared/widgets/badges.dart';
import '../../shared/widgets/empty_state.dart';
import '../../shared/widgets/ichebo_app_bar.dart';
import '../../shared/widgets/ichebo_card.dart';
import '../../shared/widgets/progress_bar.dart';

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(currentUserProvider);
    final digestAsync = ref.watch(paracleteDigestProvider);

    return Scaffold(
      appBar: IcheboAppBar(
        title: 'Ichebo',
        subtitle: user != null ? 'Peace, ${user.displayName.split(' ').first}' : null,
        watermarkText: 'HOME',
      ),
      body: digestAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => EmptyState(
          icon: Icons.cloud_off_outlined,
          message: e.toString(),
        ),
        data: (digest) => _HomeBody(digest: digest, user: user),
      ),
    );
  }
}

class _HomeBody extends StatelessWidget {
  const _HomeBody({required this.digest, required this.user});

  final ParacleteDigest digest;
  final dynamic user;

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(IcheboSpacing.s),
      children: [
        // ── Formation card ──────────────────────────────────────────────
        if (user != null)
          IcheboCard(
            accent: true,
            child: Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const LabelTag(label: 'Formation'),
                      const SizedBox(height: IcheboSpacing.xs3),
                      Text(
                        user.displayName as String,
                        style: Theme.of(context).textTheme.titleLarge,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ],
                  ),
                ),
                LevelBadge(level: user.competenceLevel as int),
              ],
            ),
          ),

        const SizedBox(height: IcheboSpacing.s),

        // ── Paraclete intelligence ──────────────────────────────────────
        IcheboCardDark(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const LabelTag(label: 'Paraclete'),
              const SizedBox(height: IcheboSpacing.xs),
              Text(
                digest.disciplinePrompt.isNotEmpty
                    ? digest.disciplinePrompt
                    : 'No prompt available today.',
                style: IcheboTextStyles.bodyMedium.copyWith(
                  color: IcheboColors.stone.withValues(alpha: 0.85),
                ),
              ),
              if (digest.promptPathway.isNotEmpty) ...[
                const SizedBox(height: IcheboSpacing.xs3),
                Text(
                  digest.promptPathway.toUpperCase().replaceAll('_', ' '),
                  style: IcheboTextStyles.labelCaps.copyWith(
                    color: IcheboColors.primary,
                    fontSize: 10,
                  ),
                ),
              ],
            ],
          ),
        ),

        const SizedBox(height: IcheboSpacing.s),

        // ── Stats row ───────────────────────────────────────────────────
        Row(
          children: [
            Expanded(
              child: _StatCard(
                label: 'Due today',
                value: digest.dueToday.length.toString(),
                color: digest.dueToday.isEmpty
                    ? IcheboColors.success
                    : IcheboColors.warning,
              ),
            ),
            const SizedBox(width: IcheboSpacing.xs),
            Expanded(
              child: _StatCard(
                label: 'Overdue',
                value: digest.overdueCount.toString(),
                color: digest.overdueCount == 0
                    ? IcheboColors.success
                    : IcheboColors.error,
              ),
            ),
            if (digest.teamPendingCount != null) ...[
              const SizedBox(width: IcheboSpacing.xs),
              Expanded(
                child: _StatCard(
                  label: 'Team pending',
                  value: digest.teamPendingCount.toString(),
                  color: IcheboColors.secondary,
                ),
              ),
            ],
          ],
        ),

        // ── Active enrolments ───────────────────────────────────────────
        if (digest.activeEnrolments.isNotEmpty) ...[
          const SizedBox(height: IcheboSpacing.m),
          const LabelTag(label: 'Formation Programmes'),
          const SizedBox(height: IcheboSpacing.xs),
          ...digest.activeEnrolments.map(
            (p) => Padding(
              padding: const EdgeInsets.only(bottom: IcheboSpacing.xs),
              child: IcheboCard(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(p.title,
                        style: Theme.of(context).textTheme.titleMedium),
                    const SizedBox(height: IcheboSpacing.xs),
                    IcheboProgressBar(
                      value: p.progress / 100,
                      label: 'Progress',
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],

        // ── Next lesson ─────────────────────────────────────────────────
        if (digest.nextLesson != null) ...[
          const SizedBox(height: IcheboSpacing.m),
          const LabelTag(label: 'Next Lesson'),
          const SizedBox(height: IcheboSpacing.xs),
          IcheboCard(
            accent: true,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  digest.nextLesson!.programmeTitle,
                  style: Theme.of(context)
                      .textTheme
                      .bodySmall
                      ?.copyWith(color: IcheboColors.muted),
                ),
                Text(
                  digest.nextLesson!.title,
                  style: Theme.of(context).textTheme.titleMedium,
                ),
              ],
            ),
          ),
        ],

        // ── Due today ───────────────────────────────────────────────────
        if (digest.dueToday.isNotEmpty) ...[
          const SizedBox(height: IcheboSpacing.m),
          const LabelTag(label: 'Due Today'),
          const SizedBox(height: IcheboSpacing.xs),
          ...digest.dueToday.map((a) => _ActivityRow(activity: a)),
        ],

        // ── Habits ──────────────────────────────────────────────────────
        if (digest.habitStreaks.isNotEmpty) ...[
          const SizedBox(height: IcheboSpacing.m),
          const LabelTag(label: 'Habit Streaks'),
          const SizedBox(height: IcheboSpacing.xs),
          ...digest.habitStreaks.map(
            (h) => Padding(
              padding: const EdgeInsets.only(bottom: IcheboSpacing.xs3),
              child: Row(
                children: [
                  const Icon(Icons.local_fire_department,
                      size: 16, color: IcheboColors.warning),
                  const SizedBox(width: IcheboSpacing.xs3),
                  Expanded(
                    child: Text(h.title,
                        style: Theme.of(context).textTheme.bodyMedium),
                  ),
                  Text(
                    '${h.streak}d',
                    style: IcheboTextStyles.labelLarge
                        .copyWith(color: IcheboColors.warning),
                  ),
                ],
              ),
            ),
          ),
        ],

        const SizedBox(height: IcheboSpacing.xl),
      ],
    );
  }
}

class _StatCard extends StatelessWidget {
  const _StatCard({required this.label, required this.value, required this.color});
  final String label;
  final String value;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return IcheboCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            value,
            style: IcheboTextStyles.displaySmall.copyWith(color: color),
          ),
          Text(
            label,
            style: Theme.of(context).textTheme.bodySmall,
          ),
        ],
      ),
    );
  }
}

class _ActivityRow extends StatelessWidget {
  const _ActivityRow({required this.activity});
  final ActivityCard activity;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: IcheboSpacing.xs3),
      child: Row(
        children: [
          Icon(
            _iconFor(activity.activityType),
            size: 16,
            color: IcheboColors.muted,
          ),
          const SizedBox(width: IcheboSpacing.xs3),
          Expanded(
            child: Text(
              activity.title,
              style: Theme.of(context).textTheme.bodyMedium,
              overflow: TextOverflow.ellipsis,
            ),
          ),
          StatusBadge(
            label: activity.status,
            variant: activity.status == 'completed'
                ? StatusVariant.success
                : activity.status == 'in_progress'
                    ? StatusVariant.active
                    : StatusVariant.muted,
          ),
        ],
      ),
    );
  }

  IconData _iconFor(String type) {
    switch (type) {
      case 'habit': return Icons.loop;
      case 'goal': return Icons.flag_outlined;
      case 'event': return Icons.event_outlined;
      case 'reminder': return Icons.notifications_outlined;
      default: return Icons.check_circle_outline;
    }
  }
}

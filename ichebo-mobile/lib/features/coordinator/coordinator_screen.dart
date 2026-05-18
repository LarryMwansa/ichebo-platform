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

final _coordTabProvider = StateProvider.autoDispose<int>((ref) => 0);

class CoordinatorScreen extends ConsumerWidget {
  const CoordinatorScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final tab = ref.watch(_coordTabProvider);

    return Scaffold(
      appBar: const IcheboAppBar(
          title: 'Coordinator', watermarkText: 'COORDINATOR'),
      body: Column(
        children: [
          _CoordTabRow(
            currentTab: tab,
            onTab: (i) => ref.read(_coordTabProvider.notifier).state = i,
          ),
          Expanded(
            child: switch (tab) {
              0 => const _CertificationQueue(),
              1 => const _InductionQueue(),
              _ => const _MemberRoster(),
            },
          ),
        ],
      ),
    );
  }
}

// ── Tab row ───────────────────────────────────────────────────────────────────

class _CoordTabRow extends StatelessWidget {
  const _CoordTabRow({required this.currentTab, required this.onTab});
  final int currentTab;
  final ValueChanged<int> onTab;

  @override
  Widget build(BuildContext context) {
    const labels = ['Certifications', 'Induction', 'Members'];
    return Container(
      color: Theme.of(context).colorScheme.surface,
      padding: const EdgeInsets.symmetric(
        horizontal: IcheboSpacing.s,
        vertical: IcheboSpacing.xs3,
      ),
      child: Row(
        children: List.generate(labels.length, (i) {
          final active = i == currentTab;
          return Padding(
            padding: const EdgeInsets.only(right: IcheboSpacing.xs),
            child: GestureDetector(
              onTap: () => onTab(i),
              child: Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: IcheboSpacing.xs,
                  vertical: IcheboSpacing.xs3,
                ),
                decoration: BoxDecoration(
                  border: active
                      ? const Border(
                          bottom: BorderSide(
                              color: IcheboColors.primary, width: 2))
                      : null,
                ),
                child: Text(
                  labels[i],
                  style: IcheboTextStyles.labelLarge.copyWith(
                    color: active ? IcheboColors.primary : IcheboColors.muted,
                  ),
                ),
              ),
            ),
          );
        }),
      ),
    );
  }
}

// ── Certification queue ───────────────────────────────────────────────────────

class _CertificationQueue extends ConsumerWidget {
  const _CertificationQueue();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final queueAsync = ref.watch(certificationQueueProvider);

    return queueAsync.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (e, _) => EmptyState(message: e.toString()),
      data: (items) {
        final pending = items.where((i) => i.status == 'pending').toList();
        return pending.isEmpty
            ? const EmptyState(
                icon: Icons.verified_outlined,
                message: 'No certifications pending review.',
              )
            : ListView.builder(
                padding: const EdgeInsets.all(IcheboSpacing.s),
                itemCount: pending.length,
                itemBuilder: (context, i) => Padding(
                  padding: const EdgeInsets.only(bottom: IcheboSpacing.xs),
                  child: _CertCard(item: pending[i]),
                ),
              );
      },
    );
  }
}

class _CertCard extends ConsumerWidget {
  const _CertCard({required this.item});
  final CertificationQueueItem item;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return IcheboCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(item.candidateName,
                        style: Theme.of(context).textTheme.titleMedium),
                    Text(item.candidateEmail,
                        style: IcheboTextStyles.bodySmall
                            .copyWith(color: IcheboColors.muted)),
                  ],
                ),
              ),
              LevelBadge(level: item.currentLevel, showLabel: false),
              const Icon(Icons.arrow_forward,
                  size: 14, color: IcheboColors.mutedLight),
              LevelBadge(level: item.targetLevel, showLabel: false),
            ],
          ),
          const SizedBox(height: IcheboSpacing.xs3),
          LabelTag(label: item.programmeName),
          const SizedBox(height: IcheboSpacing.xs),
          Row(
            children: [
              Expanded(
                child: IcheboButton(
                  label: 'Approve',
                  icon: Icons.check,
                  onPressed: () => _review(context, ref, 'confirm'),
                  variant: IcheboButtonVariant.primary,
                ),
              ),
              const SizedBox(width: IcheboSpacing.xs),
              Expanded(
                child: IcheboButton(
                  label: 'Decline',
                  icon: Icons.close,
                  onPressed: () => _review(context, ref, 'decline'),
                  variant: IcheboButtonVariant.danger,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Future<void> _review(
      BuildContext context, WidgetRef ref, String action) async {
    try {
      await ref.read(apiClientProvider).post<void>(
        'learn/certifications/${item.id}/$action/',
        data: {},
      );
      ref.invalidate(certificationQueueProvider);
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
              content: Text(action == 'confirm' ? 'Certification approved.' : 'Certification declined.')),
        );
      }
    } catch (_) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Action failed. Please try again.')),
        );
      }
    }
  }
}

// ── Induction queue ───────────────────────────────────────────────────────────

class _InductionQueue extends ConsumerWidget {
  const _InductionQueue();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final queueAsync = ref.watch(inductionQueueProvider);

    return queueAsync.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (e, _) => EmptyState(message: e.toString()),
      data: (items) {
        final pending = items.where((i) => i.status == 'pending').toList();
        return pending.isEmpty
            ? const EmptyState(
                icon: Icons.how_to_reg_outlined,
                message: 'No induction requests pending.',
              )
            : ListView.builder(
                padding: const EdgeInsets.all(IcheboSpacing.s),
                itemCount: pending.length,
                itemBuilder: (context, i) => Padding(
                  padding: const EdgeInsets.only(bottom: IcheboSpacing.xs),
                  child: _InductionCard(item: pending[i]),
                ),
              );
      },
    );
  }
}

class _InductionCard extends ConsumerWidget {
  const _InductionCard({required this.item});
  final InductionQueueItem item;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return IcheboCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(item.applicantName,
              style: Theme.of(context).textTheme.titleMedium),
          Text(item.applicantEmail,
              style:
                  IcheboTextStyles.bodySmall.copyWith(color: IcheboColors.muted)),
          if (item.note != null && item.note!.isNotEmpty) ...[
            const SizedBox(height: IcheboSpacing.xs3),
            Text(item.note!,
                style: Theme.of(context).textTheme.bodySmall,
                maxLines: 2,
                overflow: TextOverflow.ellipsis),
          ],
          const SizedBox(height: IcheboSpacing.xs),
          Row(
            children: [
              Expanded(
                child: IcheboButton(
                  label: 'Accept',
                  icon: Icons.check,
                  onPressed: () => _respond(context, ref, 'approve'),
                  variant: IcheboButtonVariant.primary,
                ),
              ),
              const SizedBox(width: IcheboSpacing.xs),
              Expanded(
                child: IcheboButton(
                  label: 'Decline',
                  icon: Icons.close,
                  onPressed: () => _respond(context, ref, 'decline'),
                  variant: IcheboButtonVariant.danger,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Future<void> _respond(
      BuildContext context, WidgetRef ref, String action) async {
    try {
      await ref.read(apiClientProvider).post<void>(
        'community/membership-requests/${item.id}/$action/',
        data: {},
      );
      ref.invalidate(inductionQueueProvider);
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
              content: Text(action == 'approve'
                  ? 'Request accepted.'
                  : 'Request declined.')),
        );
      }
    } catch (_) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Action failed. Please try again.')),
        );
      }
    }
  }
}

// ── Member roster ─────────────────────────────────────────────────────────────

class _MemberRoster extends ConsumerWidget {
  const _MemberRoster();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final membersAsync = ref.watch(communityMembersProvider({'page_size': '100'}));

    return membersAsync.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (e, _) => EmptyState(message: e.toString()),
      data: (page) => page.results.isEmpty
          ? const EmptyState(
              icon: Icons.people_outline,
              message: 'No members yet.',
            )
          : ListView.builder(
              padding: const EdgeInsets.all(IcheboSpacing.s),
              itemCount: page.results.length,
              itemBuilder: (context, i) {
                final m = page.results[i];
                return ListTile(
                  leading: CircleAvatar(
                    radius: 18,
                    backgroundColor:
                        IcheboColors.forLevel(m.competenceLevel).withValues(alpha: 0.15),
                    child: Text(
                      m.displayName.isNotEmpty ? m.displayName[0].toUpperCase() : '?',
                      style: IcheboTextStyles.labelLarge.copyWith(
                          color: IcheboColors.forLevel(m.competenceLevel),
                          fontSize: 13),
                    ),
                  ),
                  title: Text(m.displayName),
                  subtitle: Text(m.role.replaceAll('-', ' ')),
                  trailing: LevelBadge(level: m.competenceLevel, showLabel: false),
                  contentPadding: const EdgeInsets.symmetric(
                    horizontal: 0,
                    vertical: IcheboSpacing.xs3,
                  ),
                );
              },
            ),
    );
  }
}

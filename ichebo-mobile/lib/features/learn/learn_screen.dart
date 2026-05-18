import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/api/api_client.dart';
import '../../core/api/providers.dart';
import '../../core/auth/auth_provider.dart';
import '../../shared/tokens/tokens.dart';
import '../../shared/widgets/badges.dart';
import '../../shared/widgets/empty_state.dart';
import '../../shared/widgets/ichebo_app_bar.dart';
import '../../shared/widgets/ichebo_button.dart';
import '../../shared/widgets/ichebo_card.dart';
import '../../shared/widgets/progress_bar.dart';
import 'lesson_screen.dart';

final _learnTabProvider = StateProvider.autoDispose<int>((ref) => 0);

class LearnScreen extends ConsumerWidget {
  const LearnScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final tab = ref.watch(_learnTabProvider);

    return Scaffold(
      appBar: const IcheboAppBar(title: 'Learn', watermarkText: 'FORMATION'),
      body: Column(
        children: [
          _TabRow(currentTab: tab, onTab: (i) => ref.read(_learnTabProvider.notifier).state = i),
          Expanded(child: tab == 0 ? const _MyLearning() : const _Catalogue()),
        ],
      ),
    );
  }
}

class _TabRow extends StatelessWidget {
  const _TabRow({required this.currentTab, required this.onTab});
  final int currentTab;
  final ValueChanged<int> onTab;

  @override
  Widget build(BuildContext context) {
    return Container(
      color: Theme.of(context).colorScheme.surface,
      padding: const EdgeInsets.symmetric(
        horizontal: IcheboSpacing.s,
        vertical: IcheboSpacing.xs3,
      ),
      child: Row(
        children: [
          _Tab(label: 'My Learning', active: currentTab == 0, onTap: () => onTab(0)),
          const SizedBox(width: IcheboSpacing.xs),
          _Tab(label: 'Catalogue', active: currentTab == 1, onTap: () => onTab(1)),
        ],
      ),
    );
  }
}

class _Tab extends StatelessWidget {
  const _Tab({required this.label, required this.active, required this.onTap});
  final String label;
  final bool active;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(
          horizontal: IcheboSpacing.s,
          vertical: IcheboSpacing.xs3,
        ),
        decoration: BoxDecoration(
          border: active
              ? const Border(bottom: BorderSide(color: IcheboColors.primary, width: 2))
              : null,
        ),
        child: Text(
          label,
          style: IcheboTextStyles.labelLarge.copyWith(
            color: active ? IcheboColors.primary : IcheboColors.muted,
          ),
        ),
      ),
    );
  }
}

// ── My Learning (enrolments) ──────────────────────────────────────────────────

class _MyLearning extends ConsumerWidget {
  const _MyLearning();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final enrolmentsAsync = ref.watch(myEnrolmentsProvider);

    return enrolmentsAsync.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (e, _) => EmptyState(message: e.toString()),
      data: (enrolments) => enrolments.isEmpty
          ? const EmptyState(
              icon: Icons.school_outlined,
              message: 'No active enrolments.\nBrowse the Catalogue to begin.',
            )
          : ListView.builder(
              padding: const EdgeInsets.all(IcheboSpacing.s),
              itemCount: enrolments.length,
              itemBuilder: (context, i) => Padding(
                padding: const EdgeInsets.only(bottom: IcheboSpacing.xs),
                child: _ProgrammeCard(programme: enrolments[i], showEnrolButton: false),
              ),
            ),
    );
  }
}

// ── Catalogue ─────────────────────────────────────────────────────────────────

class _Catalogue extends ConsumerWidget {
  const _Catalogue();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final programmesAsync = ref.watch(programmesProvider);
    final user = ref.watch(currentUserProvider);

    return programmesAsync.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (e, _) => EmptyState(message: e.toString()),
      data: (programmes) => programmes.isEmpty
          ? const EmptyState(message: 'No programmes available.')
          : ListView.builder(
              padding: const EdgeInsets.all(IcheboSpacing.s),
              itemCount: programmes.length,
              itemBuilder: (context, i) {
                final p = programmes[i];
                final locked = !p.accessible &&
                    (user?.competenceLevel ?? 0) < p.requiredLevel;
                return Padding(
                  padding: const EdgeInsets.only(bottom: IcheboSpacing.xs),
                  child: Opacity(
                    opacity: locked ? 0.55 : 1.0,
                    child: _ProgrammeCard(programme: p, showEnrolButton: !p.enrolled && p.accessible),
                  ),
                );
              },
            ),
    );
  }
}

// ── Programme card ────────────────────────────────────────────────────────────

class _ProgrammeCard extends ConsumerWidget {
  const _ProgrammeCard({required this.programme, required this.showEnrolButton});
  final Programme programme;
  final bool showEnrolButton;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return IcheboCard(
      accent: programme.enrolled,
      child: InkWell(
        onTap: programme.enrolled
            ? () => Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (_) => LessonScreen(programmeId: programme.id),
                  ),
                )
            : null,
        borderRadius: IcheboRadius.l,
        child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  programme.title,
                  style: Theme.of(context).textTheme.titleMedium,
                ),
              ),
              if (programme.enrolled)
                const StatusBadge(label: 'Enrolled', variant: StatusVariant.active),
              if (!programme.accessible)
                StatusBadge(
                  label: 'Level ${programme.requiredLevel}+',
                  variant: StatusVariant.muted,
                ),
            ],
          ),
          if (programme.summary != null && programme.summary!.isNotEmpty) ...[
            const SizedBox(height: IcheboSpacing.xs3),
            Text(
              programme.summary!,
              style: Theme.of(context).textTheme.bodySmall,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
          ],
          if (programme.kgsQualification != null && programme.kgsQualification!.isNotEmpty) ...[
            const SizedBox(height: IcheboSpacing.xs3),
            LabelTag(label: programme.kgsQualification!),
          ],
          if (programme.enrolled) ...[
            const SizedBox(height: IcheboSpacing.xs),
            const IcheboProgressBar(value: 0, label: 'Progress'),
          ],
          if (showEnrolButton) ...[
            const SizedBox(height: IcheboSpacing.xs),
            IcheboButton(
              label: 'Enrol',
              onPressed: () => _enrol(context, ref),
              variant: IcheboButtonVariant.secondary,
              expand: false,
            ),
          ],
        ],
        ),
      ),
    );
  }

  Future<void> _enrol(BuildContext context, WidgetRef ref) async {
    final client = ref.read(
      // ignore: avoid_manual_providers_as_generated_provider_dependency
      apiClientProvider,
    );
    try {
      await client.post<void>(
        'learn/programmes/${programme.id}/enrol/',
        data: {},
      );
      ref.invalidate(programmesProvider);
      ref.invalidate(myEnrolmentsProvider);
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Enrolled successfully.')),
        );
      }
    } catch (_) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Could not enrol. Please try again.')),
        );
      }
    }
  }
}

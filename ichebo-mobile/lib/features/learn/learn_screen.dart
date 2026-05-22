import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/api/providers.dart';
import '../../core/theme/tokens.dart';
import 'learn_providers.dart';

class LearnScreen extends ConsumerWidget {
  const LearnScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final selectedId = ref.watch(selectedProgrammeIdProvider);
    if (selectedId != null) {
      return _ProgrammeDetailScreen(programmeId: selectedId);
    }
    return DefaultTabController(length: 2, child: const _LearnHome());
  }
}

// ── Home: tabs for Catalogue and My Programmes ────────────────────────────────

class _LearnHome extends ConsumerWidget {
  const _LearnHome();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final tab = ref.watch(learnTabProvider);

    return Scaffold(
      backgroundColor: IcsColors.inkBg,
      appBar: AppBar(
        backgroundColor: IcsColors.stone1,
        title: const Text('Learn'),
        bottom: TabBar(
          controller: _tabController(context, ref, tab),
          indicatorColor: IcsColors.accentBlue,
          labelColor: IcsColors.accentBlue,
          unselectedLabelColor: IcsColors.textMuted,
          tabs: const [
            Tab(text: 'Catalogue'),
            Tab(text: 'My Programmes'),
          ],
        ),
      ),
      body: tab == 0
          ? const _CatalogueView()
          : const _MyProgrammesView(),
    );
  }

  TabController _tabController(
      BuildContext context, WidgetRef ref, int tab) {
    // DefaultTabController is provided by the parent; we drive selection via
    // learnTabProvider so back-navigation preserves the selected tab.
    final ctrl = DefaultTabController.of(context);
    if (ctrl.index != tab) {
      WidgetsBinding.instance
          .addPostFrameCallback((_) => ctrl.animateTo(tab));
    }
    ctrl.addListener(() {
      if (ctrl.indexIsChanging) return;
      ref.read(learnTabProvider.notifier).state = ctrl.index;
    });
    return ctrl;
  }
}

// ── Catalogue view ────────────────────────────────────────────────────────────

class _CatalogueView extends ConsumerWidget {
  const _CatalogueView();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final programmes = ref.watch(programmesProvider);

    return programmes.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (e, st) => _ErrorView(message: e.toString()),
      data: (list) {
        if (list.isEmpty) {
          return const Center(
            child: Text('No programmes available',
                style: TextStyle(color: IcsColors.textMuted)),
          );
        }
        return RefreshIndicator(
          onRefresh: () async => ref.invalidate(programmesProvider),
          child: ListView.separated(
            padding: const EdgeInsets.all(IcsSpacing.m),
            itemCount: list.length,
            separatorBuilder: (_, i) => const SizedBox(height: IcsSpacing.s),
            itemBuilder: (_, i) => _ProgrammeTile(
              programme: list[i],
              onTap: () => ref
                  .read(selectedProgrammeIdProvider.notifier)
                  .state = list[i].id,
            ),
          ),
        );
      },
    );
  }
}

// ── My Programmes view ────────────────────────────────────────────────────────

class _MyProgrammesView extends ConsumerWidget {
  const _MyProgrammesView();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final enrolments = ref.watch(myEnrolmentsProvider);

    return enrolments.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (e, st) => _ErrorView(message: e.toString()),
      data: (list) {
        if (list.isEmpty) {
          return Center(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Text('No active programmes',
                    style: TextStyle(color: IcsColors.textMuted)),
                const SizedBox(height: IcsSpacing.m),
                TextButton(
                  onPressed: () =>
                      ref.read(learnTabProvider.notifier).state = 0,
                  child: const Text('Browse catalogue'),
                ),
              ],
            ),
          );
        }
        return RefreshIndicator(
          onRefresh: () async => ref.invalidate(myEnrolmentsProvider),
          child: ListView.separated(
            padding: const EdgeInsets.all(IcsSpacing.m),
            itemCount: list.length,
            separatorBuilder: (_, i) => const SizedBox(height: IcsSpacing.s),
            itemBuilder: (_, i) => _EnrolledTile(
              programme: list[i],
              onTap: () => ref
                  .read(selectedProgrammeIdProvider.notifier)
                  .state = list[i].id,
            ),
          ),
        );
      },
    );
  }
}

// ── Programme tile (catalogue) ────────────────────────────────────────────────

class _ProgrammeTile extends StatelessWidget {
  const _ProgrammeTile({required this.programme, required this.onTap});
  final Programme    programme;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final locked = !programme.accessible;
    return Card(
      color: IcsColors.stone1,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8),
        side: BorderSide(
          color: programme.enrolled
              ? IcsColors.accentBlue.withAlpha(102)
              : IcsColors.borderDark,
        ),
      ),
      child: InkWell(
        onTap: locked ? null : onTap,
        borderRadius: BorderRadius.circular(8),
        child: Padding(
          padding: const EdgeInsets.all(IcsSpacing.m),
          child: Row(
            children: [
              _LevelBadge(level: programme.requiredLevel),
              const SizedBox(width: IcsSpacing.m),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      programme.title,
                      style: TextStyle(
                        color: locked ? IcsColors.textMuted : Colors.white,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                    if (programme.description != null) ...[
                      const SizedBox(height: 2),
                      Text(
                        programme.description!,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(
                            color: IcsColors.textMuted, fontSize: 12),
                      ),
                    ],
                  ],
                ),
              ),
              if (programme.enrolled)
                const _EnrolledChip()
              else if (locked)
                const Icon(Icons.lock_outline,
                    color: IcsColors.textMuted, size: 16)
              else
                const Icon(Icons.chevron_right,
                    color: IcsColors.textMuted, size: 18),
            ],
          ),
        ),
      ),
    );
  }
}

// ── Enrolled tile (my programmes) ─────────────────────────────────────────────

class _EnrolledTile extends StatelessWidget {
  const _EnrolledTile({required this.programme, required this.onTap});
  final Programme    programme;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
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
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                programme.title,
                style: const TextStyle(
                    color: Colors.white, fontWeight: FontWeight.w500),
              ),
              const SizedBox(height: IcsSpacing.s),
              Row(
                children: [
                  Expanded(
                    child: LinearProgressIndicator(
                      value: programme.progress / 100,
                      backgroundColor: IcsColors.stone2,
                      valueColor: const AlwaysStoppedAnimation(
                          IcsColors.accentGreen),
                      minHeight: 4,
                    ),
                  ),
                  const SizedBox(width: IcsSpacing.s),
                  Text(
                    '${programme.progress}%',
                    style: const TextStyle(
                        color: IcsColors.textMuted, fontSize: 12),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

// ── Programme detail screen ───────────────────────────────────────────────────

class _ProgrammeDetailScreen extends ConsumerWidget {
  const _ProgrammeDetailScreen({required this.programmeId});
  final String programmeId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // Try to find the programme in either provider cache.
    final catalogue  = ref.watch(programmesProvider);
    final enrolments = ref.watch(myEnrolmentsProvider);
    final programme  = _find(catalogue, programmeId) ??
        _find(enrolments, programmeId);

    return Scaffold(
      backgroundColor: IcsColors.inkBg,
      appBar: AppBar(
        backgroundColor: IcsColors.stone1,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () =>
              ref.read(selectedProgrammeIdProvider.notifier).state = null,
        ),
        title: Text(
          programme?.title ?? 'Programme',
          overflow: TextOverflow.ellipsis,
        ),
      ),
      body: programme == null
          ? const Center(child: CircularProgressIndicator())
          : _ProgrammeDetail(programme: programme, ref: ref),
    );
  }

  Programme? _find(AsyncValue<List<Programme>> async, String id) =>
      async.whenOrNull(
        data: (list) {
          try { return list.firstWhere((p) => p.id == id); }
          catch (_) { return null; }
        },
      );
}

class _ProgrammeDetail extends ConsumerWidget {
  const _ProgrammeDetail({required this.programme, required this.ref});
  final Programme programme;
  final WidgetRef ref;

  @override
  Widget build(BuildContext context, WidgetRef watchRef) {
    return ListView(
      padding: const EdgeInsets.all(IcsSpacing.m),
      children: [
        // Header
        Container(
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
                  _LevelBadge(level: programme.requiredLevel),
                  const SizedBox(width: IcsSpacing.s),
                  Text(
                    'Level ${programme.requiredLevel}+ required',
                    style: const TextStyle(
                        color: IcsColors.textMuted, fontSize: 12),
                  ),
                ],
              ),
              const SizedBox(height: IcsSpacing.s),
              Text(
                programme.title,
                style: const TextStyle(
                    color: Colors.white,
                    fontSize: 20,
                    fontWeight: FontWeight.w600),
              ),
              if (programme.description != null &&
                  programme.description!.isNotEmpty) ...[
                const SizedBox(height: IcsSpacing.s),
                Text(
                  programme.description!,
                  style: const TextStyle(
                      color: IcsColors.textMuted, fontSize: 14),
                ),
              ],
              if (programme.enrolled) ...[
                const SizedBox(height: IcsSpacing.m),
                Row(
                  children: [
                    Expanded(
                      child: LinearProgressIndicator(
                        value: programme.progress / 100,
                        backgroundColor: IcsColors.stone2,
                        valueColor: const AlwaysStoppedAnimation(
                            IcsColors.accentGreen),
                      ),
                    ),
                    const SizedBox(width: IcsSpacing.s),
                    Text('${programme.progress}%',
                        style: const TextStyle(
                            color: IcsColors.textMuted, fontSize: 12)),
                  ],
                ),
              ],
            ],
          ),
        ),
        const SizedBox(height: IcsSpacing.m),
        // Enrol button or lesson tasks
        if (!programme.enrolled && programme.accessible)
          _EnrolButton(programmeId: programme.id, ref: ref)
        else if (programme.enrolled)
          _LessonTasksView(programmeId: programme.id),
        const SizedBox(height: IcsSpacing.xl),
      ],
    );
  }
}

// ── Enrol button ──────────────────────────────────────────────────────────────

class _EnrolButton extends ConsumerStatefulWidget {
  const _EnrolButton({required this.programmeId, required this.ref});
  final String  programmeId;
  final WidgetRef ref;

  @override
  ConsumerState<_EnrolButton> createState() => _EnrolButtonState();
}

class _EnrolButtonState extends ConsumerState<_EnrolButton> {
  bool _loading = false;
  String? _error;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        if (_error != null)
          Padding(
            padding: const EdgeInsets.only(bottom: IcsSpacing.s),
            child: Text(_error!,
                style: const TextStyle(color: IcsColors.accentRed)),
          ),
        SizedBox(
          width: double.infinity,
          child: FilledButton(
            onPressed: _loading ? null : _enrol,
            child: _loading
                ? const SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(
                        strokeWidth: 2, color: Colors.white),
                  )
                : const Text('Enrol in programme'),
          ),
        ),
      ],
    );
  }

  Future<void> _enrol() async {
    setState(() { _loading = true; _error = null; });
    try {
      final client = ref.read(apiClientProvider);
      await client.post('/learn/programmes/${widget.programmeId}/enrol/', {});
      ref.invalidate(programmesProvider);
      ref.invalidate(myEnrolmentsProvider);
      widget.ref.read(learnTabProvider.notifier).state = 1;
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }
}

// ── Lesson tasks (enrolled view) ──────────────────────────────────────────────

class _LessonTasksView extends ConsumerWidget {
  const _LessonTasksView({required this.programmeId});
  final String programmeId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final enrolment = ref.watch(enrolmentDetailProvider(programmeId));

    return enrolment.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (e, st) => _ErrorView(message: e.toString()),
      data: (enrolment) => Column(
        children: enrolment.courses.map((course) =>
          _CourseSection(course: course, ref: ref, programmeId: programmeId),
        ).toList(),
      ),
    );
  }
}

class _CourseSection extends StatelessWidget {
  const _CourseSection({
    required this.course,
    required this.ref,
    required this.programmeId,
  });
  final CourseProgress course;
  final WidgetRef      ref;
  final String         programmeId;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.only(bottom: IcsSpacing.s),
          child: Row(
            children: [
              Expanded(
                child: Text(
                  course.courseTitle,
                  style: const TextStyle(
                      color: Colors.white, fontWeight: FontWeight.w500),
                ),
              ),
              Text(
                '${course.progress}%',
                style: const TextStyle(
                    color: IcsColors.textMuted, fontSize: 12),
              ),
            ],
          ),
        ),
        ...course.lessons.map((lesson) =>
          _LessonRow(lesson: lesson, programmeId: programmeId, ref: ref)),
        const SizedBox(height: IcsSpacing.m),
      ],
    );
  }
}

class _LessonRow extends ConsumerStatefulWidget {
  const _LessonRow({
    required this.lesson,
    required this.programmeId,
    required this.ref,
  });
  final LessonTask lesson;
  final String     programmeId;
  final WidgetRef  ref;

  @override
  ConsumerState<_LessonRow> createState() => _LessonRowState();
}

class _LessonRowState extends ConsumerState<_LessonRow> {
  bool _completing = false;

  @override
  Widget build(BuildContext context) {
    final done = widget.lesson.isCompleted;
    return Padding(
      padding: const EdgeInsets.only(bottom: IcsSpacing.s),
      child: Container(
        decoration: BoxDecoration(
          color: IcsColors.stone1,
          borderRadius: BorderRadius.circular(6),
          border: Border.all(color: IcsColors.borderDark),
        ),
        child: ListTile(
          leading: done
              ? const Icon(Icons.check_circle,
                  color: IcsColors.accentGreen, size: 20)
              : const Icon(Icons.radio_button_unchecked,
                  color: IcsColors.textMuted, size: 20),
          title: Text(
            widget.lesson.title,
            style: TextStyle(
              color: done ? IcsColors.textMuted : Colors.white,
              fontSize: 14,
              decoration: done ? TextDecoration.lineThrough : null,
            ),
          ),
          trailing: done
              ? null
              : _completing
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : TextButton(
                      onPressed: _complete,
                      child: const Text('Done',
                          style: TextStyle(fontSize: 12)),
                    ),
        ),
      ),
    );
  }

  Future<void> _complete() async {
    setState(() => _completing = true);
    try {
      final client = ref.read(apiClientProvider);
      await client.post('/learn/complete-lesson/${widget.lesson.id}/', {});
      ref.invalidate(enrolmentDetailProvider(widget.programmeId));
      ref.invalidate(myEnrolmentsProvider);
    } catch (_) {
      // Lesson completion is optimistic — silently fail, user can retry.
    } finally {
      if (mounted) setState(() => _completing = false);
    }
  }
}

// ── Shared widgets ────────────────────────────────────────────────────────────

class _LevelBadge extends StatelessWidget {
  const _LevelBadge({required this.level});
  final int level;

  @override
  Widget build(BuildContext context) {
    final color = switch (level) {
      0 => IcsColors.textMuted,
      1 => IcsColors.accentBlue,
      2 => IcsColors.accentGreen,
      3 => IcsColors.accentAmber,
      4 => IcsColors.accentRed,
      _ => Colors.purple,
    };
    return Container(
      padding: const EdgeInsets.symmetric(
          horizontal: IcsSpacing.s, vertical: 2),
      decoration: BoxDecoration(
        color: color.withAlpha(26),
        borderRadius: BorderRadius.circular(4),
        border: Border.all(color: color.withAlpha(77)),
      ),
      child: Text(
        'L$level',
        style: TextStyle(color: color, fontSize: 11, fontWeight: FontWeight.w600),
      ),
    );
  }
}

class _EnrolledChip extends StatelessWidget {
  const _EnrolledChip();

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(
          horizontal: IcsSpacing.s, vertical: 2),
      decoration: BoxDecoration(
        color: IcsColors.accentBlue.withAlpha(26),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: IcsColors.accentBlue.withAlpha(77)),
      ),
      child: const Text(
        'Enrolled',
        style: TextStyle(
            color: IcsColors.accentBlue, fontSize: 10),
      ),
    );
  }
}

class _ErrorView extends StatelessWidget {
  const _ErrorView({required this.message});
  final String message;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(IcsSpacing.l),
        child: Text(
          message,
          style: const TextStyle(color: IcsColors.accentRed),
          textAlign: TextAlign.center,
        ),
      ),
    );
  }
}

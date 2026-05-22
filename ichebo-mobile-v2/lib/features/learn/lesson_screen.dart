import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/api/api_client.dart';
import '../../core/api/providers.dart';
import '../../shared/tokens/tokens.dart';
import '../../shared/widgets/badges.dart';
import '../../shared/widgets/empty_state.dart';
import '../../shared/widgets/ichebo_button.dart';
import '../../shared/widgets/ichebo_card.dart';
import '../../shared/widgets/ichebo_video_player.dart';

class LessonScreen extends ConsumerWidget {
  const LessonScreen({super.key, required this.programmeId});
  final String programmeId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final lessonsAsync = ref.watch(lessonsProvider(programmeId));

    return Scaffold(
      appBar: AppBar(
        title: const Text('Lessons'),
        centerTitle: false,
      ),
      body: lessonsAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => EmptyState(message: e.toString()),
        data: (lessons) => lessons.isEmpty
            ? const EmptyState(
                icon: Icons.school_outlined,
                message: 'No lessons available yet.',
              )
            : ListView.builder(
                padding: const EdgeInsets.all(IcheboSpacing.s),
                itemCount: lessons.length,
                itemBuilder: (context, i) => Padding(
                  padding: const EdgeInsets.only(bottom: IcheboSpacing.xs),
                  child: _LessonTile(
                    lesson: lessons[i],
                    onTap: () => Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (_) => _LessonDetailScreen(lesson: lessons[i]),
                      ),
                    ),
                  ),
                ),
              ),
      ),
    );
  }
}

class _LessonTile extends StatelessWidget {
  const _LessonTile({required this.lesson, required this.onTap});
  final Lesson lesson;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return IcheboCard(
      accent: lesson.completed,
      child: InkWell(
        onTap: onTap,
        borderRadius: IcheboRadius.l,
        child: Row(
          children: [
            Container(
              width: 32,
              height: 32,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: lesson.completed
                    ? IcheboColors.success.withValues(alpha: 0.15)
                    : IcheboColors.stone2,
              ),
              alignment: Alignment.center,
              child: lesson.completed
                  ? const Icon(Icons.check, size: 16, color: IcheboColors.success)
                  : Text(
                      '${lesson.order}',
                      style: IcheboTextStyles.labelLarge.copyWith(
                        color: IcheboColors.muted,
                        fontSize: 12,
                      ),
                    ),
            ),
            const SizedBox(width: IcheboSpacing.xs),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(lesson.title,
                      style: Theme.of(context).textTheme.titleMedium),
                  if (lesson.summary != null && lesson.summary!.isNotEmpty)
                    Text(
                      lesson.summary!,
                      style: Theme.of(context).textTheme.bodySmall,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                ],
              ),
            ),
            const SizedBox(width: IcheboSpacing.xs3),
            if (lesson.videoUrl != null)
              const Icon(Icons.play_circle_outline,
                  size: 20, color: IcheboColors.secondary),
            const Icon(Icons.chevron_right, size: 18, color: IcheboColors.mutedLight),
          ],
        ),
      ),
    );
  }
}

// ── Lesson detail ─────────────────────────────────────────────────────────────

class _LessonDetailScreen extends ConsumerStatefulWidget {
  const _LessonDetailScreen({required this.lesson});
  final Lesson lesson;

  @override
  ConsumerState<_LessonDetailScreen> createState() => _LessonDetailScreenState();
}

class _LessonDetailScreenState extends ConsumerState<_LessonDetailScreen> {
  bool _marking = false;
  late bool _completed;

  @override
  void initState() {
    super.initState();
    _completed = widget.lesson.completed;
  }

  Future<void> _markComplete() async {
    setState(() => _marking = true);
    try {
      await ref.read(apiClientProvider).post<void>(
        'learn/lessons/${widget.lesson.id}/complete/',
        data: {},
      );
      ref.invalidate(lessonsProvider(widget.lesson.programmeId));
      ref.invalidate(myEnrolmentsProvider);
      if (mounted) setState(() => _completed = true);
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Could not mark complete. Please try again.')),
        );
      }
    } finally {
      if (mounted) setState(() => _marking = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final lesson = widget.lesson;

    return Scaffold(
      appBar: AppBar(
        title: Text(lesson.programmeTitle,
            style: Theme.of(context)
                .textTheme
                .bodyMedium
                ?.copyWith(color: IcheboColors.muted)),
        centerTitle: false,
      ),
      body: ListView(
        padding: const EdgeInsets.all(IcheboSpacing.s),
        children: [
          // ── Title + status ────────────────────────────────────────────
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Text(lesson.title,
                    style: IcheboTextStyles.headlineLarge),
              ),
              if (_completed)
                const StatusBadge(label: 'Done', variant: StatusVariant.success),
            ],
          ),
          const SizedBox(height: IcheboSpacing.s),

          // ── Video ─────────────────────────────────────────────────────
          if (lesson.videoUrl != null && lesson.videoUrl!.isNotEmpty) ...[
            IcheboVideoPlayer(
              videoUrl: lesson.videoUrl!,
              activityId: lesson.activityId,
              videoRecordId: lesson.videoRecordId,
              chapters: lesson.chapterMarkers.isNotEmpty
                  ? lesson.chapterMarkers
                  : null,
              onComplete: _markComplete,
            ),
            const SizedBox(height: IcheboSpacing.s),
          ],

          // ── Content ───────────────────────────────────────────────────
          if (lesson.markdownContent != null &&
              lesson.markdownContent!.isNotEmpty) ...[
            MarkdownBody(
              data: lesson.markdownContent!,
              styleSheet: MarkdownStyleSheet.fromTheme(Theme.of(context))
                  .copyWith(
                p: Theme.of(context)
                    .textTheme
                    .bodyLarge
                    ?.copyWith(height: 1.7),
              ),
            ),
            const SizedBox(height: IcheboSpacing.m),
          ] else if (lesson.summary != null && lesson.summary!.isNotEmpty) ...[
            Text(lesson.summary!,
                style: Theme.of(context)
                    .textTheme
                    .bodyLarge
                    ?.copyWith(height: 1.7)),
            const SizedBox(height: IcheboSpacing.m),
          ],

          // ── Mark complete ─────────────────────────────────────────────
          if (!_completed)
            IcheboButton(
              label: 'Mark as complete',
              icon: Icons.check_circle_outline,
              onPressed: _markComplete,
              loading: _marking,
            )
          else
            IcheboButton(
              label: 'Completed',
              icon: Icons.check_circle,
              onPressed: null,
              variant: IcheboButtonVariant.secondary,
            ),

          const SizedBox(height: IcheboSpacing.xl),
        ],
      ),
    );
  }
}


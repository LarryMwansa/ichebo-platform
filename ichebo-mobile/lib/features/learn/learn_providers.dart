import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/api/providers.dart';

// ── Models ────────────────────────────────────────────────────────────────────

class Programme {
  const Programme({
    required this.id,
    required this.title,
    required this.status,
    required this.enrolled,
    required this.accessible,
    this.description,
    this.requiredLevel = 1,
    this.progress      = 0,
  });

  final String  id;
  final String  title;
  final String  status;
  final bool    enrolled;
  final bool    accessible;
  final String? description;
  final int     requiredLevel;
  final int     progress;

  factory Programme.fromJson(Map<String, dynamic> j) {
    final meta  = j['metadata'] as Map<String, dynamic>? ?? {};
    final perms = j['permissions'] as Map<String, dynamic>? ?? {};
    return Programme(
      id:            j['id']           as String,
      title:         j['title']        as String? ?? '(Untitled)',
      status:        j['status']       as String? ?? 'active',
      enrolled:      j['enrolled']     as bool?   ?? false,
      accessible:    j['accessible']   as bool?   ?? false,
      description:   meta['description'] as String?,
      requiredLevel: perms['required_level'] as int? ?? 1,
      progress:      j['progress']     as int?    ?? 0,
    );
  }
}

class Enrolment {
  const Enrolment({
    required this.programmeActivityId,
    required this.programmeTitle,
    required this.progress,
    required this.courses,
  });

  final String       programmeActivityId;
  final String       programmeTitle;
  final int          progress;
  final List<CourseProgress> courses;

  factory Enrolment.fromJson(Map<String, dynamic> j) => Enrolment(
    programmeActivityId: j['programme_activity_id'] as String? ?? '',
    programmeTitle:      j['programme_title']       as String? ?? '',
    progress:            j['progress']              as int?    ?? 0,
    courses: (j['courses'] as List<dynamic>? ?? [])
        .cast<Map<String, dynamic>>()
        .map(CourseProgress.fromJson)
        .toList(),
  );
}

class CourseProgress {
  const CourseProgress({
    required this.courseActivityId,
    required this.courseTitle,
    required this.progress,
    required this.lessons,
  });

  final String          courseActivityId;
  final String          courseTitle;
  final int             progress;
  final List<LessonTask> lessons;

  factory CourseProgress.fromJson(Map<String, dynamic> j) => CourseProgress(
    courseActivityId: j['course_activity_id'] as String? ?? '',
    courseTitle:      j['course_title']       as String? ?? '',
    progress:         j['progress']           as int?    ?? 0,
    lessons: (j['lessons'] as List<dynamic>? ?? [])
        .cast<Map<String, dynamic>>()
        .map(LessonTask.fromJson)
        .toList(),
  );
}

class LessonTask {
  const LessonTask({
    required this.id,
    required this.title,
    required this.status,
    required this.progress,
  });

  final String id;
  final String title;
  final String status;
  final int    progress;

  bool get isCompleted => status == 'completed' || progress >= 100;

  factory LessonTask.fromJson(Map<String, dynamic> j) => LessonTask(
    id:       j['id']       as String? ?? '',
    title:    j['title']    as String? ?? '(Lesson)',
    status:   j['status']   as String? ?? 'active',
    progress: j['progress'] as int?    ?? 0,
  );
}

// ── Providers ─────────────────────────────────────────────────────────────────

final programmesProvider = FutureProvider<List<Programme>>((ref) async {
  final client = ref.watch(apiClientProvider);
  final data   = await client.get('/learn/programmes/') as List<dynamic>;
  return data.cast<Map<String, dynamic>>().map(Programme.fromJson).toList();
});

final myEnrolmentsProvider = FutureProvider<List<Programme>>((ref) async {
  final client = ref.watch(apiClientProvider);
  final data   = await client.get('/learn/my-enrolments/') as List<dynamic>;
  return data.cast<Map<String, dynamic>>().map(Programme.fromJson).toList();
});

final enrolmentDetailProvider =
    FutureProvider.family<Enrolment, String>((ref, programmeId) async {
  final client = ref.watch(apiClientProvider);
  final data   = await client.get('/learn/my-lesson-tasks/$programmeId/')
      as Map<String, dynamic>;
  return Enrolment.fromJson(data);
});

// ── UI state ──────────────────────────────────────────────────────────────────

final selectedProgrammeIdProvider = StateProvider<String?>((_) => null);
final learnTabProvider            = StateProvider<int>((_) => 0); // 0=catalogue 1=mine

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'api_client.dart';

// Generic paginated result wrapper.
class PageResult<T> {
  const PageResult({
    required this.results,
    required this.count,
    this.next,
  });
  final List<T> results;
  final int count;
  final int? next;
}

// ── Helpers ───────────────────────────────────────────────────────────────────

String _friendlyDioError(Object e) {
  if (e is DioException) {
    final status = e.response?.statusCode;
    if (status == 401) return 'Session expired. Please sign in again.';
    if (status == 403) return 'You do not have permission to view this.';
    if (status == 404) return 'Not found.';
    if (status != null && status >= 500) return 'Server error. Please try again later.';
    if (e.type == DioExceptionType.connectionTimeout ||
        e.type == DioExceptionType.receiveTimeout) {
      return 'Connection timed out.';
    }
    if (e.type == DioExceptionType.connectionError) return 'No internet connection.';
  }
  return 'Something went wrong.';
}

// ── Paraclete ─────────────────────────────────────────────────────────────────

class ParacleteDigest {
  const ParacleteDigest({
    required this.generatedAt,
    required this.competenceLevel,
    required this.pendingCount,
    required this.overdueCount,
    required this.dueToday,
    required this.overdueItems,
    required this.habitStreaks,
    required this.activeEnrolments,
    this.nextLesson,
    required this.disciplinePrompt,
    required this.promptPathway,
    this.darToday,
    this.teamPendingCount,
    this.teamOverdueCount,
  });

  final String generatedAt;
  final int competenceLevel;
  final int pendingCount;
  final int overdueCount;
  final List<ActivityCard> dueToday;
  final List<ActivityCard> overdueItems;
  final List<HabitStreak> habitStreaks;
  final List<ProgrammeCard> activeEnrolments;
  final LessonCard? nextLesson;
  final String disciplinePrompt;
  final String promptPathway;
  final DarCard? darToday;
  final int? teamPendingCount;
  final int? teamOverdueCount;

  factory ParacleteDigest.fromJson(Map<String, dynamic> j) => ParacleteDigest(
        generatedAt: j['generated_at'] as String,
        competenceLevel: j['competence_level'] as int,
        pendingCount: j['pending_count'] as int,
        overdueCount: j['overdue_count'] as int,
        dueToday: (j['due_today'] as List).map((e) => ActivityCard.fromJson(e as Map<String, dynamic>)).toList(),
        overdueItems: (j['overdue_items'] as List).map((e) => ActivityCard.fromJson(e as Map<String, dynamic>)).toList(),
        habitStreaks: (j['habit_streaks'] as List).map((e) => HabitStreak.fromJson(e as Map<String, dynamic>)).toList(),
        activeEnrolments: (j['active_enrolments'] as List).map((e) => ProgrammeCard.fromJson(e as Map<String, dynamic>)).toList(),
        nextLesson: j['next_lesson'] != null ? LessonCard.fromJson(j['next_lesson'] as Map<String, dynamic>) : null,
        disciplinePrompt: (j['discipline_prompt'] as String?) ?? '',
        promptPathway: (j['prompt_pathway'] as String?) ?? '',
        darToday: j['dar_today'] != null ? DarCard.fromJson(j['dar_today'] as Map<String, dynamic>) : null,
        teamPendingCount: j['team_pending_count'] as int?,
        teamOverdueCount: j['team_over_count'] as int?,
      );
}

class ActivityCard {
  const ActivityCard({required this.id, required this.title, required this.activityType, required this.status, this.dueAt, this.kgsPathway});
  final String id;
  final String title;
  final String activityType;
  final String status;
  final String? dueAt;
  final String? kgsPathway;
  factory ActivityCard.fromJson(Map<String, dynamic> j) => ActivityCard(
        id: j['id'] as String,
        title: j['title'] as String,
        activityType: j['activity_type'] as String,
        status: j['status'] as String,
        dueAt: j['due_at'] as String?,
        kgsPathway: j['kgs_pathway'] as String?,
      );
}

class HabitStreak {
  const HabitStreak({required this.activityId, required this.title, required this.streak, this.lastCompleted});
  final String activityId;
  final String title;
  final int streak;
  final String? lastCompleted;
  factory HabitStreak.fromJson(Map<String, dynamic> j) => HabitStreak(
        activityId: j['activity_id'] as String,
        title: j['title'] as String,
        streak: j['streak'] as int,
        lastCompleted: j['last_completed'] as String?,
      );
}

class ProgrammeCard {
  const ProgrammeCard({required this.recordId, required this.title, required this.progress});
  final String recordId;
  final String title;
  final int progress;
  factory ProgrammeCard.fromJson(Map<String, dynamic> j) => ProgrammeCard(
        recordId: j['record_id'] as String,
        title: j['title'] as String,
        progress: j['progress'] as int,
      );
}

class LessonCard {
  const LessonCard({required this.recordId, required this.title, required this.programmeTitle, required this.url});
  final String recordId;
  final String title;
  final String programmeTitle;
  final String url;
  factory LessonCard.fromJson(Map<String, dynamic> j) => LessonCard(
        recordId: j['record_id'] as String,
        title: j['title'] as String,
        programmeTitle: j['programme_title'] as String,
        url: j['url'] as String,
      );
}

class DarCard {
  const DarCard({required this.recordId, required this.title, required this.createdAt, required this.url});
  final String recordId;
  final String title;
  final String createdAt;
  final String url;
  factory DarCard.fromJson(Map<String, dynamic> j) => DarCard(
        recordId: j['record_id'] as String,
        title: j['title'] as String,
        createdAt: j['created_at'] as String,
        url: j['url'] as String,
      );
}

final paracleteDigestProvider = FutureProvider.autoDispose<ParacleteDigest>((ref) async {
  final client = ref.read(apiClientProvider);
  try {
    final res = await client.get<Map<String, dynamic>>('paraclete/digest/');
    return ParacleteDigest.fromJson(res.data!);
  } catch (e) {
    throw _friendlyDioError(e);
  }
});

// ── Bible ─────────────────────────────────────────────────────────────────────

class BibleTranslation {
  const BibleTranslation({required this.id, required this.code, required this.name, required this.isDefault});
  final String id;
  final String code;
  final String name;
  final bool isDefault;
  factory BibleTranslation.fromJson(Map<String, dynamic> j) => BibleTranslation(
        id: j['id'] as String,
        code: j['code'] as String,
        name: j['name'] as String,
        isDefault: (j['is_default'] as bool?) ?? false,
      );
}

class BibleBook {
  const BibleBook({required this.id, required this.code, required this.name, required this.testament, required this.order});
  final String id;
  final String code;
  final String name;
  final String testament;
  final int order;
  factory BibleBook.fromJson(Map<String, dynamic> j) => BibleBook(
        id: j['id'] as String,
        code: j['code'] as String,
        name: j['name'] as String,
        testament: j['testament'] as String,
        order: j['order'] as int,
      );
}

class BibleVerse {
  const BibleVerse({required this.id, required this.bookCode, required this.bookName, required this.chapter, required this.verse, required this.text, required this.translationCode});
  final String id;
  final String bookCode;
  final String bookName;
  final int chapter;
  final int verse;
  final String text;
  final String translationCode;
  factory BibleVerse.fromJson(Map<String, dynamic> j) => BibleVerse(
        id: j['id'] as String,
        bookCode: j['book_code'] as String,
        bookName: j['book_name'] as String,
        chapter: j['chapter'] as int,
        verse: j['verse'] as int,
        text: j['text'] as String,
        translationCode: j['translation_code'] as String,
      );
}

final bibleTranslationsProvider = FutureProvider.autoDispose<List<BibleTranslation>>((ref) async {
  final res = await ref.read(apiClientProvider).get<List>('bible/translations/');
  return (res.data ?? []).map((e) => BibleTranslation.fromJson(e as Map<String, dynamic>)).toList();
});

final bibleBooksProvider = FutureProvider.autoDispose<List<BibleBook>>((ref) async {
  final res = await ref.read(apiClientProvider).get<List>('bible/books/');
  return (res.data ?? []).map((e) => BibleBook.fromJson(e as Map<String, dynamic>)).toList();
});

// params: {bookCode, chapter, translationCode?}
final bibleVersesProvider = FutureProvider.autoDispose.family<List<BibleVerse>, Map<String, String>>((ref, params) async {
  final res = await ref.read(apiClientProvider).get<List>('bible/verses/', params: params);
  return (res.data ?? []).map((e) => BibleVerse.fromJson(e as Map<String, dynamic>)).toList();
});

final bibleChaptersProvider = FutureProvider.autoDispose.family<List<int>, String>((ref, bookCode) async {
  final res = await ref.read(apiClientProvider).get<Map<String, dynamic>>('bible/chapters/', params: {'book_code': bookCode});
  return ((res.data?['chapters'] as List?) ?? []).map((e) => e as int).toList();
});

// ── Learn ─────────────────────────────────────────────────────────────────────

class Programme {
  const Programme({required this.id, required this.title, this.summary, required this.status, required this.requiredLevel, required this.enrolled, required this.accessible, this.kgsQualification});
  final String id;
  final String title;
  final String? summary;
  final String status;
  final int requiredLevel;
  final bool enrolled;
  final bool accessible;
  final String? kgsQualification;
  factory Programme.fromJson(Map<String, dynamic> j) => Programme(
        id: j['id'] as String,
        title: j['title'] as String,
        summary: j['summary'] as String?,
        status: j['status'] as String,
        requiredLevel: (j['required_level'] as int?) ?? 1,
        enrolled: (j['enrolled'] as bool?) ?? false,
        accessible: (j['accessible'] as bool?) ?? false,
        kgsQualification: j['kgs_qualification'] as String?,
      );
}

final programmesProvider = FutureProvider.autoDispose<List<Programme>>((ref) async {
  final res = await ref.read(apiClientProvider).get<List>('learn/programmes/');
  return (res.data ?? []).map((e) => Programme.fromJson(e as Map<String, dynamic>)).toList();
});

final myEnrolmentsProvider = FutureProvider.autoDispose<List<Programme>>((ref) async {
  final res = await ref.read(apiClientProvider).get<List>('learn/enrolments/');
  return (res.data ?? []).map((e) => Programme.fromJson(e as Map<String, dynamic>)).toList();
});

// ── Activity ──────────────────────────────────────────────────────────────────

class ActivityItem {
  const ActivityItem({required this.id, required this.title, required this.activityType, required this.status, this.dueAt, this.description, this.progress});
  final String id;
  final String title;
  final String activityType;
  final String status;
  final String? dueAt;
  final String? description;
  final int? progress;
  factory ActivityItem.fromJson(Map<String, dynamic> j) => ActivityItem(
        id: j['id'] as String,
        title: j['title'] as String,
        activityType: j['activity_type'] as String,
        status: j['status'] as String,
        dueAt: j['due_at'] as String?,
        description: j['description'] as String?,
        progress: j['progress'] as int?,
      );
}

// params: {activity_type?, status?, page?}
final activitiesProvider = FutureProvider.autoDispose.family<List<ActivityItem>, Map<String, String>>((ref, params) async {
  final res = await ref.read(apiClientProvider).get<Map<String, dynamic>>('activities/', params: params);
  final raw = res.data?['results'] as List? ?? res.data as List? ?? [];
  return raw.map((e) => ActivityItem.fromJson(e as Map<String, dynamic>)).toList();
});

// ── Community ─────────────────────────────────────────────────────────────────

class Member {
  const Member({required this.id, required this.displayName, required this.email, required this.competenceLevel, required this.role, this.avatarUrl, this.serviceOrder, this.joinedAt});
  final String id;
  final String displayName;
  final String email;
  final int competenceLevel;
  final String role;
  final String? avatarUrl;
  final String? serviceOrder;
  final String? joinedAt;
  factory Member.fromJson(Map<String, dynamic> j) => Member(
        id: j['id'] as String,
        displayName: (j['display_name'] as String?) ?? j['email'] as String,
        email: j['email'] as String,
        competenceLevel: (j['competence_level'] as int?) ?? 0,
        role: (j['role'] as String?) ?? 'seeker',
        avatarUrl: j['avatar_url'] as String?,
        serviceOrder: j['service_order'] as String?,
        joinedAt: j['joined_at'] as String?,
      );
}

final communityMembersProvider = FutureProvider.autoDispose.family<PageResult<Member>, Map<String, String>>((ref, params) async {
  final res = await ref.read(apiClientProvider).get<Map<String, dynamic>>('community/members/', params: params);
  final data = res.data!;
  return PageResult(
    count: data['count'] as int,
    results: (data['results'] as List).map((e) => Member.fromJson(e as Map<String, dynamic>)).toList(),
  );
});

// ── Notifications ─────────────────────────────────────────────────────────────

class AppNotification {
  const AppNotification({required this.id, required this.message, required this.notificationType, required this.createdAt, this.readAt});
  final String id;
  final String message;
  final String notificationType;
  final String createdAt;
  final String? readAt;
  bool get isRead => readAt != null;
  factory AppNotification.fromJson(Map<String, dynamic> j) => AppNotification(
        id: j['id'] as String,
        message: (j['message'] as String?) ?? '',
        notificationType: (j['notification_type'] as String?) ?? '',
        createdAt: (j['created_at'] as String?) ?? '',
        readAt: j['read_at'] as String?,
      );
}

final notificationsProvider = FutureProvider.autoDispose<List<AppNotification>>((ref) async {
  final res = await ref.read(apiClientProvider).get<Map<String, dynamic>>('notifications/notifications/');
  final raw = (res.data?['results'] as List?) ?? [];
  return raw.map((e) => AppNotification.fromJson(e as Map<String, dynamic>)).toList();
});

final unreadCountProvider = FutureProvider.autoDispose<int>((ref) async {
  final res = await ref.read(apiClientProvider).get<Map<String, dynamic>>('notifications/notifications/unread-count/');
  return (res.data?['count'] as int?) ?? 0;
});

// ── Records (Governance) ──────────────────────────────────────────────────────

class GovernanceRecord {
  const GovernanceRecord({required this.id, required this.title, required this.recordType, required this.recordClass, required this.status, this.summary, this.createdAt});
  final String id;
  final String title;
  final String recordType;
  final String recordClass;
  final String status;
  final String? summary;
  final String? createdAt;
  factory GovernanceRecord.fromJson(Map<String, dynamic> j) => GovernanceRecord(
        id: j['id'] as String,
        title: (j['title'] as String?) ?? '',
        recordType: (j['record_type'] as String?) ?? '',
        recordClass: (j['record_class'] as String?) ?? '',
        status: (j['status'] as String?) ?? '',
        summary: j['summary'] as String?,
        createdAt: j['created_at'] as String?,
      );
}

// params: {record_class, record_family?, record_type?}
final recordsProvider = FutureProvider.autoDispose.family<List<GovernanceRecord>, Map<String, String>>((ref, params) async {
  final res = await ref.read(apiClientProvider).get<Map<String, dynamic>>('records/', params: params);
  final raw = res.data?['results'] as List? ?? [];
  return raw.map((e) => GovernanceRecord.fromJson(e as Map<String, dynamic>)).toList();
});

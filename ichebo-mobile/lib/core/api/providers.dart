import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'api_client.dart';
import '../cache/offline_cache.dart';
import '../../shared/widgets/chapter_navigator.dart';

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
  final cache = ref.read(offlineCacheProvider);
  try {
    final res = await client.get<Map<String, dynamic>>('paraclete/digest/');
    await cache.put(CacheKeys.paracleteDigest, res.data!);
    return ParacleteDigest.fromJson(res.data!);
  } catch (e) {
    final cached = await cache.get<ParacleteDigest>(
      CacheKeys.paracleteDigest,
      (d) => ParacleteDigest.fromJson(d as Map<String, dynamic>),
    );
    if (cached != null) return cached;
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
  final client = ref.read(apiClientProvider);
  final cache = ref.read(offlineCacheProvider);
  List<BibleTranslation> parse(dynamic d) =>
      (d as List).map((e) => BibleTranslation.fromJson(e as Map<String, dynamic>)).toList();
  try {
    final res = await client.get<List>('bible/translations/');
    await cache.put(CacheKeys.bibleTranslations, res.data!);
    return parse(res.data!);
  } catch (_) {
    final cached = await cache.get<List<BibleTranslation>>(CacheKeys.bibleTranslations, parse);
    return cached ?? [];
  }
});

final bibleBooksProvider = FutureProvider.autoDispose<List<BibleBook>>((ref) async {
  final client = ref.read(apiClientProvider);
  final cache = ref.read(offlineCacheProvider);
  List<BibleBook> parse(dynamic d) =>
      (d as List).map((e) => BibleBook.fromJson(e as Map<String, dynamic>)).toList();
  try {
    final res = await client.get<List>('bible/books/');
    await cache.put(CacheKeys.bibleBooks, res.data!);
    return parse(res.data!);
  } catch (_) {
    final cached = await cache.get<List<BibleBook>>(CacheKeys.bibleBooks, parse);
    return cached ?? [];
  }
});

// params: {book_code, chapter, translation_code?}
final bibleVersesProvider = FutureProvider.autoDispose.family<List<BibleVerse>, Map<String, String>>((ref, params) async {
  final client = ref.read(apiClientProvider);
  final cache = ref.read(offlineCacheProvider);
  final bookCode = params['book_code'] ?? '';
  final chapter = int.tryParse(params['chapter'] ?? '') ?? 0;
  final translationCode = params['translation_code'] ?? 'default';
  final cacheKey = CacheKeys.bibleVerses(bookCode, chapter, translationCode);
  List<BibleVerse> parse(dynamic d) =>
      (d as List).map((e) => BibleVerse.fromJson(e as Map<String, dynamic>)).toList();
  try {
    final res = await client.get<List>('bible/verses/', params: params);
    await cache.put(cacheKey, res.data!);
    return parse(res.data!);
  } catch (_) {
    final cached = await cache.get<List<BibleVerse>>(cacheKey, parse);
    return cached ?? [];
  }
});

final bibleChaptersProvider = FutureProvider.autoDispose.family<List<int>, String>((ref, bookCode) async {
  final client = ref.read(apiClientProvider);
  final cache = ref.read(offlineCacheProvider);
  final cacheKey = CacheKeys.bibleChapters(bookCode);
  List<int> parse(dynamic d) {
    final m = d as Map<String, dynamic>;
    return ((m['chapters'] as List?) ?? []).map((e) => e as int).toList();
  }
  try {
    final res = await client.get<Map<String, dynamic>>('bible/chapters/', params: {'book_code': bookCode});
    await cache.put(cacheKey, res.data!);
    return parse(res.data!);
  } catch (_) {
    final cached = await cache.get<List<int>>(cacheKey, parse);
    return cached ?? [];
  }
});

// ── Bible notes (record_family=bible, record_type=bible_note) ────────────────

class BibleNote {
  const BibleNote({
    required this.id,
    required this.title,
    required this.summary,
    required this.createdAt,
    this.verseRef,
  });
  final String id;
  final String title;
  final String summary;
  final String createdAt;
  final String? verseRef; // e.g. "GEN 1:1"
  factory BibleNote.fromJson(Map<String, dynamic> j) => BibleNote(
        id: j['id'] as String,
        title: (j['title'] as String?) ?? '',
        summary: (j['summary'] as String?) ?? '',
        createdAt: (j['created_at'] as String?) ?? '',
        verseRef: j['verse_ref'] as String?,
      );
}

// params: {book_code, chapter, verse}
final bibleNotesProvider = FutureProvider.autoDispose
    .family<List<BibleNote>, Map<String, String>>((ref, params) async {
  final client = ref.read(apiClientProvider);
  final verseRef = '${params['book_code']} ${params['chapter']}:${params['verse']}';
  final cacheKey = 'bible_note_${params['book_code']}_${params['chapter']}_${params['verse']}';
  List<BibleNote> parse(dynamic d) {
    final raw = (d as Map<String, dynamic>)['results'] as List? ?? [];
    return raw.map((e) => BibleNote.fromJson(e as Map<String, dynamic>)).toList();
  }
  try {
    final res = await client.get<Map<String, dynamic>>(
      'records/',
      params: {
        'record_family': 'bible',
        'record_type': 'bible_note',
        'verse_ref': verseRef,
      },
    );
    await ref.read(offlineCacheProvider).put(cacheKey, res.data!);
    return parse(res.data!);
  } catch (_) {
    return await ref.read(offlineCacheProvider).get<List<BibleNote>>(cacheKey, parse) ?? [];
  }
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
  final client = ref.read(apiClientProvider);
  final cache = ref.read(offlineCacheProvider);
  List<Programme> parse(dynamic d) =>
      (d as List).map((e) => Programme.fromJson(e as Map<String, dynamic>)).toList();
  try {
    final res = await client.get<List>('learn/programmes/');
    await cache.put(CacheKeys.programmes, res.data!);
    return parse(res.data!);
  } catch (_) {
    return await cache.get<List<Programme>>(CacheKeys.programmes, parse) ?? [];
  }
});

final myEnrolmentsProvider = FutureProvider.autoDispose<List<Programme>>((ref) async {
  final client = ref.read(apiClientProvider);
  final cache = ref.read(offlineCacheProvider);
  List<Programme> parse(dynamic d) =>
      (d as List).map((e) => Programme.fromJson(e as Map<String, dynamic>)).toList();
  try {
    final res = await client.get<List>('learn/enrolments/');
    await cache.put(CacheKeys.myEnrolments, res.data!);
    return parse(res.data!);
  } catch (_) {
    return await cache.get<List<Programme>>(CacheKeys.myEnrolments, parse) ?? [];
  }
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
  final client = ref.read(apiClientProvider);
  final cache = ref.read(offlineCacheProvider);
  final cacheKey = 'activities_${params.entries.map((e) => '${e.key}=${e.value}').join('_')}';
  List<ActivityItem> parse(dynamic d) {
    final raw = (d as Map<String, dynamic>)['results'] as List? ?? d as List? ?? [];
    return raw.map((e) => ActivityItem.fromJson(e as Map<String, dynamic>)).toList();
  }
  try {
    final res = await client.get<Map<String, dynamic>>('activities/', params: params);
    await cache.put(cacheKey, res.data!);
    final raw = res.data?['results'] as List? ?? res.data as List? ?? [];
    return raw.map((e) => ActivityItem.fromJson(e as Map<String, dynamic>)).toList();
  } catch (_) {
    return await cache.get<List<ActivityItem>>(cacheKey, parse) ?? [];
  }
});

// ── Lessons ───────────────────────────────────────────────────────────────────

class Lesson {
  const Lesson({
    required this.id,
    required this.title,
    required this.programmeId,
    required this.programmeTitle,
    required this.order,
    this.summary,
    this.videoUrl,
    this.videoRecordId,
    this.markdownContent,
    required this.status,
    required this.completed,
    this.activityId,
    this.chapterMarkers = const [],
  });
  final String id;
  final String title;
  final String programmeId;
  final String programmeTitle;
  final int order;
  final String? summary;
  final String? videoUrl;
  final String? videoRecordId;
  final String? markdownContent;
  final String status;
  final bool completed;
  final String? activityId;
  final List<ChapterMarker> chapterMarkers;

  factory Lesson.fromJson(Map<String, dynamic> j) => Lesson(
        id: j['id'] as String,
        title: j['title'] as String,
        programmeId: (j['programme_id'] as String?) ?? '',
        programmeTitle: (j['programme_title'] as String?) ?? '',
        order: (j['order'] as int?) ?? 0,
        summary: j['summary'] as String?,
        videoUrl: j['video_url'] as String?,
        videoRecordId: j['video_record_id'] as String?,
        markdownContent: j['markdown_content'] as String?,
        status: (j['status'] as String?) ?? 'active',
        completed: (j['completed'] as bool?) ?? false,
        activityId: j['activity_id'] as String?,
        chapterMarkers: (j['chapter_markers'] as List? ?? [])
            .map((e) => ChapterMarker.fromJson(e as Map<String, dynamic>))
            .toList(),
      );
}

// params: {programme_id}
final lessonsProvider = FutureProvider.autoDispose.family<List<Lesson>, String>((ref, programmeId) async {
  final client = ref.read(apiClientProvider);
  final cache = ref.read(offlineCacheProvider);
  final cacheKey = 'lessons_$programmeId';
  List<Lesson> parse(dynamic d) {
    final raw = (d as Map<String, dynamic>)['results'] as List? ?? d as List? ?? [];
    return raw.map((e) => Lesson.fromJson(e as Map<String, dynamic>)).toList();
  }
  try {
    final res = await client.get<Map<String, dynamic>>('learn/programmes/$programmeId/lessons/');
    await cache.put(cacheKey, res.data!);
    final raw = res.data?['results'] as List? ?? res.data as List? ?? [];
    return raw.map((e) => Lesson.fromJson(e as Map<String, dynamic>)).toList();
  } catch (_) {
    return await cache.get<List<Lesson>>(cacheKey, parse) ?? [];
  }
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
  final client = ref.read(apiClientProvider);
  final cache = ref.read(offlineCacheProvider);
  final cacheKey = 'community_members_${params.entries.map((e) => '${e.key}=${e.value}').join('_')}';
  PageResult<Member> parse(dynamic d) {
    final m = d as Map<String, dynamic>;
    return PageResult(
      count: (m['count'] as int?) ?? 0,
      results: (m['results'] as List).map((e) => Member.fromJson(e as Map<String, dynamic>)).toList(),
    );
  }
  try {
    final res = await client.get<Map<String, dynamic>>('community/members/', params: params);
    await cache.put(cacheKey, res.data!);
    return parse(res.data!);
  } catch (_) {
    final cached = await cache.get<PageResult<Member>>(cacheKey, parse);
    if (cached != null) return cached;
    return const PageResult(count: 0, results: []);
  }
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
  final client = ref.read(apiClientProvider);
  final cache = ref.read(offlineCacheProvider);
  List<AppNotification> parse(dynamic d) {
    final raw = (d as Map<String, dynamic>)['results'] as List? ?? [];
    return raw.map((e) => AppNotification.fromJson(e as Map<String, dynamic>)).toList();
  }
  try {
    final res = await client.get<Map<String, dynamic>>('notifications/notifications/');
    await cache.put(CacheKeys.notifications, res.data!);
    final raw = (res.data?['results'] as List?) ?? [];
    return raw.map((e) => AppNotification.fromJson(e as Map<String, dynamic>)).toList();
  } catch (_) {
    return await cache.get<List<AppNotification>>(CacheKeys.notifications, parse) ?? [];
  }
});

final unreadCountProvider = FutureProvider.autoDispose<int>((ref) async {
  try {
    final res = await ref.read(apiClientProvider).get<Map<String, dynamic>>('notifications/notifications/unread-count/');
    return (res.data?['count'] as int?) ?? 0;
  } catch (_) {
    return 0;
  }
});

// ── Announcements & Gatherings ────────────────────────────────────────────────

class Announcement {
  const Announcement({
    required this.id,
    required this.title,
    required this.body,
    required this.createdAt,
    this.authorName,
  });
  final String id;
  final String title;
  final String body;
  final String createdAt;
  final String? authorName;
  factory Announcement.fromJson(Map<String, dynamic> j) => Announcement(
        id: j['id'] as String,
        title: (j['title'] as String?) ?? '',
        body: (j['body'] as String?) ?? '',
        createdAt: (j['created_at'] as String?) ?? '',
        authorName: j['author_name'] as String?,
      );
}

class Gathering {
  const Gathering({
    required this.id,
    required this.title,
    required this.startsAt,
    this.endsAt,
    this.location,
    this.description,
  });
  final String id;
  final String title;
  final String startsAt;
  final String? endsAt;
  final String? location;
  final String? description;
  factory Gathering.fromJson(Map<String, dynamic> j) => Gathering(
        id: j['id'] as String,
        title: (j['title'] as String?) ?? '',
        startsAt: (j['starts_at'] as String?) ?? '',
        endsAt: j['ends_at'] as String?,
        location: j['location'] as String?,
        description: j['description'] as String?,
      );
}

final announcementsProvider = FutureProvider.autoDispose<List<Announcement>>((ref) async {
  final client = ref.read(apiClientProvider);
  final cache = ref.read(offlineCacheProvider);
  const cacheKey = 'community_announcements';
  List<Announcement> parse(dynamic d) {
    final raw = (d as Map<String, dynamic>)['results'] as List? ?? d as List? ?? [];
    return raw.map((e) => Announcement.fromJson(e as Map<String, dynamic>)).toList();
  }
  try {
    final res = await client.get<Map<String, dynamic>>('community/announcements/');
    await cache.put(cacheKey, res.data!);
    return parse(res.data!);
  } catch (_) {
    return await cache.get<List<Announcement>>(cacheKey, parse) ?? [];
  }
});

final gatheringsProvider = FutureProvider.autoDispose<List<Gathering>>((ref) async {
  final client = ref.read(apiClientProvider);
  final cache = ref.read(offlineCacheProvider);
  const cacheKey = 'community_gatherings';
  List<Gathering> parse(dynamic d) {
    final raw = (d as Map<String, dynamic>)['results'] as List? ?? d as List? ?? [];
    return raw.map((e) => Gathering.fromJson(e as Map<String, dynamic>)).toList();
  }
  try {
    final res = await client.get<Map<String, dynamic>>('community/gatherings/');
    await cache.put(cacheKey, res.data!);
    return parse(res.data!);
  } catch (_) {
    return await cache.get<List<Gathering>>(cacheKey, parse) ?? [];
  }
});

// ── Coordinator (Level 3+) ────────────────────────────────────────────────────

class CertificationQueueItem {
  const CertificationQueueItem({
    required this.id,
    required this.candidateName,
    required this.candidateEmail,
    required this.programmeName,
    required this.currentLevel,
    required this.targetLevel,
    required this.submittedAt,
    required this.status,
  });
  final String id;
  final String candidateName;
  final String candidateEmail;
  final String programmeName;
  final int currentLevel;
  final int targetLevel;
  final String submittedAt;
  final String status;
  factory CertificationQueueItem.fromJson(Map<String, dynamic> j) =>
      CertificationQueueItem(
        id: j['id'] as String,
        candidateName: (j['candidate_name'] as String?) ?? '',
        candidateEmail: (j['candidate_email'] as String?) ?? '',
        programmeName: (j['programme_name'] as String?) ?? '',
        currentLevel: (j['current_level'] as int?) ?? 0,
        targetLevel: (j['target_level'] as int?) ?? 1,
        submittedAt: (j['submitted_at'] as String?) ?? '',
        status: (j['status'] as String?) ?? 'pending',
      );
}

class InductionQueueItem {
  const InductionQueueItem({
    required this.id,
    required this.applicantName,
    required this.applicantEmail,
    required this.submittedAt,
    required this.status,
    this.note,
  });
  final String id;
  final String applicantName;
  final String applicantEmail;
  final String submittedAt;
  final String status;
  final String? note;
  factory InductionQueueItem.fromJson(Map<String, dynamic> j) =>
      InductionQueueItem(
        id: j['id'] as String,
        applicantName: (j['applicant_name'] as String?) ?? '',
        applicantEmail: (j['applicant_email'] as String?) ?? '',
        submittedAt: (j['submitted_at'] as String?) ?? '',
        status: (j['status'] as String?) ?? 'pending',
        note: j['note'] as String?,
      );
}

final certificationQueueProvider = FutureProvider.autoDispose<List<CertificationQueueItem>>((ref) async {
  final client = ref.read(apiClientProvider);
  final cache = ref.read(offlineCacheProvider);
  const cacheKey = 'coordinator_cert_queue';
  List<CertificationQueueItem> parse(dynamic d) {
    final raw = (d as Map<String, dynamic>)['results'] as List? ?? d as List? ?? [];
    return raw.map((e) => CertificationQueueItem.fromJson(e as Map<String, dynamic>)).toList();
  }
  try {
    final res = await client.get<Map<String, dynamic>>('learn/certifications/queue/');
    await cache.put(cacheKey, res.data!);
    return parse(res.data!);
  } catch (_) {
    return await cache.get<List<CertificationQueueItem>>(cacheKey, parse) ?? [];
  }
});

final inductionQueueProvider = FutureProvider.autoDispose<List<InductionQueueItem>>((ref) async {
  final client = ref.read(apiClientProvider);
  final cache = ref.read(offlineCacheProvider);
  const cacheKey = 'coordinator_induction_queue';
  List<InductionQueueItem> parse(dynamic d) {
    final raw = (d as Map<String, dynamic>)['results'] as List? ?? d as List? ?? [];
    return raw.map((e) => InductionQueueItem.fromJson(e as Map<String, dynamic>)).toList();
  }
  try {
    final res = await client.get<Map<String, dynamic>>('community/membership-requests/');
    await cache.put(cacheKey, res.data!);
    return parse(res.data!);
  } catch (_) {
    return await cache.get<List<InductionQueueItem>>(cacheKey, parse) ?? [];
  }
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

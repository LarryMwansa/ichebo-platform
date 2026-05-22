import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/api/providers.dart';

// ── Models ────────────────────────────────────────────────────────────────────

class BibleBook {
  const BibleBook({
    required this.code,
    required this.name,
    required this.testament,
    required this.order,
  });

  final String code;
  final String name;
  final String testament; // 'OT' | 'NT'
  final int    order;

  factory BibleBook.fromJson(Map<String, dynamic> j) => BibleBook(
    code:      j['code']      as String,
    name:      j['name']      as String,
    testament: j['testament'] as String? ?? 'OT',
    order:     j['order']     as int?    ?? 0,
  );
}

class BibleVerse {
  const BibleVerse({
    required this.id,
    required this.chapter,
    required this.verse,
    required this.text,
    required this.bookCode,
    required this.bookName,
    this.translationCode = '',
  });

  final String id;
  final int    chapter;
  final int    verse;
  final String text;
  final String bookCode;
  final String bookName;
  final String translationCode;

  factory BibleVerse.fromJson(Map<String, dynamic> j) => BibleVerse(
    id:              j['id']               as String? ?? '',
    chapter:         j['chapter']          as int?    ?? 1,
    verse:           j['verse']            as int?    ?? 1,
    text:            j['text']             as String? ?? '',
    bookCode:        (j['book'] as Map<String, dynamic>?)?['code'] as String? ?? '',
    bookName:        (j['book'] as Map<String, dynamic>?)?['name'] as String? ?? '',
    translationCode: (j['translation'] as Map<String, dynamic>?)?['code'] as String? ?? '',
  );
}

class SearchResult {
  const SearchResult({
    required this.id,
    required this.reference,
    required this.bookCode,
    required this.bookName,
    required this.chapter,
    required this.verse,
    required this.text,
  });

  final String id;
  final String reference;
  final String bookCode;
  final String bookName;
  final int    chapter;
  final int    verse;
  final String text;

  factory SearchResult.fromJson(Map<String, dynamic> j) => SearchResult(
    id:        j['id']        as String? ?? '',
    reference: j['reference'] as String? ?? '',
    bookCode:  j['book_code'] as String? ?? '',
    bookName:  j['book_name'] as String? ?? '',
    chapter:   j['chapter']   as int?    ?? 1,
    verse:     j['verse']     as int?    ?? 1,
    text:      j['text']      as String? ?? '',
  );
}

// ── Navigation state ──────────────────────────────────────────────────────────

class BibleLocation {
  const BibleLocation({
    required this.bookCode,
    required this.bookName,
    required this.chapter,
    this.translationCode = 'KJV',
  });

  final String bookCode;
  final String bookName;
  final int    chapter;
  final String translationCode;

  BibleLocation copyWith({
    String? bookCode,
    String? bookName,
    int?    chapter,
    String? translationCode,
  }) => BibleLocation(
    bookCode:        bookCode        ?? this.bookCode,
    bookName:        bookName        ?? this.bookName,
    chapter:         chapter         ?? this.chapter,
    translationCode: translationCode ?? this.translationCode,
  );
}

final bibleLocationProvider = StateProvider<BibleLocation?>((_) => null);

// ── Remote data providers ─────────────────────────────────────────────────────

final bibleBooksProvider = FutureProvider<List<BibleBook>>((ref) async {
  final client = ref.watch(apiClientProvider);
  final data   = await client.get('/bible/books/') as List<dynamic>;
  return data
      .cast<Map<String, dynamic>>()
      .map(BibleBook.fromJson)
      .toList();
});

final bibleChaptersProvider =
    FutureProvider.family<List<int>, String>((ref, bookCode) async {
  final client = ref.watch(apiClientProvider);
  final data = await client.get('/bible/chapters/?book_code=$bookCode')
      as Map<String, dynamic>;
  final chapters = data['chapters'] as List<dynamic>? ?? [];
  return chapters.cast<int>();
});

// Fetches verses for a given location.
final bibleVersesProvider =
    FutureProvider.family<List<BibleVerse>, BibleLocation>((ref, loc) async {
  final client = ref.watch(apiClientProvider);
  final data = await client.get(
    '/bible/verses/?book_code=${loc.bookCode}'
    '&chapter=${loc.chapter}'
    '&translation_code=${loc.translationCode}',
  ) as List<dynamic>;
  return data.cast<Map<String, dynamic>>().map(BibleVerse.fromJson).toList();
});

// Search — only fires when query is non-empty.
final bibleSearchProvider =
    FutureProvider.family<List<SearchResult>, String>((ref, query) async {
  if (query.trim().length < 2) return [];
  final client = ref.watch(apiClientProvider);
  final data = await client.get(
    '/bible/search/?q=${Uri.encodeComponent(query)}',
  ) as Map<String, dynamic>;
  final results = data['results'] as List<dynamic>? ?? [];
  return results.cast<Map<String, dynamic>>().map(SearchResult.fromJson).toList();
});

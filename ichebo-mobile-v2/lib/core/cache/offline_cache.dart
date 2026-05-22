import 'dart:convert';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

// Simple key-value cache backed by SharedPreferences.
// Each entry stores the JSON string + a write timestamp.
// Stale entries are served when the network is unavailable.

final offlineCacheProvider = Provider<OfflineCache>((ref) => OfflineCache());

class OfflineCache {
  static const _tsPrefix = '__ts__';

  Future<void> put(String key, Object value) async {
    final prefs = await SharedPreferences.getInstance();
    final json = jsonEncode(value);
    await prefs.setString(key, json);
    await prefs.setInt(
      '$_tsPrefix$key',
      DateTime.now().millisecondsSinceEpoch,
    );
  }

  Future<T?> get<T>(String key, T Function(dynamic) fromJson) async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(key);
    if (raw == null) return null;
    try {
      return fromJson(jsonDecode(raw));
    } catch (_) {
      return null;
    }
  }

  Future<DateTime?> lastWritten(String key) async {
    final prefs = await SharedPreferences.getInstance();
    final ms = prefs.getInt('$_tsPrefix$key');
    if (ms == null) return null;
    return DateTime.fromMillisecondsSinceEpoch(ms);
  }

  Future<void> remove(String key) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(key);
    await prefs.remove('$_tsPrefix$key');
  }

  Future<void> clear() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.clear();
  }
}

// ── Cache keys ────────────────────────────────────────────────────────────────

class CacheKeys {
  CacheKeys._();
  static const paracleteDigest = 'paraclete_digest';
  static const bibleTranslations = 'bible_translations';
  static const bibleBooks = 'bible_books';
  static String bibleChapters(String bookCode) => 'bible_chapters_$bookCode';
  static String bibleVerses(String bookCode, int chapter, String translationCode) =>
      'bible_verses_${bookCode}_${chapter}_$translationCode';
  static const programmes = 'learn_programmes';
  static const myEnrolments = 'learn_enrolments';
  static const communityMembers = 'community_members';
  static const notifications = 'notifications';
  static const governanceRecords = 'governance_records';
}

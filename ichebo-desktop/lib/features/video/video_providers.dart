import 'dart:convert';
import 'dart:io';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:http/http.dart' as http;
import 'package:path_provider/path_provider.dart';
import 'package:path/path.dart' as p;
import '../../core/database/db.dart';
import 'video_models.dart';

// ── Video library provider ────────────────────────────────────────────────────

final videoLibraryProvider = FutureProvider<List<VideoRecord>>((ref) async {
  final db = await ref.watch(dbProvider.future);
  final rows = await db.query(
    'records',
    where: "record_family = 'media' AND deleted_at IS NULL",
    orderBy: 'created_at DESC',
  );
  return rows.map(VideoRecord.fromMap).toList();
});

// ── Selected video ────────────────────────────────────────────────────────────

final selectedVideoIdProvider = StateProvider<String?>((ref) => null);

final selectedVideoProvider = FutureProvider<VideoRecord?>((ref) async {
  final id = ref.watch(selectedVideoIdProvider);
  if (id == null) return null;
  final db = await ref.watch(dbProvider.future);
  final rows = await db.query('records', where: 'id = ?', whereArgs: [id], limit: 1);
  if (rows.isEmpty) return null;
  return VideoRecord.fromMap(rows.first);
});

// ── Offline download state ────────────────────────────────────────────────────

enum DownloadStatus { idle, downloading, done, error }

class DownloadState {
  const DownloadState({
    this.status = DownloadStatus.idle,
    this.progress = 0.0,
    this.error,
  });

  final DownloadStatus status;
  final double progress; // 0.0–1.0
  final String? error;

  DownloadState copyWith({DownloadStatus? status, double? progress, String? error}) =>
      DownloadState(
        status: status ?? this.status,
        progress: progress ?? this.progress,
        error: error ?? this.error,
      );
}

// Per-record download state notifier.
class DownloadNotifier extends StateNotifier<DownloadState> {
  DownloadNotifier(this._ref, this._recordId) : super(const DownloadState());

  final Ref _ref;
  final String _recordId;

  Future<void> download(String cdnUrl) async {
    if (state.status == DownloadStatus.downloading) return;
    state = const DownloadState(status: DownloadStatus.downloading);

    try {
      final dir = await getApplicationSupportDirectory();
      final destDir = Directory(p.join(dir.path, 'media', _recordId));
      await destDir.create(recursive: true);
      final destPath = p.join(destDir.path, '480p.ts');

      final client = http.Client();
      final request = http.Request('GET', Uri.parse(cdnUrl));
      final response = await client.send(request);

      if (response.statusCode != 200) {
        throw Exception('HTTP ${response.statusCode}');
      }

      final totalBytes = response.contentLength ?? 0;
      var received = 0;
      final sink = File(destPath).openWrite();

      await for (final chunk in response.stream) {
        sink.add(chunk);
        received += chunk.length;
        if (totalBytes > 0) {
          state = state.copyWith(
            status: DownloadStatus.downloading,
            progress: received / totalBytes,
          );
        }
      }
      await sink.close();
      client.close();

      // Persist local_file_path into custom_fields in SQLite.
      await _writeLocalFilePath(destPath);

      state = const DownloadState(status: DownloadStatus.done, progress: 1.0);

      // Invalidate so VideoRecord reloads with new local_file_path.
      _ref.invalidate(videoLibraryProvider);
      _ref.invalidate(selectedVideoProvider);
    } catch (e) {
      state = DownloadState(status: DownloadStatus.error, error: e.toString());
    }
  }

  Future<void> _writeLocalFilePath(String path) async {
    final db = await _ref.read(dbProvider.future);
    final rows = await db.query('records', where: 'id = ?', whereArgs: [_recordId], limit: 1);
    if (rows.isEmpty) return;
    final cfRaw = rows.first['custom_fields'] as String? ?? '{}';
    Map<String, dynamic> cf;
    try {
      cf = jsonDecode(cfRaw) as Map<String, dynamic>;
    } catch (_) {
      cf = {};
    }
    cf['local_file_path'] = path;
    await db.update(
      'records',
      {'custom_fields': jsonEncode(cf)},
      where: 'id = ?',
      whereArgs: [_recordId],
    );
  }
}

final downloadProvider =
    StateNotifierProvider.family<DownloadNotifier, DownloadState, String>(
  (ref, recordId) => DownloadNotifier(ref, recordId),
);

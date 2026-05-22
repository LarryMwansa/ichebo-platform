import 'dart:convert';

class ChapterMarker {
  const ChapterMarker({required this.timestampSeconds, required this.title});

  final int timestampSeconds;
  final String title;

  factory ChapterMarker.fromJson(Map<String, dynamic> j) => ChapterMarker(
        timestampSeconds: (j['timestamp_seconds'] as num).toInt(),
        title: j['title'] as String? ?? '',
      );

  static List<ChapterMarker> listFromJson(String raw) {
    try {
      final list = jsonDecode(raw) as List<dynamic>;
      return list.map((e) => ChapterMarker.fromJson(e as Map<String, dynamic>)).toList();
    } catch (_) {
      return [];
    }
  }
}

// A video record is a Record row with record_family=media.
class VideoRecord {
  const VideoRecord({
    required this.id,
    required this.title,
    required this.recordType,
    required this.status,
    this.videoUrl,
    this.thumbnailUrl,
    this.durationSeconds,
    this.localFilePath,
    this.chapterMarkers = const [],
  });

  final String id;
  final String title;
  final String recordType; // 'teaching_video' | 'learning_video' | 'broadcast'
  final String status;
  final String? videoUrl;
  final String? thumbnailUrl;
  final int? durationSeconds;
  final String? localFilePath; // custom_fields.local_file_path — offline cache
  final List<ChapterMarker> chapterMarkers; // custom_fields.chapter_markers

  bool get isLearning => recordType == 'learning_video';
  bool get isOfflineAvailable => localFilePath != null && localFilePath!.isNotEmpty;

  factory VideoRecord.fromMap(Map<String, dynamic> m) {
    final cf = _parseJson(m['custom_fields'] as String? ?? '{}');
    final meta = _parseJson(m['metadata'] as String? ?? '{}');
    return VideoRecord(
      id: m['id'] as String,
      title: m['title'] as String? ?? '',
      recordType: m['record_type'] as String? ?? 'teaching_video',
      status: m['status'] as String? ?? 'published',
      videoUrl: meta['video_url'] as String?,
      thumbnailUrl: meta['thumbnail_url'] as String?,
      durationSeconds: (meta['duration_seconds'] as num?)?.toInt(),
      localFilePath: cf['local_file_path'] as String?,
      chapterMarkers: ChapterMarker.listFromJson(
        cf['chapter_markers'] is String
            ? cf['chapter_markers'] as String
            : jsonEncode(cf['chapter_markers'] ?? []),
      ),
    );
  }

  static Map<String, dynamic> _parseJson(String raw) {
    try {
      return jsonDecode(raw) as Map<String, dynamic>;
    } catch (_) {
      return {};
    }
  }
}

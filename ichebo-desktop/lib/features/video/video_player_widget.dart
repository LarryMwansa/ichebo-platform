import 'dart:io';
import 'package:chewie/chewie.dart';
import 'package:flutter/material.dart';
import 'package:video_player/video_player.dart';
import '../../core/theme/tokens.dart';
import 'video_models.dart';
import 'video_progress_tracker.dart';

class IcheboVideoPlayer extends StatefulWidget {
  const IcheboVideoPlayer({
    super.key,
    required this.record,
    this.tracker,
  });

  final VideoRecord record;
  final VideoProgressTracker? tracker;

  @override
  State<IcheboVideoPlayer> createState() => _IcheboVideoPlayerState();
}

class _IcheboVideoPlayerState extends State<IcheboVideoPlayer> {
  VideoPlayerController? _controller;
  ChewieController? _chewieController;
  bool _initialized = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _init();
  }

  @override
  void didUpdateWidget(IcheboVideoPlayer old) {
    super.didUpdateWidget(old);
    if (old.record.id != widget.record.id) {
      _dispose();
      _init();
    }
  }

  Future<void> _init() async {
    final record = widget.record;
    // Prefer local file if offline download exists.
    final Uri uri;
    if (record.isOfflineAvailable) {
      uri = Uri.file(record.localFilePath!);
    } else if (record.videoUrl != null && record.videoUrl!.isNotEmpty) {
      uri = Uri.parse(record.videoUrl!);
    } else {
      setState(() => _error = 'No video source available.');
      return;
    }

    final controller = record.isOfflineAvailable
        ? VideoPlayerController.file(File(record.localFilePath!))
        : VideoPlayerController.networkUrl(uri);

    try {
      await controller.initialize();
    } catch (e) {
      setState(() => _error = 'Failed to load video: $e');
      controller.dispose();
      return;
    }

    // Progress tracking — fire milestones as playback advances.
    if (widget.tracker != null) {
      controller.addListener(() {
        final pos = controller.value.position.inSeconds;
        widget.tracker!.onProgress(pos);
      });
    }

    final chewie = ChewieController(
      videoPlayerController: controller,
      autoPlay: false,
      looping: false,
      aspectRatio: 16 / 9,
      additionalOptions: (ctx) => [],
      customControls: const MaterialControls(),
    );

    if (!mounted) {
      controller.dispose();
      chewie.dispose();
      return;
    }

    setState(() {
      _controller = controller;
      _chewieController = chewie;
      _initialized = true;
      _error = null;
    });
  }

  void _dispose() {
    _chewieController?.dispose();
    _controller?.dispose();
    _chewieController = null;
    _controller = null;
    _initialized = false;
    _error = null;
  }

  @override
  void dispose() {
    _dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (_error != null) {
      return _ErrorState(message: _error!);
    }
    if (!_initialized) {
      return const Center(child: CircularProgressIndicator());
    }
    return AspectRatio(
      aspectRatio: 16 / 9,
      child: Chewie(controller: _chewieController!),
    );
  }
}

// ── Chapter navigator ─────────────────────────────────────────────────────────

class ChapterNavigator extends StatelessWidget {
  const ChapterNavigator({
    super.key,
    required this.chapters,
    required this.controller,
  });

  final List<ChapterMarker> chapters;
  final VideoPlayerController controller;

  @override
  Widget build(BuildContext context) {
    if (chapters.isEmpty) return const SizedBox.shrink();

    final isDark = Theme.of(context).brightness == Brightness.dark;
    final border = isDark ? IcsColors.borderDark : IcsColors.borderLight;
    final textMuted = isDark ? IcsColors.textMutedDark : IcsColors.textMuted;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          child: Text(
            'Chapters',
            style: Theme.of(context).textTheme.labelLarge?.copyWith(color: textMuted),
          ),
        ),
        Container(
          decoration: BoxDecoration(
            border: Border(top: BorderSide(color: border)),
          ),
          child: ListView.separated(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            itemCount: chapters.length,
            separatorBuilder: (_, _) => Divider(height: 1, color: border),
            itemBuilder: (context, i) {
              final ch = chapters[i];
              final min = ch.timestampSeconds ~/ 60;
              final sec = ch.timestampSeconds % 60;
              final timestamp = '${min.toString().padLeft(2, '0')}:${sec.toString().padLeft(2, '0')}';

              return InkWell(
                onTap: () => controller.seekTo(Duration(seconds: ch.timestampSeconds)),
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                  child: Row(
                    children: [
                      Text(
                        timestamp,
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                              color: IcsColors.accentRed,
                              fontFeatures: const [FontFeature.tabularFigures()],
                            ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          ch.title,
                          style: Theme.of(context).textTheme.bodyMedium,
                        ),
                      ),
                    ],
                  ),
                ),
              );
            },
          ),
        ),
      ],
    );
  }
}

class _ErrorState extends StatelessWidget {
  const _ErrorState({required this.message});
  final String message;

  @override
  Widget build(BuildContext context) {
    return AspectRatio(
      aspectRatio: 16 / 9,
      child: Container(
        color: Colors.black,
        child: Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.error_outline, color: IcsColors.error, size: 40),
              const SizedBox(height: 8),
              Text(message, style: const TextStyle(color: Colors.white70)),
            ],
          ),
        ),
      ),
    );
  }
}


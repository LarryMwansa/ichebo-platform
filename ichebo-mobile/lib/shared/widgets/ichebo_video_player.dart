import 'package:chewie/chewie.dart';
import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:video_player/video_player.dart';

import '../../shared/tokens/tokens.dart';
import 'chapter_navigator.dart';
import 'video_progress_tracker.dart';

class IcheboVideoPlayer extends StatefulWidget {
  const IcheboVideoPlayer({
    super.key,
    required this.videoUrl,
    this.aspectRatio,
    this.activityId,
    this.videoRecordId,
    this.chapters,
    this.onComplete,
  });

  final String videoUrl;
  final double? aspectRatio;
  final String? activityId;
  final String? videoRecordId;
  final List<ChapterMarker>? chapters;
  final VoidCallback? onComplete;

  @override
  State<IcheboVideoPlayer> createState() => _IcheboVideoPlayerState();
}

class _IcheboVideoPlayerState extends State<IcheboVideoPlayer> {
  VideoPlayerController? _vpController;
  ChewieController? _chewieController;
  VideoProgressTracker? _tracker;
  bool _isHls = false;
  bool _initialized = false;
  int _currentPositionSeconds = 0;

  @override
  void initState() {
    super.initState();
    _isHls = _urlIsHls(widget.videoUrl);
    if (_isHls) {
      _initHlsPlayer();
    }
  }

  bool _urlIsHls(String url) {
    final lower = url.toLowerCase();
    return lower.contains('.m3u8') || lower.contains('cdn.ichebo.org');
  }

  bool _urlIsExternal(String url) {
    return url.contains('youtube.com') ||
        url.contains('youtu.be') ||
        url.contains('vimeo.com');
  }

  Future<void> _initHlsPlayer() async {
    _vpController = VideoPlayerController.networkUrl(Uri.parse(widget.videoUrl));
    await _vpController!.initialize();

    final totalSecs = _vpController!.value.duration.inSeconds;

    if (widget.activityId != null && widget.videoRecordId != null && totalSecs > 0) {
      _tracker = VideoProgressTracker(
        activityId: widget.activityId!,
        videoRecordId: widget.videoRecordId!,
        totalSeconds: totalSecs,
        onComplete: widget.onComplete,
      );
    }

    _chewieController = ChewieController(
      videoPlayerController: _vpController!,
      aspectRatio: widget.aspectRatio ?? 16 / 9,
      autoPlay: false,
      looping: false,
      allowFullScreen: true,
      allowPlaybackSpeedChanging: true,
      playbackSpeeds: const [0.75, 1.0, 1.25, 1.5, 2.0],
      materialProgressColors: ChewieProgressColors(
        playedColor: IcheboColors.primary,
        handleColor: IcheboColors.primary,
        bufferedColor: IcheboColors.primary.withValues(alpha: 0.3),
        backgroundColor: IcheboColors.darkBorder,
      ),
    );

    if (_tracker != null) {
      _vpController!.addListener(_onVideoProgress);
    }

    if (mounted) setState(() => _initialized = true);
  }

  void _onVideoProgress() {
    if (_vpController == null || !_vpController!.value.isInitialized) return;
    final pos = _vpController!.value.position.inSeconds;
    if (pos != _currentPositionSeconds) {
      setState(() => _currentPositionSeconds = pos);
      _tracker?.onProgress(pos);
    }
  }

  @override
  void dispose() {
    _vpController?.removeListener(_onVideoProgress);
    _chewieController?.dispose();
    _vpController?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (!_isHls) {
      return _ExternalVideoCard(
        url: widget.videoUrl,
        isExternal: _urlIsExternal(widget.videoUrl),
      );
    }

    if (!_initialized) {
      return AspectRatio(
        aspectRatio: widget.aspectRatio ?? 16 / 9,
        child: Container(
          color: Colors.black,
          child: const Center(
            child: CircularProgressIndicator(color: IcheboColors.primary),
          ),
        ),
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        AspectRatio(
          aspectRatio: widget.aspectRatio ?? 16 / 9,
          child: Chewie(controller: _chewieController!),
        ),
        if (widget.chapters != null && widget.chapters!.isNotEmpty) ...[
          const SizedBox(height: IcheboSpacing.xs3),
          ChapterNavigator(
            chapters: widget.chapters!,
            controller: _vpController!,
            currentPositionSeconds: _currentPositionSeconds,
          ),
        ],
      ],
    );
  }
}

class _ExternalVideoCard extends StatelessWidget {
  const _ExternalVideoCard({required this.url, required this.isExternal});
  final String url;
  final bool isExternal;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: () async {
        final uri = Uri.tryParse(url);
        if (uri != null && await canLaunchUrl(uri)) {
          await launchUrl(uri, mode: LaunchMode.externalApplication);
        }
      },
      child: Container(
        height: 180,
        decoration: BoxDecoration(
          color: Colors.black,
          borderRadius: IcheboRadius.m,
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.play_circle_outline, color: Colors.white, size: 48),
            const SizedBox(height: IcheboSpacing.xs3),
            Text(
              isExternal ? 'Open in YouTube / Vimeo' : 'Play video',
              style: IcheboTextStyles.bodySmall.copyWith(color: Colors.white70),
            ),
          ],
        ),
      ),
    );
  }
}

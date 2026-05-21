import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../core/theme/tokens.dart';
import '../sync/sync_engine.dart';
import '../sync/sync_state.dart';

// ── Sync status bar ───────────────────────────────────────────────────────────
// Persistent bottom bar on the Stage — four states matching DOC-C §3.10.
// Sits below the stage canvas, above the window edge.

class SyncBar extends ConsumerWidget {
  const SyncBar({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final status = ref.watch(syncStateProvider);
    final notifier = ref.read(syncStateProvider.notifier);
    final isDark = Theme.of(context).brightness == Brightness.dark;

    final bgColor = isDark
        ? const Color(0xFF1A1A1A)
        : IcsColors.stone2;
    final borderColor = isDark ? IcsColors.borderDark : IcsColors.borderLight;

    return Container(
      height: 28,
      decoration: BoxDecoration(
        color: bgColor,
        border: Border(top: BorderSide(color: borderColor, width: 1)),
      ),
      padding: const EdgeInsets.symmetric(horizontal: IcsSpacing.l),
      child: Row(
        children: [
          _StatusIndicator(state: status.state),
          const SizedBox(width: IcsSpacing.xs),
          _StatusLabel(status: status, isDark: isDark),
          const Spacer(),
          if (status.conflictCount > 0) ...[
            _ConflictBadge(count: status.conflictCount),
            const SizedBox(width: IcsSpacing.s),
          ],
          if (status.pendingCount > 0) ...[
            _PendingLabel(count: status.pendingCount, isDark: isDark),
            const SizedBox(width: IcsSpacing.s),
          ],
          _SyncNowButton(
            onTap: notifier.triggerSync,
            enabled: status.state != SyncState.syncing,
            isDark: isDark,
          ),
        ],
      ),
    );
  }
}

// ── State indicator dot / spinner ─────────────────────────────────────────────

class _StatusIndicator extends StatelessWidget {
  const _StatusIndicator({required this.state});
  final SyncState state;

  @override
  Widget build(BuildContext context) {
    if (state == SyncState.syncing) {
      return SizedBox(
        width: 10,
        height: 10,
        child: CircularProgressIndicator(
          strokeWidth: 1.5,
          color: _dotColor,
        ),
      );
    }
    return Container(
      width: 7,
      height: 7,
      decoration: BoxDecoration(
        color: _dotColor,
        shape: BoxShape.circle,
        boxShadow: state == SyncState.synced
            ? [BoxShadow(color: _dotColor.withValues(alpha: 0.4), blurRadius: 4)]
            : null,
      ),
    );
  }

  Color get _dotColor => switch (state) {
        SyncState.synced => IcsColors.success,
        SyncState.syncing => IcsColors.info,
        SyncState.conflict => IcsColors.warning,
        SyncState.blocked => IcsColors.error,
        SyncState.offline => const Color(0xFF666666),
      };
}

// ── Status label ──────────────────────────────────────────────────────────────

class _StatusLabel extends StatelessWidget {
  const _StatusLabel({required this.status, required this.isDark});
  final SyncStatusModel status;
  final bool isDark;

  String get _text => switch (status.state) {
        SyncState.synced => 'Up to date',
        SyncState.syncing => 'Syncing…',
        SyncState.conflict => 'Conflicts need attention',
        SyncState.blocked => 'Sync blocked',
        SyncState.offline => 'Offline',
      };

  @override
  Widget build(BuildContext context) {
    return Text(
      _text,
      style: TextStyle(
        fontSize: 11,
        fontWeight: FontWeight.w500,
        color: isDark
            ? IcsColors.textMutedDark
            : IcsColors.textMuted,
      ),
    );
  }
}

// ── Conflict badge ────────────────────────────────────────────────────────────

class _ConflictBadge extends StatelessWidget {
  const _ConflictBadge({required this.count});
  final int count;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: IcsSpacing.xs, vertical: 1),
      decoration: BoxDecoration(
        color: IcsColors.warning.withValues(alpha: 0.15),
        borderRadius: BorderRadius.all(IcsRadius.full),
        border: Border.all(color: IcsColors.warning.withValues(alpha: 0.3)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.warning_amber_outlined, size: 10, color: IcsColors.warning),
          const SizedBox(width: 3),
          Text(
            '$count ${count == 1 ? 'conflict' : 'conflicts'}',
            style: TextStyle(
              fontSize: 10,
              fontWeight: FontWeight.w700,
              color: IcsColors.warning,
            ),
          ),
        ],
      ),
    );
  }
}

// ── Pending count label ───────────────────────────────────────────────────────

class _PendingLabel extends StatelessWidget {
  const _PendingLabel({required this.count, required this.isDark});
  final int count;
  final bool isDark;

  @override
  Widget build(BuildContext context) {
    return Text(
      '$count pending',
      style: TextStyle(
        fontSize: 10,
        color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted,
      ),
    );
  }
}

// ── Sync now button ───────────────────────────────────────────────────────────

class _SyncNowButton extends StatefulWidget {
  const _SyncNowButton({
    required this.onTap,
    required this.enabled,
    required this.isDark,
  });
  final VoidCallback onTap;
  final bool enabled;
  final bool isDark;

  @override
  State<_SyncNowButton> createState() => _SyncNowButtonState();
}

class _SyncNowButtonState extends State<_SyncNowButton> {
  bool _hovered = false;

  @override
  Widget build(BuildContext context) {
    final color = widget.enabled
        ? (_hovered ? IcsColors.accentRed : (widget.isDark ? IcsColors.textMutedDark : IcsColors.textMuted))
        : (widget.isDark ? IcsColors.textMutedDark.withValues(alpha: 0.4) : IcsColors.textMuted.withValues(alpha: 0.4));

    return MouseRegion(
      onEnter: (_) => setState(() => _hovered = true),
      onExit: (_) => setState(() => _hovered = false),
      child: GestureDetector(
        onTap: widget.enabled ? widget.onTap : null,
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.sync, size: 12, color: color),
            const SizedBox(width: 3),
            Text(
              'Sync now',
              style: TextStyle(
                fontSize: 10,
                fontWeight: FontWeight.w600,
                color: color,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

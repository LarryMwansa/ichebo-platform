import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/theme/tokens.dart';
import '../../sync/sync_engine.dart';
import 'sync_providers.dart';

class ConflictTile extends ConsumerStatefulWidget {
  const ConflictTile({super.key, required this.entry, required this.isDark});
  final ConflictEntry entry;
  final bool isDark;

  @override
  ConsumerState<ConflictTile> createState() => _ConflictTileState();
}

class _ConflictTileState extends ConsumerState<ConflictTile> {
  bool _resolving = false;
  String? _error;

  Future<void> _resolve(bool keepLocal) async {
    setState(() { _resolving = true; _error = null; });
    final code = SyncEngine.instance.resolveConflict(
      widget.entry.id,
      keepLocal: keepLocal,
    );
    if (!mounted) return;
    if (code == 0 || code == -99) {
      ref.invalidate(conflictsProvider);
    } else {
      setState(() { _resolving = false; _error = 'Could not resolve (code $code). Try again.'; });
    }
  }

  @override
  Widget build(BuildContext context) {
    final e = widget.entry;
    final isDark = widget.isDark;
    final localSummary  = ConflictEntry.summarise(e.localVersion);
    final cloudSummary  = ConflictEntry.summarise(e.cloudVersion);

    return Container(
      margin: const EdgeInsets.symmetric(horizontal: IcsSpacing.m, vertical: IcsSpacing.xs),
      decoration: BoxDecoration(
        color: isDark ? IcsColors.ink2 : Colors.white,
        borderRadius: BorderRadius.circular(8),
        border: Border(
          left: const BorderSide(color: IcsColors.warning, width: 3),
          top:    BorderSide(color: isDark ? IcsColors.borderDark : IcsColors.borderLight),
          right:  BorderSide(color: isDark ? IcsColors.borderDark : IcsColors.borderLight),
          bottom: BorderSide(color: isDark ? IcsColors.borderDark : IcsColors.borderLight),
        ),
      ),
      child: Padding(
        padding: const EdgeInsets.all(IcsSpacing.m),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // ── Entity header ────────────────────────────────────────────
            Row(
              children: [
                _EntityBadge(type: e.entityType),
                const SizedBox(width: IcsSpacing.s),
                Expanded(
                  child: Text(
                    e.entityId.length > 8
                        ? '…${e.entityId.substring(e.entityId.length - 8)}'
                        : e.entityId,
                    style: TextStyle(
                      fontSize: 11, fontFamily: 'monospace',
                      color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted,
                    ),
                  ),
                ),
                Text(
                  _fmtDate(e.createdAt),
                  style: TextStyle(
                    fontSize: 10,
                    color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted,
                  ),
                ),
              ],
            ),
            const SizedBox(height: IcsSpacing.s),
            // ── Version rows ─────────────────────────────────────────────
            _VersionRow(
              label: 'Local',
              summary: localSummary,
              color: IcsColors.info,
              isDark: isDark,
            ),
            const SizedBox(height: 4),
            _VersionRow(
              label: 'Cloud',
              summary: cloudSummary,
              color: IcsColors.warning,
              isDark: isDark,
            ),
            if (_error != null) ...[
              const SizedBox(height: IcsSpacing.xs),
              Text(_error!, style: const TextStyle(fontSize: 11, color: IcsColors.error)),
            ],
            const SizedBox(height: IcsSpacing.m),
            // ── Actions ──────────────────────────────────────────────────
            _resolving
                ? const Center(child: SizedBox(width: 20, height: 20,
                    child: CircularProgressIndicator(strokeWidth: 2, color: IcsColors.accentRed)))
                : Row(
                    children: [
                      Expanded(
                        child: OutlinedButton(
                          onPressed: () => _resolve(true),
                          style: OutlinedButton.styleFrom(
                            foregroundColor: IcsColors.info,
                            side: const BorderSide(color: IcsColors.info),
                            padding: const EdgeInsets.symmetric(vertical: 6),
                            textStyle: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
                          ),
                          child: const Text('Keep mine'),
                        ),
                      ),
                      const SizedBox(width: IcsSpacing.s),
                      Expanded(
                        child: OutlinedButton(
                          onPressed: () => _resolve(false),
                          style: OutlinedButton.styleFrom(
                            foregroundColor: IcsColors.warning,
                            side: const BorderSide(color: IcsColors.warning),
                            padding: const EdgeInsets.symmetric(vertical: 6),
                            textStyle: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
                          ),
                          child: const Text('Accept theirs'),
                        ),
                      ),
                    ],
                  ),
          ],
        ),
      ),
    );
  }

  String _fmtDate(DateTime dt) {
    final months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
    return '${dt.day} ${months[dt.month - 1]}  '
        '${dt.hour.toString().padLeft(2,'0')}:${dt.minute.toString().padLeft(2,'0')}';
  }
}

// ── Entity type badge ─────────────────────────────────────────────────────────

class _EntityBadge extends StatelessWidget {
  const _EntityBadge({required this.type});
  final String type;

  @override
  Widget build(BuildContext context) {
    final (label, color) = switch (type) {
      'member'   => ('Member',   IcsColors.accentRed),
      'activity' => ('Activity', const Color(0xFF2563EB)),
      'record'   => ('Record',   const Color(0xFF059669)),
      _          => (type,       const Color(0xFF9E9E9E)),
    };
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: IcsSpacing.s, vertical: 2),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(4),
        border: Border.all(color: color.withValues(alpha: 0.3)),
      ),
      child: Text(
        label,
        style: TextStyle(fontSize: 10, fontWeight: FontWeight.w700, color: color),
      ),
    );
  }
}

// ── Version summary row ───────────────────────────────────────────────────────

class _VersionRow extends StatelessWidget {
  const _VersionRow({
    required this.label,
    required this.summary,
    required this.color,
    required this.isDark,
  });
  final String label;
  final String summary;
  final Color color;
  final bool isDark;

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          width: 42,
          padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 1),
          decoration: BoxDecoration(
            color: color.withValues(alpha: 0.08),
            borderRadius: BorderRadius.circular(3),
          ),
          child: Text(
            label,
            style: TextStyle(fontSize: 10, fontWeight: FontWeight.w700, color: color),
          ),
        ),
        const SizedBox(width: IcsSpacing.s),
        Expanded(
          child: Text(
            summary,
            style: TextStyle(
              fontSize: 12,
              color: isDark ? Colors.white.withValues(alpha: 0.85) : IcsColors.inkBg,
            ),
          ),
        ),
      ],
    );
  }
}

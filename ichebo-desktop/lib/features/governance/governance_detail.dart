import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/theme/tokens.dart';
import 'governance_providers.dart';

class GovernanceDetail extends ConsumerWidget {
  const GovernanceDetail({super.key, required this.recordId});
  final String recordId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final recAsync = ref.watch(governanceByIdProvider(recordId));
    final isDark   = Theme.of(context).brightness == Brightness.dark;

    return recAsync.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error:   (e, _) => Center(child: Text('Error: $e')),
      data: (record) {
        if (record == null) {
          return Center(child: Text('Record not found.',
              style: TextStyle(
                  color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted)));
        }
        return SingleChildScrollView(
          padding: const EdgeInsets.all(IcsSpacing.l),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              _RecordHeader(record: record, isDark: isDark),
              const SizedBox(height: IcsSpacing.l),
              _MetaCard(record: record, isDark: isDark),
              if (record.body != null && record.body!.isNotEmpty) ...[
                const SizedBox(height: IcsSpacing.m),
                _BodyCard(body: record.body!, isDark: isDark),
              ],
              const SizedBox(height: IcsSpacing.l),
              _ReadOnlyNotice(isDark: isDark),
            ],
          ),
        );
      },
    );
  }
}

// ── Header ────────────────────────────────────────────────────────────────────

class _RecordHeader extends StatelessWidget {
  const _RecordHeader({required this.record, required this.isDark});
  final GovernanceRecord record;
  final bool isDark;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _FamilyBadge(family: record.recordFamily),
        const SizedBox(height: IcsSpacing.s),
        Text(record.title,
            style: TextStyle(fontFamily: 'Playfair Display',
                fontSize: 20, fontWeight: FontWeight.w700,
                color: isDark ? Colors.white : IcsColors.inkBg)),
        const SizedBox(height: IcsSpacing.xs),
        Row(children: [
          Container(width: 7, height: 7,
              decoration: BoxDecoration(
                  color: _statusColor(record.status), shape: BoxShape.circle)),
          const SizedBox(width: 4),
          Text(_statusLabel(record.status),
              style: TextStyle(fontSize: 12, color: _statusColor(record.status))),
        ]),
      ],
    );
  }

  static Color _statusColor(String s) => switch (s) {
        'active'     => IcsColors.success,
        'locked'     => IcsColors.info,
        'superseded' => const Color(0xFF9E9E9E),
        'draft'      => IcsColors.warning,
        _            => const Color(0xFF9E9E9E),
      };

  static String _statusLabel(String s) => switch (s) {
        'active'     => 'Active',
        'locked'     => 'Locked',
        'superseded' => 'Superseded',
        'draft'      => 'Draft',
        _            => s,
      };
}

// ── Meta card ─────────────────────────────────────────────────────────────────

class _MetaCard extends StatelessWidget {
  const _MetaCard({required this.record, required this.isDark});
  final GovernanceRecord record;
  final bool isDark;

  String _fmtDate(String? iso) {
    if (iso == null || iso.isEmpty) return '—';
    try {
      final dt = DateTime.parse(iso).toLocal();
      final months = ['Jan','Feb','Mar','Apr','May','Jun',
                      'Jul','Aug','Sep','Oct','Nov','Dec'];
      return '${dt.day} ${months[dt.month - 1]} ${dt.year}';
    } catch (_) { return iso; }
  }

  @override
  Widget build(BuildContext context) {
    return _Card(title: 'Details', isDark: isDark, child: Column(children: [
      _Row('Family',   _familyLabel(record.recordFamily), isDark),
      const SizedBox(height: IcsSpacing.s),
      _Row('Type',     record.typeLabel, isDark),
      const SizedBox(height: IcsSpacing.s),
      _Row('Class',    'Governance', isDark),
      const SizedBox(height: IcsSpacing.s),
      _Row('Updated',  _fmtDate(record.updatedAt), isDark),
    ]));
  }

  static String _familyLabel(String f) => switch (f) {
        'reference' => 'Reference Library',
        'mandate'   => 'Mandate Branch',
        'keys'      => 'Keys Library',
        _           => f,
      };
}

// ── Body card ─────────────────────────────────────────────────────────────────

class _BodyCard extends StatelessWidget {
  const _BodyCard({required this.body, required this.isDark});
  final String body;
  final bool isDark;

  @override
  Widget build(BuildContext context) {
    return _Card(title: 'Content', isDark: isDark,
      child: SelectableText(body,
          style: TextStyle(fontSize: 13, height: 1.6,
              color: isDark ? Colors.white.withValues(alpha: 0.9) : IcsColors.inkBg)));
  }
}

// ── Read-only notice ──────────────────────────────────────────────────────────

class _ReadOnlyNotice extends StatelessWidget {
  const _ReadOnlyNotice({required this.isDark});
  final bool isDark;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(
          horizontal: IcsSpacing.m, vertical: IcsSpacing.s),
      decoration: BoxDecoration(
        color: isDark ? const Color(0xFF1A1A1A) : IcsColors.stone2,
        borderRadius: BorderRadius.circular(6),
        border: Border.all(
            color: isDark ? IcsColors.borderDark : IcsColors.borderLight),
      ),
      child: Row(children: [
        Icon(Icons.lock_outline, size: 14,
            color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted),
        const SizedBox(width: IcsSpacing.s),
        Expanded(child: Text(
            'Governance content is read-only on Desktop. '
            'To author records, use Ichebo Web.',
            style: TextStyle(fontSize: 11,
                color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted))),
      ]),
    );
  }
}

// ── Family badge ──────────────────────────────────────────────────────────────

class _FamilyBadge extends StatelessWidget {
  const _FamilyBadge({required this.family});
  final String family;

  @override
  Widget build(BuildContext context) {
    final (label, color) = switch (family) {
      'reference' => ('Reference Library', const Color(0xFF2563EB)),
      'mandate'   => ('Mandate Branch',    IcsColors.warning),
      'keys'      => ('Keys Library',      IcsColors.accentRed),
      _           => (family,              const Color(0xFF9E9E9E)),
    };
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: IcsSpacing.s, vertical: 3),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(4),
        border: Border.all(color: color.withValues(alpha: 0.3)),
      ),
      child: Text(label,
          style: TextStyle(fontSize: 10, fontWeight: FontWeight.w700, color: color)),
    );
  }
}

// ── Shared card chrome ────────────────────────────────────────────────────────

class _Card extends StatelessWidget {
  const _Card({required this.title, required this.isDark, required this.child});
  final String title;
  final bool isDark;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: isDark ? IcsColors.ink2 : Colors.white,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
            color: isDark ? IcsColors.borderDark : IcsColors.borderLight),
      ),
      child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(
              IcsSpacing.m, IcsSpacing.m, IcsSpacing.m, IcsSpacing.s),
          child: Text(title.toUpperCase(),
              style: TextStyle(fontSize: 10, fontWeight: FontWeight.w700,
                  letterSpacing: 0.8,
                  color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted)),
        ),
        Divider(height: 1,
            color: isDark ? IcsColors.borderDark : IcsColors.borderLight),
        Padding(padding: const EdgeInsets.all(IcsSpacing.m), child: child),
      ]),
    );
  }
}

class _Row extends StatelessWidget {
  const _Row(this.label, this.value, this.isDark);
  final String label, value;
  final bool isDark;

  @override
  Widget build(BuildContext context) => Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(width: 90,
              child: Text(label, style: TextStyle(fontSize: 12,
                  color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted))),
          Expanded(child: Text(value, style: TextStyle(fontSize: 13,
              color: isDark ? Colors.white : IcsColors.inkBg))),
        ],
      );
}

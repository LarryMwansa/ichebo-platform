import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/theme/tokens.dart';
import 'governance_providers.dart';

class GovernanceList extends ConsumerWidget {
  const GovernanceList({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final byFamily   = ref.watch(governanceByFamilyProvider);
    final filtered   = ref.watch(filteredGovernanceProvider);
    final search     = ref.watch(governanceSearchProvider);
    final selectedId = ref.watch(selectedGovernanceIdProvider);
    final isDark     = Theme.of(context).brightness == Brightness.dark;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        // ── Search bar ────────────────────────────────────────────────
        Padding(
          padding: const EdgeInsets.fromLTRB(
              IcsSpacing.m, IcsSpacing.m, IcsSpacing.m, IcsSpacing.s),
          child: _GovernanceSearch(value: search, isDark: isDark,
            onChanged: (v) => ref.read(governanceSearchProvider.notifier).state = v),
        ),
        Divider(height: 1, color: isDark ? IcsColors.borderDark : IcsColors.borderLight),
        // ── List ──────────────────────────────────────────────────────
        Expanded(
          child: search.isNotEmpty
              ? _FlatList(filtered: filtered, selectedId: selectedId, isDark: isDark)
              : _GroupedList(byFamily: byFamily, selectedId: selectedId, isDark: isDark),
        ),
        // ── Footer ───────────────────────────────────────────────────
        ref.watch(governanceRecordsProvider).maybeWhen(
          data: (records) => Container(
            height: 28,
            padding: const EdgeInsets.symmetric(horizontal: IcsSpacing.m),
            decoration: BoxDecoration(
              border: Border(
                top: BorderSide(color: isDark ? IcsColors.borderDark : IcsColors.borderLight),
              ),
            ),
            alignment: Alignment.centerLeft,
            child: Text(
              '${records.length} ${records.length == 1 ? 'record' : 'records'}',
              style: TextStyle(fontSize: 11,
                  color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted),
            ),
          ),
          orElse: () => const SizedBox.shrink(),
        ),
      ],
    );
  }
}

// ── Flat list (during search) ─────────────────────────────────────────────────

class _FlatList extends ConsumerWidget {
  const _FlatList({required this.filtered, required this.selectedId, required this.isDark});
  final AsyncValue<List<GovernanceRecord>> filtered;
  final String? selectedId;
  final bool isDark;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return filtered.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (e, _) => Center(child: Text('Error: $e')),
      data: (records) {
        if (records.isEmpty) {
          return Center(child: Text('No records match.',
              style: TextStyle(fontSize: 13,
                  color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted)));
        }
        return ListView.builder(
          itemCount: records.length,
          itemBuilder: (ctx, i) => _RecordTile(
            record: records[i], selected: records[i].id == selectedId, isDark: isDark),
        );
      },
    );
  }
}

// ── Grouped list (default) ────────────────────────────────────────────────────

class _GroupedList extends ConsumerWidget {
  const _GroupedList({required this.byFamily, required this.selectedId, required this.isDark});
  final Map<String, List<GovernanceRecord>> byFamily;
  final String? selectedId;
  final bool isDark;

  static String _familyLabel(String f) {
    final labels = <String, String>{
      'reference':  'Reference Library',
      'mandate':    'Mandate Branch',
      'keys':       'Keys Library',
      'governance': 'Governance',
    };
    if (labels.containsKey(f)) return labels[f]!;
    final words = f.replaceAll('_', ' ').split(' ');
    return words.map((w) => w.isEmpty ? '' : '${w[0].toUpperCase()}${w.substring(1)}').join(' ');
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    if (byFamily.isEmpty) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.menu_book_outlined, size: 40,
                color: (isDark ? IcsColors.borderDark : IcsColors.borderLight)),
            const SizedBox(height: IcsSpacing.m),
            Text('No governance records synced yet.',
                style: TextStyle(fontSize: 13,
                    color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted)),
            const SizedBox(height: IcsSpacing.xs),
            Text('Sync with Ichebo Cloud to receive Handbook content.',
                style: TextStyle(fontSize: 12,
                    color: (isDark ? IcsColors.textMutedDark : IcsColors.textMuted)
                        .withValues(alpha: 0.6))),
          ],
        ),
      );
    }

    final families = byFamily.keys.toList()..sort();
    return ListView.builder(
      itemCount: families.length,
      itemBuilder: (ctx, fi) {
        final family  = families[fi];
        final records = byFamily[family]!;
        return _FamilySection(
          family: _familyLabel(family),
          records: records,
          selectedId: selectedId,
          isDark: isDark,
        );
      },
    );
  }
}

class _FamilySection extends ConsumerWidget {
  const _FamilySection({
    required this.family, required this.records,
    required this.selectedId, required this.isDark,
  });
  final String family;
  final List<GovernanceRecord> records;
  final String? selectedId;
  final bool isDark;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(
              IcsSpacing.m, IcsSpacing.m, IcsSpacing.m, IcsSpacing.xs),
          child: Row(children: [
            Text(family.toUpperCase(),
                style: TextStyle(fontSize: 10, fontWeight: FontWeight.w700,
                    letterSpacing: 0.8,
                    color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted)),
            const SizedBox(width: IcsSpacing.s),
            Text('${records.length}',
                style: TextStyle(fontSize: 10,
                    color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted)),
          ]),
        ),
        ...records.map((r) => _RecordTile(
            record: r, selected: r.id == selectedId, isDark: isDark)),
        Divider(height: 1, color: isDark ? IcsColors.borderDark : IcsColors.borderLight),
      ],
    );
  }
}

// ── Record tile ───────────────────────────────────────────────────────────────

class _RecordTile extends ConsumerStatefulWidget {
  const _RecordTile({required this.record, required this.selected, required this.isDark});
  final GovernanceRecord record;
  final bool selected;
  final bool isDark;

  @override
  ConsumerState<_RecordTile> createState() => _RecordTileState();
}

class _RecordTileState extends ConsumerState<_RecordTile> {
  bool _hovered = false;

  @override
  Widget build(BuildContext context) {
    final bg = widget.selected
        ? IcsColors.accentRed.withValues(alpha: 0.08)
        : (_hovered
            ? (widget.isDark ? Colors.white : Colors.black).withValues(alpha: 0.04)
            : Colors.transparent);

    return MouseRegion(
      onEnter: (_) => setState(() => _hovered = true),
      onExit:  (_) => setState(() => _hovered = false),
      child: GestureDetector(
        onTap: () => ref.read(selectedGovernanceIdProvider.notifier).state =
            widget.selected ? null : widget.record.id,
        child: Container(
          height: 52,
          padding: const EdgeInsets.symmetric(horizontal: IcsSpacing.m),
          decoration: BoxDecoration(
            color: bg,
            border: widget.selected
                ? const Border(left: BorderSide(color: IcsColors.accentRed, width: 3))
                : null,
          ),
          child: Row(children: [
            Expanded(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(widget.record.title,
                      maxLines: 1, overflow: TextOverflow.ellipsis,
                      style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600,
                          color: widget.isDark ? Colors.white : IcsColors.inkBg)),
                  Text(widget.record.typeLabel,
                      style: TextStyle(fontSize: 11,
                          color: widget.isDark
                              ? IcsColors.textMutedDark : IcsColors.textMuted)),
                ],
              ),
            ),
            _StatusDot(status: widget.record.status),
          ]),
        ),
      ),
    );
  }
}

class _StatusDot extends StatelessWidget {
  const _StatusDot({required this.status});
  final String status;

  Color get _color => switch (status) {
        'active'      => IcsColors.success,
        'locked'      => IcsColors.info,
        'superseded'  => const Color(0xFF9E9E9E),
        'draft'       => IcsColors.warning,
        _             => const Color(0xFF9E9E9E),
      };

  @override
  Widget build(BuildContext context) =>
      Container(width: 6, height: 6,
          decoration: BoxDecoration(color: _color, shape: BoxShape.circle));
}

// ── Search bar ────────────────────────────────────────────────────────────────

class _GovernanceSearch extends StatefulWidget {
  const _GovernanceSearch(
      {required this.value, required this.isDark, required this.onChanged});
  final String value;
  final bool isDark;
  final ValueChanged<String> onChanged;

  @override
  State<_GovernanceSearch> createState() => _GovernanceSearchState();
}

class _GovernanceSearchState extends State<_GovernanceSearch> {
  late final TextEditingController _ctrl;

  @override
  void initState() {
    super.initState();
    _ctrl = TextEditingController(text: widget.value);
  }

  @override
  void dispose() { _ctrl.dispose(); super.dispose(); }

  @override
  Widget build(BuildContext context) {
    return TextField(
      controller: _ctrl,
      onChanged: widget.onChanged,
      style: TextStyle(fontSize: 13,
          color: widget.isDark ? Colors.white : IcsColors.inkBg),
      decoration: InputDecoration(
        isDense: true,
        hintText: 'Search governance records…',
        hintStyle: TextStyle(fontSize: 13,
            color: widget.isDark ? IcsColors.textMutedDark : IcsColors.textMuted),
        prefixIcon: Icon(Icons.search, size: 16,
            color: widget.isDark ? IcsColors.textMutedDark : IcsColors.textMuted),
        filled: true,
        fillColor: widget.isDark ? const Color(0xFF1A1A1A) : IcsColors.stone2,
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(6),
            borderSide: BorderSide(
                color: widget.isDark ? IcsColors.borderDark : IcsColors.borderLight)),
        focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(6),
            borderSide: const BorderSide(color: IcsColors.accentRed, width: 1.5)),
        contentPadding:
            const EdgeInsets.symmetric(horizontal: IcsSpacing.m, vertical: 8),
        suffixIcon: _ctrl.text.isNotEmpty
            ? IconButton(icon: const Icon(Icons.close, size: 14),
                onPressed: () { _ctrl.clear(); widget.onChanged(''); },
                color: widget.isDark ? IcsColors.textMutedDark : IcsColors.textMuted)
            : null,
      ),
    );
  }
}

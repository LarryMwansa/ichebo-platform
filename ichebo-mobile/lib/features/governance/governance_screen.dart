import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../../core/theme/tokens.dart';
import 'governance_providers.dart';

class GovernanceScreen extends ConsumerWidget {
  const GovernanceScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final selectedId = ref.watch(selectedGovernanceIdProvider);
    if (selectedId != null) {
      return _GovernanceDetailScreen(recordId: selectedId);
    }
    return const _GovernanceListScreen();
  }
}

// ── List screen ───────────────────────────────────────────────────────────────

class _GovernanceListScreen extends ConsumerWidget {
  const _GovernanceListScreen();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final grouped = ref.watch(governanceByFamilyProvider);
    final query   = ref.watch(governanceSearchProvider);

    return Scaffold(
      backgroundColor: IcsColors.inkBg,
      appBar: AppBar(
        backgroundColor: IcsColors.stone1,
        title: const Text('Governance'),
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(60),
          child: _GovernanceSearch(
            onChanged: (v) =>
                ref.read(governanceSearchProvider.notifier).state = v,
          ),
        ),
      ),
      body: grouped.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error:   (e, st) => Center(
          child: Text('Error: $e',
              style: const TextStyle(color: IcsColors.accentRed)),
        ),
        data: (map) {
          if (map.isEmpty) {
            return const Center(
              child: Text('No governance records',
                  style: TextStyle(color: IcsColors.textMuted)),
            );
          }

          // During search: flat list. No search: grouped by family.
          if (query.isNotEmpty) {
            final flat = map.values.expand((l) => l).toList();
            return RefreshIndicator(
              onRefresh: () async =>
                  ref.invalidate(governanceRecordsProvider),
              child: ListView.separated(
                padding: const EdgeInsets.all(IcsSpacing.m),
                itemCount: flat.length,
                separatorBuilder: (_, i) =>
                    const SizedBox(height: IcsSpacing.s),
                itemBuilder: (_, i) => _RecordTile(
                  record: flat[i],
                  onTap:  () => ref
                      .read(selectedGovernanceIdProvider.notifier)
                      .state = flat[i].id,
                ),
              ),
            );
          }

          final families = map.keys.toList();
          return RefreshIndicator(
            onRefresh: () async =>
                ref.invalidate(governanceRecordsProvider),
            child: ListView.builder(
              padding: const EdgeInsets.all(IcsSpacing.m),
              itemCount: families.length,
              itemBuilder: (_, fi) {
                final family  = families[fi];
                final records = map[family]!;
                return _FamilySection(
                  family:  family,
                  records: records,
                  onSelect: (id) => ref
                      .read(selectedGovernanceIdProvider.notifier)
                      .state = id,
                );
              },
            ),
          );
        },
      ),
    );
  }
}

// ── Family section ────────────────────────────────────────────────────────────

class _FamilySection extends StatelessWidget {
  const _FamilySection({
    required this.family,
    required this.records,
    required this.onSelect,
  });
  final String                   family;
  final List<GovernanceRecord>   records;
  final ValueChanged<String>     onSelect;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.only(
              top: IcsSpacing.m, bottom: IcsSpacing.s),
          child: Text(
            _fmtFamily(family),
            style: const TextStyle(
              color: IcsColors.textMuted,
              fontSize: 11,
              letterSpacing: 1.2,
              fontWeight: FontWeight.w600,
            ),
          ),
        ),
        ...records.map((r) => Padding(
          padding: const EdgeInsets.only(bottom: IcsSpacing.s),
          child: _RecordTile(
            record: r,
            onTap:  () => onSelect(r.id),
          ),
        )),
      ],
    );
  }

  static String _fmtFamily(String f) =>
      f.replaceAll('_', ' ').toUpperCase();
}

// ── Record tile ───────────────────────────────────────────────────────────────

class _RecordTile extends StatelessWidget {
  const _RecordTile({required this.record, required this.onTap});
  final GovernanceRecord record;
  final VoidCallback     onTap;

  @override
  Widget build(BuildContext context) {
    return Card(
      color: IcsColors.stone1,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8),
        side: const BorderSide(color: IcsColors.borderDark),
      ),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(8),
        child: Padding(
          padding: const EdgeInsets.all(IcsSpacing.m),
          child: Row(
            children: [
              _StatusDot(status: record.status),
              const SizedBox(width: IcsSpacing.s),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      record.title,
                      style: const TextStyle(
                          color: Colors.white,
                          fontWeight: FontWeight.w500),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      record.recordType.replaceAll('_', ' '),
                      style: const TextStyle(
                          color: IcsColors.textMuted, fontSize: 12),
                    ),
                  ],
                ),
              ),
              const Icon(Icons.chevron_right,
                  color: IcsColors.textMuted, size: 18),
            ],
          ),
        ),
      ),
    );
  }
}

// ── Search bar ────────────────────────────────────────────────────────────────

class _GovernanceSearch extends StatefulWidget {
  const _GovernanceSearch({required this.onChanged});
  final ValueChanged<String> onChanged;

  @override
  State<_GovernanceSearch> createState() => _GovernanceSearchState();
}

class _GovernanceSearchState extends State<_GovernanceSearch> {
  final _ctrl = TextEditingController();

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(
          IcsSpacing.m, 0, IcsSpacing.m, IcsSpacing.s),
      child: TextField(
        controller: _ctrl,
        onChanged: widget.onChanged,
        style: const TextStyle(color: Colors.white),
        decoration: InputDecoration(
          hintText: 'Search records…',
          hintStyle: const TextStyle(color: IcsColors.textMuted),
          prefixIcon:
              const Icon(Icons.search, color: IcsColors.textMuted, size: 18),
          suffixIcon: _ctrl.text.isNotEmpty
              ? IconButton(
                  icon: const Icon(Icons.clear,
                      color: IcsColors.textMuted, size: 18),
                  onPressed: () {
                    _ctrl.clear();
                    widget.onChanged('');
                  },
                )
              : null,
          filled: true,
          fillColor: IcsColors.stone2,
          contentPadding:
              const EdgeInsets.symmetric(vertical: IcsSpacing.s),
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(8),
            borderSide: BorderSide.none,
          ),
        ),
      ),
    );
  }
}

// ── Status dot ────────────────────────────────────────────────────────────────

class _StatusDot extends StatelessWidget {
  const _StatusDot({required this.status});
  final String status;

  @override
  Widget build(BuildContext context) {
    final color = switch (status) {
      'active'   => IcsColors.accentGreen,
      'draft'    => IcsColors.accentAmber,
      'archived' => IcsColors.textMuted,
      'repealed' => IcsColors.accentRed,
      _          => IcsColors.textMuted,
    };
    return Container(
      width: 8,
      height: 8,
      decoration: BoxDecoration(shape: BoxShape.circle, color: color),
    );
  }
}

// ── Detail screen ─────────────────────────────────────────────────────────────

class _GovernanceDetailScreen extends ConsumerWidget {
  const _GovernanceDetailScreen({required this.recordId});
  final String recordId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(governanceByIdProvider(recordId));

    return async.when(
      loading: () => const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      ),
      error: (e, st) => Scaffold(
        appBar: AppBar(leading: _BackButton(ref: ref)),
        body: Center(
          child: Text('Error: $e',
              style: const TextStyle(color: IcsColors.accentRed)),
        ),
      ),
      data: (record) {
        if (record == null) {
          return Scaffold(
            appBar: AppBar(leading: _BackButton(ref: ref)),
            body: const Center(child: Text('Record not found')),
          );
        }
        return _RecordDetail(record: record, ref: ref);
      },
    );
  }
}

class _BackButton extends StatelessWidget {
  const _BackButton({required this.ref});
  final WidgetRef ref;

  @override
  Widget build(BuildContext context) {
    return IconButton(
      icon: const Icon(Icons.arrow_back),
      onPressed: () =>
          ref.read(selectedGovernanceIdProvider.notifier).state = null,
    );
  }
}

class _RecordDetail extends StatelessWidget {
  const _RecordDetail({required this.record, required this.ref});
  final GovernanceRecord record;
  final WidgetRef        ref;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: IcsColors.inkBg,
      appBar: AppBar(
        backgroundColor: IcsColors.stone1,
        leading: _BackButton(ref: ref),
        title: Text(
          _fmtFamily(record.recordFamily),
          style: const TextStyle(fontSize: 14, color: IcsColors.textMuted),
        ),
        actions: [
          _StatusBadge(status: record.status),
          const SizedBox(width: IcsSpacing.m),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(IcsSpacing.m),
        children: [
          _TitleCard(record: record),
          const SizedBox(height: IcsSpacing.m),
          _MetaCard(record: record),
          if (record.summary != null && record.summary!.isNotEmpty) ...[
            const SizedBox(height: IcsSpacing.m),
            _SummaryCard(summary: record.summary!),
          ],
          const SizedBox(height: IcsSpacing.xl),
        ],
      ),
    );
  }

  static String _fmtFamily(String f) =>
      f.replaceAll('_', ' ').toUpperCase();
}

// ── Title card ────────────────────────────────────────────────────────────────

class _TitleCard extends StatelessWidget {
  const _TitleCard({required this.record});
  final GovernanceRecord record;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(IcsSpacing.m),
      decoration: BoxDecoration(
        color: IcsColors.stone1,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: IcsColors.borderDark),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            record.recordType.replaceAll('_', ' ').toUpperCase(),
            style: const TextStyle(
                color: IcsColors.textMuted,
                fontSize: 11,
                letterSpacing: 1.2),
          ),
          const SizedBox(height: IcsSpacing.s),
          Text(
            record.title,
            style: const TextStyle(
                color: Colors.white,
                fontSize: 20,
                fontWeight: FontWeight.w600),
          ),
        ],
      ),
    );
  }
}

// ── Meta card ─────────────────────────────────────────────────────────────────

class _MetaCard extends StatelessWidget {
  const _MetaCard({required this.record});
  final GovernanceRecord record;

  @override
  Widget build(BuildContext context) {
    final rows = <(String, String)>[
      ('Family', record.recordFamily.replaceAll('_', ' ')),
      ('Type',   record.recordType.replaceAll('_', ' ')),
      ('Status', record.status),
    ];
    if (record.effectiveAt != null && record.effectiveAt!.isNotEmpty) {
      rows.add(('Effective', _fmtDate(record.effectiveAt!)));
    }
    rows.add(('Updated', _fmtDate(record.updatedAt)));

    return Container(
      decoration: BoxDecoration(
        color: IcsColors.stone1,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: IcsColors.borderDark),
      ),
      child: Column(
        children: rows.indexed.map((entry) {
          final (i, row) = entry;
          final (label, value) = row;
          return Column(
            children: [
              if (i > 0)
                const Divider(height: 1, color: IcsColors.borderDark),
              Padding(
                padding: const EdgeInsets.symmetric(
                    horizontal: IcsSpacing.m, vertical: IcsSpacing.s + 2),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(label,
                        style: const TextStyle(
                            color: IcsColors.textMuted, fontSize: 13)),
                    Text(value,
                        style: const TextStyle(
                            color: Colors.white, fontSize: 13)),
                  ],
                ),
              ),
            ],
          );
        }).toList(),
      ),
    );
  }
}

// ── Summary card ──────────────────────────────────────────────────────────────

class _SummaryCard extends StatelessWidget {
  const _SummaryCard({required this.summary});
  final String summary;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(IcsSpacing.m),
      decoration: BoxDecoration(
        color: IcsColors.stone1,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: IcsColors.borderDark),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'SUMMARY',
            style: TextStyle(
                color: IcsColors.textMuted,
                fontSize: 11,
                letterSpacing: 1.2),
          ),
          const SizedBox(height: IcsSpacing.s),
          Text(
            summary,
            style: const TextStyle(
                color: Colors.white, fontSize: 14, height: 1.5),
          ),
        ],
      ),
    );
  }
}

// ── Status badge ──────────────────────────────────────────────────────────────

class _StatusBadge extends StatelessWidget {
  const _StatusBadge({required this.status});
  final String status;

  @override
  Widget build(BuildContext context) {
    final color = switch (status) {
      'active'   => IcsColors.accentGreen,
      'draft'    => IcsColors.accentAmber,
      'archived' => IcsColors.textMuted,
      'repealed' => IcsColors.accentRed,
      _          => IcsColors.textMuted,
    };
    return Container(
      padding:
          const EdgeInsets.symmetric(horizontal: IcsSpacing.s, vertical: 3),
      decoration: BoxDecoration(
        color: color.withAlpha(26),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: color.withAlpha(77)),
      ),
      child: Text(
        status.toUpperCase(),
        style: TextStyle(color: color, fontSize: 10, letterSpacing: 1),
      ),
    );
  }
}

// ── Helpers ───────────────────────────────────────────────────────────────────

String _fmtDate(String iso) {
  try {
    final dt = DateTime.parse(iso).toLocal();
    return DateFormat('MMM d, yyyy').format(dt);
  } catch (_) {
    return iso;
  }
}


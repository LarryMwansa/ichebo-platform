import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/api/providers.dart';
import '../../shared/tokens/tokens.dart';
import '../../shared/widgets/badges.dart';
import '../../shared/widgets/empty_state.dart';
import '../../shared/widgets/ichebo_app_bar.dart';
import '../../shared/widgets/ichebo_card.dart';

// Governance tabs: Reference Library (class/principle/concept/divine_pattern)
// and Mandate branch (mandate/statement/protocol/procedure).
// Both map to governance record_class in the Records API.

final _govTabProvider = StateProvider.autoDispose<int>((ref) => 0);

const _referenceTypes = ['class', 'principle', 'concept', 'divine_pattern'];
const _mandateTypes = ['mandate', 'statement', 'protocol', 'procedure'];

class GovernanceScreen extends ConsumerWidget {
  const GovernanceScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final tab = ref.watch(_govTabProvider);

    return Scaffold(
      appBar: const IcheboAppBar(title: 'Governance', watermarkText: 'GOVERNANCE'),
      body: Column(
        children: [
          _GovTabRow(
            currentTab: tab,
            onTab: (i) => ref.read(_govTabProvider.notifier).state = i,
          ),
          Expanded(
            child: _RecordList(
              types: tab == 0 ? _referenceTypes : _mandateTypes,
              label: tab == 0 ? 'Reference Library' : 'Mandate',
            ),
          ),
        ],
      ),
    );
  }
}

class _GovTabRow extends StatelessWidget {
  const _GovTabRow({required this.currentTab, required this.onTab});
  final int currentTab;
  final ValueChanged<int> onTab;

  @override
  Widget build(BuildContext context) {
    return Container(
      color: Theme.of(context).colorScheme.surface,
      padding: const EdgeInsets.symmetric(
        horizontal: IcheboSpacing.s,
        vertical: IcheboSpacing.xs3,
      ),
      child: Row(
        children: [
          _GovTab(label: 'Reference Library', active: currentTab == 0, onTap: () => onTab(0)),
          const SizedBox(width: IcheboSpacing.xs),
          _GovTab(label: 'Mandate', active: currentTab == 1, onTap: () => onTab(1)),
        ],
      ),
    );
  }
}

class _GovTab extends StatelessWidget {
  const _GovTab({required this.label, required this.active, required this.onTap});
  final String label;
  final bool active;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(
          horizontal: IcheboSpacing.s,
          vertical: IcheboSpacing.xs3,
        ),
        decoration: BoxDecoration(
          border: active
              ? const Border(
                  bottom: BorderSide(color: IcheboColors.primary, width: 2))
              : null,
        ),
        child: Text(
          label,
          style: IcheboTextStyles.labelLarge.copyWith(
            color: active ? IcheboColors.primary : IcheboColors.muted,
          ),
        ),
      ),
    );
  }
}

class _RecordList extends ConsumerWidget {
  const _RecordList({required this.types, required this.label});
  final List<String> types;
  final String label;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final params = {'record_class': 'governance', 'record_family': 'governance'};
    final recordsAsync = ref.watch(recordsProvider(params));

    return recordsAsync.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (e, _) => EmptyState(message: e.toString()),
      data: (all) {
        final filtered = all.where((r) => types.contains(r.recordType)).toList();
        return filtered.isEmpty
            ? EmptyState(
                icon: Icons.account_balance_outlined,
                message: 'No $label records yet.',
              )
            : ListView.builder(
                padding: const EdgeInsets.all(IcheboSpacing.s),
                itemCount: filtered.length,
                itemBuilder: (context, i) => Padding(
                  padding: const EdgeInsets.only(bottom: IcheboSpacing.xs3),
                  child: _RecordCard(record: filtered[i]),
                ),
              );
      },
    );
  }
}

class _RecordCard extends StatelessWidget {
  const _RecordCard({required this.record});
  final GovernanceRecord record;

  @override
  Widget build(BuildContext context) {
    return IcheboCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  record.title,
                  style: Theme.of(context).textTheme.titleMedium,
                ),
              ),
              LabelTag(label: record.recordType.replaceAll('_', ' ')),
            ],
          ),
          if (record.summary != null && record.summary!.isNotEmpty) ...[
            const SizedBox(height: IcheboSpacing.xs3),
            Text(
              record.summary!,
              style: Theme.of(context).textTheme.bodySmall,
              maxLines: 3,
              overflow: TextOverflow.ellipsis,
            ),
          ],
          const SizedBox(height: IcheboSpacing.xs3),
          StatusBadge(
            label: record.status,
            variant: record.status == 'active'
                ? StatusVariant.active
                : record.status == 'locked'
                    ? StatusVariant.muted
                    : StatusVariant.warning,
          ),
        ],
      ),
    );
  }
}

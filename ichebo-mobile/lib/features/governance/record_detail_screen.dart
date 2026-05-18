import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import '../../core/api/providers.dart';
import '../../shared/tokens/tokens.dart';
import '../../shared/widgets/badges.dart';

class RecordDetailScreen extends StatelessWidget {
  const RecordDetailScreen({super.key, required this.record});
  final GovernanceRecord record;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(
          record.recordType.replaceAll('_', ' ').toUpperCase(),
          style: IcheboTextStyles.labelCaps.copyWith(fontSize: 11),
        ),
        centerTitle: false,
      ),
      body: ListView(
        padding: const EdgeInsets.all(IcheboSpacing.s),
        children: [
          // ── Title ────────────────────────────────────────────────────
          Text(record.title, style: IcheboTextStyles.headlineLarge),
          const SizedBox(height: IcheboSpacing.xs),

          // ── Meta row ─────────────────────────────────────────────────
          Row(
            children: [
              StatusBadge(
                label: record.status,
                variant: record.status == 'active'
                    ? StatusVariant.active
                    : record.status == 'locked'
                        ? StatusVariant.muted
                        : StatusVariant.warning,
              ),
              const SizedBox(width: IcheboSpacing.xs3),
              LabelTag(label: record.recordType.replaceAll('_', ' ')),
              if (record.createdAt != null) ...[
                const Spacer(),
                Text(
                  _formatDate(record.createdAt!),
                  style: IcheboTextStyles.bodySmall
                      .copyWith(color: IcheboColors.mutedLight),
                ),
              ],
            ],
          ),
          const SizedBox(height: IcheboSpacing.m),

          // ── Body ─────────────────────────────────────────────────────
          if (record.summary != null && record.summary!.isNotEmpty)
            MarkdownBody(
              data: record.summary!,
              styleSheet: MarkdownStyleSheet.fromTheme(Theme.of(context))
                  .copyWith(
                p: Theme.of(context)
                    .textTheme
                    .bodyLarge
                    ?.copyWith(height: 1.7),
                h2: IcheboTextStyles.titleLarge,
                h3: IcheboTextStyles.titleMedium,
                blockquoteDecoration: BoxDecoration(
                  border: const Border(
                    left: BorderSide(
                        color: IcheboColors.primary, width: 3),
                  ),
                  color: IcheboColors.primaryLight,
                  borderRadius: IcheboRadius.s,
                ),
              ),
            )
          else
            Text(
              'No content available.',
              style: Theme.of(context)
                  .textTheme
                  .bodyMedium
                  ?.copyWith(color: IcheboColors.muted),
            ),

          const SizedBox(height: IcheboSpacing.xl),
        ],
      ),
    );
  }

  String _formatDate(String iso) {
    try {
      final dt = DateTime.parse(iso).toLocal();
      const months = [
        '', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
        'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
      ];
      return '${dt.day} ${months[dt.month]} ${dt.year}';
    } catch (_) {
      return iso;
    }
  }
}

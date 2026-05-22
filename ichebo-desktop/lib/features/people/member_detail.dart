import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/theme/tokens.dart';
import '../../shared/level_badge.dart';
import '../../shared/member_list_tile.dart';
import 'member_form.dart';
import 'people_providers.dart';

class MemberDetail extends ConsumerWidget {
  const MemberDetail({super.key, required this.memberId});
  final String memberId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final memberAsync = ref.watch(memberByIdProvider(memberId));
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return memberAsync.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (e, _) => Center(child: Text('Error: $e')),
      data: (member) {
        if (member == null) {
          return Center(
            child: Text('Member not found.',
                style: TextStyle(color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted)),
          );
        }

        return SingleChildScrollView(
          padding: const EdgeInsets.all(IcsSpacing.l),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              _MemberHeader(member: member, isDark: isDark),
              const SizedBox(height: IcsSpacing.l),
              _FormationCard(member: member, isDark: isDark),
              const SizedBox(height: IcsSpacing.m),
              _PastoralCard(member: member, isDark: isDark),
              const SizedBox(height: IcsSpacing.l),
              _ActionBar(member: member, isDark: isDark),
            ],
          ),
        );
      },
    );
  }
}

// ── Header ────────────────────────────────────────────────────────────────────

class _MemberHeader extends StatelessWidget {
  const _MemberHeader({required this.member, required this.isDark});
  final MemberModel member;
  final bool isDark;

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        CircleAvatar(
          radius: 28,
          backgroundColor: IcsColors.accentRed.withValues(alpha: 0.15),
          child: Text(
            member.displayName.isNotEmpty ? member.displayName[0].toUpperCase() : '?',
            style: const TextStyle(
              fontFamily: 'Playfair Display',
              fontSize: 22,
              fontWeight: FontWeight.w700,
              color: IcsColors.accentRed,
            ),
          ),
        ),
        const SizedBox(width: IcsSpacing.m),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                member.displayName,
                style: TextStyle(
                  fontFamily: 'Playfair Display',
                  fontSize: 18,
                  fontWeight: FontWeight.w700,
                  color: isDark ? Colors.white : IcsColors.inkBg,
                ),
              ),
              const SizedBox(height: 2),
              Text(
                member.email,
                style: TextStyle(fontSize: 12, color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted),
              ),
              if (member.phone.isNotEmpty) ...[
                const SizedBox(height: 2),
                Text(
                  member.phone,
                  style: TextStyle(fontSize: 12, color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted),
                ),
              ],
            ],
          ),
        ),
        _StatusDot(isActive: member.isActive),
      ],
    );
  }
}

class _StatusDot extends StatelessWidget {
  const _StatusDot({required this.isActive});
  final bool isActive;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 7,
          height: 7,
          decoration: BoxDecoration(
            color: isActive ? IcsColors.success : IcsColors.textMuted,
            shape: BoxShape.circle,
          ),
        ),
        const SizedBox(width: 4),
        Text(
          isActive ? 'Active' : 'Inactive',
          style: TextStyle(fontSize: 11, color: isActive ? IcsColors.success : IcsColors.textMuted),
        ),
      ],
    );
  }
}

// ── Formation card ────────────────────────────────────────────────────────────

class _FormationCard extends StatelessWidget {
  const _FormationCard({required this.member, required this.isDark});
  final MemberModel member;
  final bool isDark;

  static const _levelNames = [
    'Seeker', 'Foundational Disciple', 'Active Contributor',
    'Functional Minister', 'Leader', 'Apostolic Steward',
  ];

  @override
  Widget build(BuildContext context) {
    return _DetailCard(
      title: 'Formation',
      isDark: isDark,
      child: Column(
        children: [
          _DetailRow(
            label: 'Competence level',
            isDark: isDark,
            value: Row(
              children: [
                LevelBadge(level: member.competenceLevel, large: true),
                const SizedBox(width: IcsSpacing.s),
                Text(
                  _levelNames[member.competenceLevel.clamp(0, 5)],
                  style: TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                    color: isDark ? Colors.white : IcsColors.inkBg,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: IcsSpacing.s),
          _DetailRow(
            label: 'Service order',
            isDark: isDark,
            value: Text(
              member.serviceOrder ?? '—',
              style: TextStyle(fontSize: 13, color: isDark ? Colors.white : IcsColors.inkBg),
            ),
          ),
        ],
      ),
    );
  }
}

// ── Pastoral card ─────────────────────────────────────────────────────────────

class _PastoralCard extends ConsumerWidget {
  const _PastoralCard({required this.member, required this.isDark});
  final MemberModel member;
  final bool isDark;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final shepherdAsync = member.shepherdId != null
        ? ref.watch(memberByIdProvider(member.shepherdId!))
        : const AsyncData<MemberModel?>(null);

    final allAsync = ref.watch(membersProvider);
    final flock = allAsync.maybeWhen(
      data: (list) => list.where((m) => m.shepherdId == member.id).toList(),
      orElse: () => <MemberModel>[],
    );

    return _DetailCard(
      title: 'Pastoral',
      isDark: isDark,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Shepherd',
            style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600,
                color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted),
          ),
          const SizedBox(height: IcsSpacing.xs),
          shepherdAsync.when(
            loading: () => const SizedBox(height: 44, child: Center(child: CircularProgressIndicator(strokeWidth: 2))),
            error: (_, st) => Text('—', style: TextStyle(fontSize: 13, color: isDark ? Colors.white : IcsColors.inkBg)),
            data: (shepherd) => shepherd != null
                ? MemberListTile(
                    displayName: shepherd.displayName,
                    email: shepherd.email,
                    competenceLevel: shepherd.competenceLevel,
                    serviceOrder: shepherd.serviceOrder,
                    compact: true,
                  )
                : Text(
                    'No shepherd assigned',
                    style: TextStyle(fontSize: 13, color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted),
                  ),
          ),
          const SizedBox(height: IcsSpacing.m),
          Row(
            children: [
              Text(
                'Flock',
                style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600,
                    color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted),
              ),
              const SizedBox(width: IcsSpacing.xs),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1),
                decoration: BoxDecoration(
                  color: IcsColors.accentRed.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Text(
                  '${flock.length}',
                  style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w700, color: IcsColors.accentRed),
                ),
              ),
            ],
          ),
          if (flock.isNotEmpty) ...[
            const SizedBox(height: IcsSpacing.xs),
            ...flock.take(5).map((m) => MemberListTile(
                  displayName: m.displayName,
                  email: m.email,
                  competenceLevel: m.competenceLevel,
                  serviceOrder: m.serviceOrder,
                  compact: true,
                )),
            if (flock.length > 5)
              Padding(
                padding: const EdgeInsets.only(top: IcsSpacing.xs, left: IcsSpacing.m),
                child: Text(
                  '+${flock.length - 5} more',
                  style: TextStyle(fontSize: 11, color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted),
                ),
              ),
          ],
        ],
      ),
    );
  }
}

// ── Action bar ────────────────────────────────────────────────────────────────

class _ActionBar extends ConsumerWidget {
  const _ActionBar({required this.member, required this.isDark});
  final MemberModel member;
  final bool isDark;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Row(
      children: [
        OutlinedButton.icon(
          onPressed: () async {
            final result = await showDialog<bool>(
              context: context,
              builder: (_) => MemberForm(mode: MemberFormMode.edit, member: member),
            );
            if (result == true) ref.invalidate(memberByIdProvider(member.id));
          },
          icon: const Icon(Icons.edit_outlined, size: 14),
          label: const Text('Edit member'),
          style: OutlinedButton.styleFrom(
            foregroundColor: isDark ? Colors.white : IcsColors.inkBg,
            side: BorderSide(color: isDark ? IcsColors.borderDark : IcsColors.borderLight),
          ),
        ),
        const SizedBox(width: IcsSpacing.s),
        OutlinedButton.icon(
          onPressed: null, // D.5 — Activity section stub
          icon: const Icon(Icons.event_note_outlined, size: 14),
          label: const Text('View activities'),
          style: OutlinedButton.styleFrom(
            foregroundColor: isDark ? IcsColors.textMutedDark : IcsColors.textMuted,
            side: BorderSide(color: isDark ? IcsColors.borderDark : IcsColors.borderLight),
          ),
        ),
      ],
    );
  }
}

// ── Shared card chrome ────────────────────────────────────────────────────────

class _DetailCard extends StatelessWidget {
  const _DetailCard({required this.title, required this.isDark, required this.child});
  final String title;
  final bool isDark;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: isDark ? IcsColors.ink2 : Colors.white,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: isDark ? IcsColors.borderDark : IcsColors.borderLight),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(IcsSpacing.m, IcsSpacing.m, IcsSpacing.m, IcsSpacing.s),
            child: Text(
              title.toUpperCase(),
              style: TextStyle(
                fontSize: 10,
                fontWeight: FontWeight.w700,
                letterSpacing: 0.08 * 10,
                color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted,
              ),
            ),
          ),
          Divider(height: 1, color: isDark ? IcsColors.borderDark : IcsColors.borderLight),
          Padding(
            padding: const EdgeInsets.all(IcsSpacing.m),
            child: child,
          ),
        ],
      ),
    );
  }
}

class _DetailRow extends StatelessWidget {
  const _DetailRow({required this.label, required this.value, required this.isDark});
  final String label;
  final Widget value;
  final bool isDark;

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        SizedBox(
          width: 130,
          child: Text(
            label,
            style: TextStyle(fontSize: 12, color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted),
          ),
        ),
        Expanded(child: value),
      ],
    );
  }
}

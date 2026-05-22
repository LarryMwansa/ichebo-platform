import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/theme/tokens.dart';
import 'community_providers.dart';

class CommunityScreen extends ConsumerWidget {
  const CommunityScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final selectedId = ref.watch(selectedMemberIdProvider);
    final isDark     = Theme.of(context).brightness == Brightness.dark;

    // If a member is selected show detail with back nav
    if (selectedId != null) {
      return _MemberDetailScreen(memberId: selectedId, isDark: isDark);
    }
    return _MemberListScreen(isDark: isDark);
  }
}

// ── List screen ───────────────────────────────────────────────────────────────

class _MemberListScreen extends ConsumerWidget {
  const _MemberListScreen({required this.isDark});
  final bool isDark;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final filtered = ref.watch(filteredMembersProvider);
    final search   = ref.watch(memberSearchProvider);
    final level    = ref.watch(memberFilterLevelProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Community')),
      body: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Search bar
          Padding(
            padding: const EdgeInsets.fromLTRB(
                IcsSpacing.m, IcsSpacing.m, IcsSpacing.m, IcsSpacing.xs),
            child: _SearchBar(
              value:     search,
              isDark:    isDark,
              onChanged: (v) =>
                  ref.read(memberSearchProvider.notifier).state = v,
            ),
          ),
          // Level filter chips
          SizedBox(
            height: 36,
            child: ListView(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(
                  horizontal: IcsSpacing.m, vertical: 2),
              children: [
                _LevelChip(
                  label: 'All',
                  selected: level == null,
                  isDark: isDark,
                  onTap: () =>
                      ref.read(memberFilterLevelProvider.notifier).state =
                          null,
                ),
                ...List.generate(
                  6,
                  (i) => _LevelChip(
                    label: 'L$i',
                    selected: level == i,
                    isDark: isDark,
                    onTap: () => ref
                        .read(memberFilterLevelProvider.notifier)
                        .state = level == i ? null : i,
                  ),
                ),
              ],
            ),
          ),
          Divider(
              height: 1,
              color:
                  isDark ? IcsColors.borderDark : IcsColors.borderLight),
          // List
          Expanded(
            child: RefreshIndicator(
              color: IcsColors.accentRed,
              onRefresh: () async => ref.invalidate(membersProvider),
              child: filtered.when(
                loading: () =>
                    const Center(child: CircularProgressIndicator()),
                error: (e, _) =>
                    Center(child: Text('Error: $e')),
                data: (members) {
                  if (members.isEmpty) {
                    return Center(
                      child: Text(
                        search.isNotEmpty
                            ? 'No members match "$search".'
                            : 'No members synced yet.',
                        style: TextStyle(
                          fontSize: 14,
                          color: isDark
                              ? IcsColors.textMutedDark
                              : IcsColors.textMuted,
                        ),
                      ),
                    );
                  }
                  return ListView.separated(
                    itemCount: members.length,
                    separatorBuilder: (_, i) => Divider(
                        height: 1,
                        indent: 72,
                        color: isDark
                            ? IcsColors.borderDark
                            : IcsColors.borderLight),
                    itemBuilder: (context, i) {
                      final m = members[i];
                      return _MemberTile(
                        member: m,
                        isDark: isDark,
                        onTap: () => ref
                            .read(selectedMemberIdProvider.notifier)
                            .state = m.id,
                      );
                    },
                  );
                },
              ),
            ),
          ),
          // Footer count
          filtered.maybeWhen(
            data: (members) => Container(
              height: 28,
              padding: const EdgeInsets.symmetric(
                  horizontal: IcsSpacing.m),
              decoration: BoxDecoration(
                border: Border(
                  top: BorderSide(
                      color: isDark
                          ? IcsColors.borderDark
                          : IcsColors.borderLight),
                ),
              ),
              alignment: Alignment.centerLeft,
              child: Text(
                '${members.length} '
                '${members.length == 1 ? 'member' : 'members'}',
                style: TextStyle(
                  fontSize: 11,
                  color: isDark
                      ? IcsColors.textMutedDark
                      : IcsColors.textMuted,
                ),
              ),
            ),
            orElse: () => const SizedBox.shrink(),
          ),
        ],
      ),
    );
  }
}

// ── Member tile ───────────────────────────────────────────────────────────────

class _MemberTile extends StatelessWidget {
  const _MemberTile({
    required this.member,
    required this.isDark,
    required this.onTap,
  });
  final MemberModel  member;
  final bool         isDark;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return ListTile(
      onTap: onTap,
      leading: CircleAvatar(
        radius: 20,
        backgroundColor: IcsColors.accentRed.withValues(alpha: 0.12),
        child: Text(
          member.initials,
          style: const TextStyle(
            fontSize: 13,
            fontWeight: FontWeight.w700,
            color: IcsColors.accentRed,
          ),
        ),
      ),
      title: Text(
        member.displayName,
        style: TextStyle(
          fontSize: 14,
          fontWeight: FontWeight.w600,
          color: isDark ? Colors.white : IcsColors.inkBg,
        ),
      ),
      subtitle: Text(
        member.email,
        style: TextStyle(
          fontSize: 12,
          color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted,
        ),
      ),
      trailing: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          _LevelBadge(level: member.competenceLevel),
          const SizedBox(width: IcsSpacing.xs),
          Icon(Icons.chevron_right,
              size: 16,
              color: isDark
                  ? IcsColors.textMutedDark
                  : IcsColors.textMuted),
        ],
      ),
    );
  }
}

// ── Detail screen ─────────────────────────────────────────────────────────────

class _MemberDetailScreen extends ConsumerWidget {
  const _MemberDetailScreen(
      {required this.memberId, required this.isDark});
  final String memberId;
  final bool   isDark;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final memberAsync = ref.watch(memberByIdProvider(memberId));

    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () =>
              ref.read(selectedMemberIdProvider.notifier).state = null,
        ),
        title: memberAsync.maybeWhen(
          data: (m) => Text(m?.displayName ?? 'Member'),
          orElse: () => const Text('Member'),
        ),
      ),
      body: memberAsync.when(
        loading: () =>
            const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('Error: $e')),
        data: (member) {
          if (member == null) {
            return Center(
              child: Text('Member not found.',
                  style: TextStyle(
                      color: isDark
                          ? IcsColors.textMutedDark
                          : IcsColors.textMuted)),
            );
          }
          return SingleChildScrollView(
            padding: const EdgeInsets.all(IcsSpacing.m),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                _ProfileHeader(member: member, isDark: isDark),
                const SizedBox(height: IcsSpacing.m),
                _FormationCard(member: member, isDark: isDark),
                const SizedBox(height: IcsSpacing.m),
                _ContactCard(member: member, isDark: isDark),
                const SizedBox(height: IcsSpacing.m),
                _ShepherdCard(member: member, isDark: isDark),
                const SizedBox(height: IcsSpacing.l),
              ],
            ),
          );
        },
      ),
    );
  }
}

// ── Profile header ────────────────────────────────────────────────────────────

class _ProfileHeader extends StatelessWidget {
  const _ProfileHeader({required this.member, required this.isDark});
  final MemberModel member;
  final bool        isDark;

  @override
  Widget build(BuildContext context) {
    return Row(crossAxisAlignment: CrossAxisAlignment.center, children: [
      CircleAvatar(
        radius: 32,
        backgroundColor: IcsColors.accentRed.withValues(alpha: 0.12),
        child: Text(member.initials,
            style: const TextStyle(
              fontFamily: 'PlayfairDisplay',
              fontSize: 24,
              fontWeight: FontWeight.w700,
              color: IcsColors.accentRed,
            )),
      ),
      const SizedBox(width: IcsSpacing.m),
      Expanded(
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(member.displayName,
              style: TextStyle(
                fontFamily: 'PlayfairDisplay',
                fontSize: 20,
                fontWeight: FontWeight.w700,
                color: isDark ? Colors.white : IcsColors.inkBg,
              )),
          const SizedBox(height: 2),
          Row(children: [
            Container(
              width: 7, height: 7,
              decoration: BoxDecoration(
                color: member.isActive
                    ? IcsColors.accentGreen
                    : IcsColors.textMuted,
                shape: BoxShape.circle,
              ),
            ),
            const SizedBox(width: 4),
            Text(member.isActive ? 'Active' : 'Inactive',
                style: TextStyle(
                    fontSize: 12,
                    color: member.isActive
                        ? IcsColors.accentGreen
                        : IcsColors.textMuted)),
          ]),
        ]),
      ),
    ]);
  }
}

// ── Formation card ────────────────────────────────────────────────────────────

class _FormationCard extends StatelessWidget {
  const _FormationCard({required this.member, required this.isDark});
  final MemberModel member;
  final bool        isDark;

  @override
  Widget build(BuildContext context) {
    return _DetailCard(
      title: 'Formation',
      isDark: isDark,
      child: Column(children: [
        _DetailRow(
          label: 'Level',
          isDark: isDark,
          trailing: Row(mainAxisSize: MainAxisSize.min, children: [
            _LevelBadge(level: member.competenceLevel),
            const SizedBox(width: IcsSpacing.s),
            Text(member.levelName,
                style: TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                    color: isDark ? Colors.white : IcsColors.inkBg)),
          ]),
        ),
        if (member.serviceOrder != null) ...[
          Divider(
              height: 1,
              color: isDark
                  ? IcsColors.borderDark
                  : IcsColors.borderLight),
          _DetailRow(
            label: 'Service order',
            isDark: isDark,
            trailing: Text(member.serviceOrder!,
                style: TextStyle(
                    fontSize: 13,
                    color: isDark ? Colors.white : IcsColors.inkBg)),
          ),
        ],
      ]),
    );
  }
}

// ── Contact card ──────────────────────────────────────────────────────────────

class _ContactCard extends StatelessWidget {
  const _ContactCard({required this.member, required this.isDark});
  final MemberModel member;
  final bool        isDark;

  @override
  Widget build(BuildContext context) {
    return _DetailCard(
      title: 'Contact',
      isDark: isDark,
      child: Column(children: [
        _DetailRow(
          label: 'Email',
          isDark: isDark,
          trailing: Text(member.email.isNotEmpty ? member.email : '—',
              style: TextStyle(
                  fontSize: 13,
                  color: isDark ? Colors.white : IcsColors.inkBg)),
        ),
        if (member.phone.isNotEmpty) ...[
          Divider(
              height: 1,
              color: isDark
                  ? IcsColors.borderDark
                  : IcsColors.borderLight),
          _DetailRow(
            label: 'Phone',
            isDark: isDark,
            trailing: Text(member.phone,
                style: TextStyle(
                    fontSize: 13,
                    color: isDark ? Colors.white : IcsColors.inkBg)),
          ),
        ],
      ]),
    );
  }
}

// ── Shepherd card ─────────────────────────────────────────────────────────────

class _ShepherdCard extends ConsumerWidget {
  const _ShepherdCard({required this.member, required this.isDark});
  final MemberModel member;
  final bool        isDark;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    if (member.shepherdId == null) return const SizedBox.shrink();

    final shepherdAsync = ref.watch(memberByIdProvider(member.shepherdId!));
    return _DetailCard(
      title: 'Shepherd',
      isDark: isDark,
      child: shepherdAsync.when(
        loading: () => const SizedBox(
            height: 40,
            child: Center(
                child: CircularProgressIndicator(strokeWidth: 2))),
        error: (_, st) => Text('—',
            style: TextStyle(
                fontSize: 13,
                color: isDark ? Colors.white : IcsColors.inkBg)),
        data: (shepherd) => shepherd != null
            ? Row(children: [
                CircleAvatar(
                  radius: 16,
                  backgroundColor:
                      IcsColors.accentRed.withValues(alpha: 0.12),
                  child: Text(shepherd.initials,
                      style: const TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.w700,
                          color: IcsColors.accentRed)),
                ),
                const SizedBox(width: IcsSpacing.m),
                Expanded(
                  child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(shepherd.displayName,
                            style: TextStyle(
                                fontSize: 14,
                                fontWeight: FontWeight.w600,
                                color: isDark
                                    ? Colors.white
                                    : IcsColors.inkBg)),
                        Text(shepherd.levelName,
                            style: TextStyle(
                                fontSize: 12,
                                color: isDark
                                    ? IcsColors.textMutedDark
                                    : IcsColors.textMuted)),
                      ]),
                ),
              ])
            : Text('No shepherd assigned',
                style: TextStyle(
                    fontSize: 13,
                    color: isDark
                        ? IcsColors.textMutedDark
                        : IcsColors.textMuted)),
      ),
    );
  }
}

// ── Shared primitives ─────────────────────────────────────────────────────────

class _DetailCard extends StatelessWidget {
  const _DetailCard(
      {required this.title,
      required this.isDark,
      required this.child});
  final String title;
  final bool   isDark;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: isDark ? IcsColors.stone1 : Colors.white,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
            color:
                isDark ? IcsColors.borderDark : IcsColors.borderLight),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(
                IcsSpacing.m, IcsSpacing.m, IcsSpacing.m, IcsSpacing.s),
            child: Text(title.toUpperCase(),
                style: TextStyle(
                    fontSize: 10,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 0.8,
                    color: isDark
                        ? IcsColors.textMutedDark
                        : IcsColors.textMuted)),
          ),
          Divider(
              height: 1,
              color:
                  isDark ? IcsColors.borderDark : IcsColors.borderLight),
          Padding(
              padding: const EdgeInsets.all(IcsSpacing.m),
              child: child),
        ],
      ),
    );
  }
}

class _DetailRow extends StatelessWidget {
  const _DetailRow({
    required this.label,
    required this.isDark,
    required this.trailing,
  });
  final String label;
  final bool   isDark;
  final Widget trailing;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: IcsSpacing.s),
      child: Row(children: [
        SizedBox(
          width: 110,
          child: Text(label,
              style: TextStyle(
                  fontSize: 12,
                  color: isDark
                      ? IcsColors.textMutedDark
                      : IcsColors.textMuted)),
        ),
        Expanded(child: trailing),
      ]),
    );
  }
}

class _LevelBadge extends StatelessWidget {
  const _LevelBadge({required this.level});
  final int level;

  static const _colors = [
    Color(0xFF6B7280), // L0 — grey
    Color(0xFF3B82F6), // L1 — blue
    Color(0xFF10B981), // L2 — green
    Color(0xFFF59E0B), // L3 — amber
    Color(0xFFEF4444), // L4 — red
    Color(0xFF8B5CF6), // L5 — purple
  ];

  @override
  Widget build(BuildContext context) {
    final color = _colors[level.clamp(0, 5)];
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Text('L$level',
          style: TextStyle(
              fontSize: 10,
              fontWeight: FontWeight.w700,
              color: color)),
    );
  }
}

class _SearchBar extends StatefulWidget {
  const _SearchBar({
    required this.value,
    required this.isDark,
    required this.onChanged,
  });
  final String              value;
  final bool                isDark;
  final ValueChanged<String> onChanged;

  @override
  State<_SearchBar> createState() => _SearchBarState();
}

class _SearchBarState extends State<_SearchBar> {
  late final TextEditingController _ctrl;

  @override
  void initState() {
    super.initState();
    _ctrl = TextEditingController(text: widget.value);
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return TextField(
      controller: _ctrl,
      onChanged:  widget.onChanged,
      style: TextStyle(
          fontSize: 14,
          color: widget.isDark ? Colors.white : IcsColors.inkBg),
      decoration: InputDecoration(
        isDense:   true,
        hintText:  'Search members…',
        hintStyle: TextStyle(
            fontSize: 14,
            color: widget.isDark
                ? IcsColors.textMutedDark
                : IcsColors.textMuted),
        prefixIcon: Icon(Icons.search,
            size: 18,
            color: widget.isDark
                ? IcsColors.textMutedDark
                : IcsColors.textMuted),
        suffixIcon: _ctrl.text.isNotEmpty
            ? IconButton(
                icon: const Icon(Icons.close, size: 16),
                onPressed: () {
                  _ctrl.clear();
                  widget.onChanged('');
                },
                color: widget.isDark
                    ? IcsColors.textMutedDark
                    : IcsColors.textMuted,
              )
            : null,
      ),
    );
  }
}

class _LevelChip extends StatelessWidget {
  const _LevelChip({
    required this.label,
    required this.selected,
    required this.isDark,
    required this.onTap,
  });
  final String       label;
  final bool         selected, isDark;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        margin: const EdgeInsets.only(right: IcsSpacing.xs),
        padding: const EdgeInsets.symmetric(
            horizontal: IcsSpacing.s, vertical: 4),
        decoration: BoxDecoration(
          color: selected
              ? IcsColors.accentRed
              : (isDark ? IcsColors.stone1 : IcsColors.stone2),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
              color: selected
                  ? IcsColors.accentRed
                  : (isDark
                      ? IcsColors.borderDark
                      : IcsColors.borderLight)),
        ),
        child: Text(label,
            style: TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.w600,
                color: selected
                    ? Colors.white
                    : (isDark
                        ? IcsColors.textMutedDark
                        : IcsColors.textMuted))),
      ),
    );
  }
}

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/theme/tokens.dart';
import '../../shared/member_list_tile.dart';
import 'member_form.dart';
import 'people_providers.dart';

class MemberList extends ConsumerWidget {
  const MemberList({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final filtered = ref.watch(filteredMembersProvider);
    final search = ref.watch(memberSearchProvider);
    final levelFilter = ref.watch(memberFilterLevelProvider);
    final selectedId = ref.watch(selectedMemberIdProvider);
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        // ── Toolbar ──────────────────────────────────────────────────────────
        Padding(
          padding: const EdgeInsets.fromLTRB(IcsSpacing.m, IcsSpacing.m, IcsSpacing.m, IcsSpacing.s),
          child: Row(
            children: [
              Expanded(
                child: _SearchBar(
                  value: search,
                  isDark: isDark,
                  onChanged: (v) => ref.read(memberSearchProvider.notifier).state = v,
                ),
              ),
              const SizedBox(width: IcsSpacing.s),
              _AddButton(isDark: isDark),
            ],
          ),
        ),
        // ── Level filter chips ────────────────────────────────────────────────
        SizedBox(
          height: 32,
          child: ListView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: IcsSpacing.m),
            children: [
              _FilterChip(
                label: 'All',
                selected: levelFilter == null,
                isDark: isDark,
                onTap: () => ref.read(memberFilterLevelProvider.notifier).state = null,
              ),
              ...List.generate(6, (i) => _FilterChip(
                label: 'L$i',
                selected: levelFilter == i,
                isDark: isDark,
                onTap: () => ref.read(memberFilterLevelProvider.notifier).state =
                    levelFilter == i ? null : i,
              )),
            ],
          ),
        ),
        const SizedBox(height: IcsSpacing.xs),
        Divider(height: 1, color: isDark ? IcsColors.borderDark : IcsColors.borderLight),
        // ── List ──────────────────────────────────────────────────────────────
        Expanded(
          child: filtered.when(
            loading: () => const Center(child: CircularProgressIndicator()),
            error: (e, _) => Center(child: Text('Error: $e')),
            data: (members) {
              if (members.isEmpty) {
                return Center(
                  child: Text(
                    search.isNotEmpty ? 'No members match "$search".' : 'No members yet.',
                    style: TextStyle(fontSize: 13, color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted),
                  ),
                );
              }
              return ListView.builder(
                itemCount: members.length,
                itemBuilder: (context, i) {
                  final m = members[i];
                  return MemberListTile(
                    displayName: m.displayName,
                    email: m.email,
                    competenceLevel: m.competenceLevel,
                    serviceOrder: m.serviceOrder,
                    selected: m.id == selectedId,
                    onTap: () => ref.read(selectedMemberIdProvider.notifier).state = m.id,
                  );
                },
              );
            },
          ),
        ),
        // ── Footer count ──────────────────────────────────────────────────────
        filtered.maybeWhen(
          data: (members) => Container(
            height: 28,
            padding: const EdgeInsets.symmetric(horizontal: IcsSpacing.m),
            decoration: BoxDecoration(
              border: Border(top: BorderSide(color: isDark ? IcsColors.borderDark : IcsColors.borderLight)),
            ),
            alignment: Alignment.centerLeft,
            child: Text(
              '${members.length} ${members.length == 1 ? 'member' : 'members'}',
              style: TextStyle(fontSize: 11, color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted),
            ),
          ),
          orElse: () => const SizedBox.shrink(),
        ),
      ],
    );
  }
}

// ── Search bar ────────────────────────────────────────────────────────────────

class _SearchBar extends StatefulWidget {
  const _SearchBar({required this.value, required this.isDark, required this.onChanged});
  final String value;
  final bool isDark;
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
      onChanged: widget.onChanged,
      style: TextStyle(fontSize: 13, color: widget.isDark ? Colors.white : IcsColors.inkBg),
      decoration: InputDecoration(
        isDense: true,
        hintText: 'Search members…',
        hintStyle: TextStyle(fontSize: 13, color: widget.isDark ? IcsColors.textMutedDark : IcsColors.textMuted),
        prefixIcon: Icon(Icons.search, size: 16, color: widget.isDark ? IcsColors.textMutedDark : IcsColors.textMuted),
        filled: true,
        fillColor: widget.isDark ? const Color(0xFF1A1A1A) : IcsColors.stone2,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(6),
          borderSide: BorderSide(color: widget.isDark ? IcsColors.borderDark : IcsColors.borderLight),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(6),
          borderSide: BorderSide(color: IcsColors.accentRed, width: 1.5),
        ),
        contentPadding: const EdgeInsets.symmetric(horizontal: IcsSpacing.m, vertical: 8),
        suffixIcon: _ctrl.text.isNotEmpty
            ? IconButton(
                icon: const Icon(Icons.close, size: 14),
                onPressed: () {
                  _ctrl.clear();
                  widget.onChanged('');
                },
                color: widget.isDark ? IcsColors.textMutedDark : IcsColors.textMuted,
              )
            : null,
      ),
    );
  }
}

// ── Add button ────────────────────────────────────────────────────────────────

class _AddButton extends ConsumerWidget {
  const _AddButton({required this.isDark});
  final bool isDark;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return ElevatedButton.icon(
      onPressed: () async {
        final result = await showDialog<bool>(
          context: context,
          builder: (_) => const MemberForm(mode: MemberFormMode.add),
        );
        if (result == true) ref.invalidate(membersProvider);
      },
      icon: const Icon(Icons.add, size: 14),
      label: const Text('Add member'),
      style: ElevatedButton.styleFrom(
        backgroundColor: IcsColors.accentRed,
        foregroundColor: Colors.white,
        padding: const EdgeInsets.symmetric(horizontal: IcsSpacing.m, vertical: 8),
        textStyle: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
      ),
    );
  }
}

// ── Level filter chip ─────────────────────────────────────────────────────────

class _FilterChip extends StatelessWidget {
  const _FilterChip({
    required this.label,
    required this.selected,
    required this.isDark,
    required this.onTap,
  });

  final String label;
  final bool selected;
  final bool isDark;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        margin: const EdgeInsets.only(right: IcsSpacing.xs),
        padding: const EdgeInsets.symmetric(horizontal: IcsSpacing.s, vertical: 4),
        decoration: BoxDecoration(
          color: selected
              ? IcsColors.accentRed
              : isDark
                  ? const Color(0xFF1A1A1A)
                  : IcsColors.stone2,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: selected ? IcsColors.accentRed : (isDark ? IcsColors.borderDark : IcsColors.borderLight),
          ),
        ),
        child: Text(
          label,
          style: TextStyle(
            fontSize: 11,
            fontWeight: FontWeight.w600,
            color: selected ? Colors.white : (isDark ? IcsColors.textMutedDark : IcsColors.textMuted),
          ),
        ),
      ),
    );
  }
}

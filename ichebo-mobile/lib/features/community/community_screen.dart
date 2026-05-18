import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:cached_network_image/cached_network_image.dart';
import '../../core/api/providers.dart';
import '../../shared/tokens/tokens.dart';
import '../../shared/widgets/badges.dart';
import '../../shared/widgets/empty_state.dart';
import '../../shared/widgets/ichebo_app_bar.dart';

final _memberSearchProvider = StateProvider.autoDispose<String>((ref) => '');
final _searchControllerProvider = Provider.autoDispose<TextEditingController>(
  (ref) {
    final ctrl = TextEditingController();
    ref.onDispose(ctrl.dispose);
    return ctrl;
  },
);

class CommunityScreen extends ConsumerWidget {
  const CommunityScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Scaffold(
      appBar: const IcheboAppBar(title: 'Community', watermarkText: 'COMMUNITY'),
      body: const Column(
        children: [
          _SearchBar(),
          Expanded(child: _MemberList()),
        ],
      ),
    );
  }
}

class _SearchBar extends ConsumerWidget {
  const _SearchBar();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final ctrl = ref.watch(_searchControllerProvider);
    return Padding(
      padding: const EdgeInsets.fromLTRB(
          IcheboSpacing.s, IcheboSpacing.xs, IcheboSpacing.s, IcheboSpacing.xs3),
      child: TextField(
        controller: ctrl,
        decoration: InputDecoration(
          hintText: 'Search members…',
          prefixIcon: const Icon(Icons.search, size: 20),
          suffixIcon: ValueListenableBuilder(
            valueListenable: ctrl,
            builder: (ctx, value, child) => value.text.isNotEmpty
                ? IconButton(
                    icon: const Icon(Icons.clear, size: 18),
                    onPressed: () {
                      ctrl.clear();
                      ref.read(_memberSearchProvider.notifier).state = '';
                    },
                  )
                : const SizedBox.shrink(),
          ),
        ),
        onChanged: (v) => ref.read(_memberSearchProvider.notifier).state = v,
      ),
    );
  }
}

class _MemberList extends ConsumerWidget {
  const _MemberList();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final query = ref.watch(_memberSearchProvider);
    final params = <String, String>{
      if (query.isNotEmpty) 'q': query,
      'page_size': '50',
    };
    final membersAsync = ref.watch(communityMembersProvider(params));

    return membersAsync.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (e, _) => EmptyState(message: e.toString()),
      data: (page) => page.results.isEmpty
          ? const EmptyState(
              icon: Icons.people_outline,
              message: 'No members found.',
            )
          : ListView.builder(
              itemCount: page.results.length,
              itemBuilder: (context, i) => _MemberTile(member: page.results[i]),
            ),
    );
  }
}

class _MemberTile extends StatelessWidget {
  const _MemberTile({required this.member});
  final Member member;

  @override
  Widget build(BuildContext context) {
    return ListTile(
      leading: _Avatar(member: member),
      title: Text(member.displayName),
      subtitle: member.serviceOrder != null
          ? Text(member.serviceOrder!)
          : Text(member.role.replaceAll('-', ' ')),
      trailing: LevelBadge(level: member.competenceLevel, showLabel: false),
      contentPadding: const EdgeInsets.symmetric(
        horizontal: IcheboSpacing.s,
        vertical: IcheboSpacing.xs3,
      ),
    );
  }
}

class _Avatar extends StatelessWidget {
  const _Avatar({required this.member});
  final Member member;

  @override
  Widget build(BuildContext context) {
    final initials = member.displayName.isNotEmpty
        ? member.displayName.trim().split(' ')
            .map((w) => w.isNotEmpty ? w[0].toUpperCase() : '')
            .take(2)
            .join()
        : '?';

    if (member.avatarUrl != null && member.avatarUrl!.isNotEmpty) {
      return CircleAvatar(
        radius: 20,
        backgroundColor: IcheboColors.stone2,
        backgroundImage: CachedNetworkImageProvider(member.avatarUrl!),
      );
    }

    final color = IcheboColors.forLevel(member.competenceLevel);
    return CircleAvatar(
      radius: 20,
      backgroundColor: color.withValues(alpha: 0.15),
      child: Text(
        initials,
        style: IcheboTextStyles.labelLarge.copyWith(color: color, fontSize: 13),
      ),
    );
  }
}

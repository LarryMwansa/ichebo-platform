import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:cached_network_image/cached_network_image.dart';
import '../../core/api/providers.dart';
import '../../shared/tokens/tokens.dart';
import '../../shared/widgets/badges.dart';
import '../../shared/widgets/empty_state.dart';
import '../../shared/widgets/ichebo_app_bar.dart';
import '../../shared/widgets/ichebo_card.dart';

final _memberSearchProvider = StateProvider.autoDispose<String>((ref) => '');
final _searchControllerProvider = Provider.autoDispose<TextEditingController>(
  (ref) {
    final ctrl = TextEditingController();
    ref.onDispose(ctrl.dispose);
    return ctrl;
  },
);
final _communityTabProvider = StateProvider.autoDispose<int>((ref) => 0);

class CommunityScreen extends ConsumerWidget {
  const CommunityScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final tab = ref.watch(_communityTabProvider);

    return Scaffold(
      appBar: const IcheboAppBar(title: 'Community', watermarkText: 'COMMUNITY'),
      body: Column(
        children: [
          _TabRow(
            currentTab: tab,
            onTab: (i) => ref.read(_communityTabProvider.notifier).state = i,
          ),
          Expanded(
            child: switch (tab) {
              0 => const Column(
                  children: [_SearchBar(), Expanded(child: _MemberList())],
                ),
              1 => const _AnnouncementList(),
              _ => const _GatheringList(),
            },
          ),
        ],
      ),
    );
  }
}

// ── Tab row ───────────────────────────────────────────────────────────────────

class _TabRow extends StatelessWidget {
  const _TabRow({required this.currentTab, required this.onTab});
  final int currentTab;
  final ValueChanged<int> onTab;

  @override
  Widget build(BuildContext context) {
    const labels = ['Members', 'Announcements', 'Schedule'];
    return Container(
      color: Theme.of(context).colorScheme.surface,
      padding: const EdgeInsets.symmetric(
        horizontal: IcheboSpacing.s,
        vertical: IcheboSpacing.xs3,
      ),
      child: Row(
        children: List.generate(labels.length, (i) {
          final active = i == currentTab;
          return Padding(
            padding: const EdgeInsets.only(right: IcheboSpacing.xs),
            child: GestureDetector(
              onTap: () => onTab(i),
              child: Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: IcheboSpacing.xs,
                  vertical: IcheboSpacing.xs3,
                ),
                decoration: BoxDecoration(
                  border: active
                      ? const Border(
                          bottom: BorderSide(color: IcheboColors.primary, width: 2))
                      : null,
                ),
                child: Text(
                  labels[i],
                  style: IcheboTextStyles.labelLarge.copyWith(
                    color: active ? IcheboColors.primary : IcheboColors.muted,
                  ),
                ),
              ),
            ),
          );
        }),
      ),
    );
  }
}

// ── Members tab ───────────────────────────────────────────────────────────────

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

// ── Announcements tab ─────────────────────────────────────────────────────────

class _AnnouncementList extends ConsumerWidget {
  const _AnnouncementList();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final announcementsAsync = ref.watch(announcementsProvider);

    return announcementsAsync.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (e, _) => EmptyState(message: e.toString()),
      data: (items) => items.isEmpty
          ? const EmptyState(
              icon: Icons.campaign_outlined,
              message: 'No announcements yet.',
            )
          : ListView.builder(
              padding: const EdgeInsets.all(IcheboSpacing.s),
              itemCount: items.length,
              itemBuilder: (context, i) => Padding(
                padding: const EdgeInsets.only(bottom: IcheboSpacing.xs),
                child: _AnnouncementCard(announcement: items[i]),
              ),
            ),
    );
  }
}

class _AnnouncementCard extends StatelessWidget {
  const _AnnouncementCard({required this.announcement});
  final Announcement announcement;

  @override
  Widget build(BuildContext context) {
    return IcheboCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(announcement.title,
              style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: IcheboSpacing.xs3),
          Text(
            announcement.body,
            style: Theme.of(context).textTheme.bodyMedium,
            maxLines: 4,
            overflow: TextOverflow.ellipsis,
          ),
          const SizedBox(height: IcheboSpacing.xs3),
          Row(
            children: [
              if (announcement.authorName != null) ...[
                Text(
                  announcement.authorName!,
                  style: IcheboTextStyles.bodySmall.copyWith(
                      color: IcheboColors.muted),
                ),
                const Text(' · ',
                    style: TextStyle(color: IcheboColors.mutedLight)),
              ],
              Text(
                _formatDate(announcement.createdAt),
                style: IcheboTextStyles.bodySmall.copyWith(
                    color: IcheboColors.mutedLight),
              ),
            ],
          ),
        ],
      ),
    );
  }

  String _formatDate(String iso) {
    try {
      final dt = DateTime.parse(iso).toLocal();
      return '${dt.day}/${dt.month}/${dt.year}';
    } catch (_) {
      return iso;
    }
  }
}

// ── Gathering schedule tab ────────────────────────────────────────────────────

class _GatheringList extends ConsumerWidget {
  const _GatheringList();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final gatheringsAsync = ref.watch(gatheringsProvider);

    return gatheringsAsync.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (e, _) => EmptyState(message: e.toString()),
      data: (items) => items.isEmpty
          ? const EmptyState(
              icon: Icons.event_outlined,
              message: 'No gatherings scheduled.',
            )
          : ListView.builder(
              padding: const EdgeInsets.all(IcheboSpacing.s),
              itemCount: items.length,
              itemBuilder: (context, i) => Padding(
                padding: const EdgeInsets.only(bottom: IcheboSpacing.xs),
                child: _GatheringCard(gathering: items[i]),
              ),
            ),
    );
  }
}

class _GatheringCard extends StatelessWidget {
  const _GatheringCard({required this.gathering});
  final Gathering gathering;

  @override
  Widget build(BuildContext context) {
    final dt = DateTime.tryParse(gathering.startsAt)?.toLocal();

    return IcheboCard(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // ── Date badge ───────────────────────────────────────────────
          if (dt != null)
            Container(
              width: 48,
              padding: const EdgeInsets.symmetric(vertical: IcheboSpacing.xs3),
              decoration: BoxDecoration(
                color: IcheboColors.primaryLight,
                borderRadius: IcheboRadius.s,
              ),
              alignment: Alignment.center,
              child: Column(
                children: [
                  Text(
                    _monthAbbr(dt.month),
                    style: IcheboTextStyles.labelCaps.copyWith(
                        color: IcheboColors.primary, fontSize: 9),
                  ),
                  Text(
                    '${dt.day}',
                    style: IcheboTextStyles.headlineLarge.copyWith(
                        color: IcheboColors.primary, height: 1.1),
                  ),
                ],
              ),
            ),
          const SizedBox(width: IcheboSpacing.xs),
          // ── Details ──────────────────────────────────────────────────
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(gathering.title,
                    style: Theme.of(context).textTheme.titleMedium),
                if (dt != null) ...[
                  const SizedBox(height: IcheboSpacing.xs3),
                  Text(
                    _timeRange(dt, gathering.endsAt),
                    style: IcheboTextStyles.bodySmall.copyWith(
                        color: IcheboColors.muted),
                  ),
                ],
                if (gathering.location != null &&
                    gathering.location!.isNotEmpty) ...[
                  const SizedBox(height: IcheboSpacing.xs3),
                  Row(
                    children: [
                      const Icon(Icons.place_outlined,
                          size: 13, color: IcheboColors.mutedLight),
                      const SizedBox(width: 4),
                      Expanded(
                        child: Text(
                          gathering.location!,
                          style: IcheboTextStyles.bodySmall.copyWith(
                              color: IcheboColors.muted),
                        ),
                      ),
                    ],
                  ),
                ],
                if (gathering.description != null &&
                    gathering.description!.isNotEmpty) ...[
                  const SizedBox(height: IcheboSpacing.xs3),
                  Text(
                    gathering.description!,
                    style: Theme.of(context).textTheme.bodySmall,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }

  static const _months = [
    '', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
  ];

  String _monthAbbr(int m) => m < _months.length ? _months[m] : '';

  String _timeRange(DateTime start, String? endsAt) {
    String fmt(DateTime dt) {
      final h = dt.hour % 12 == 0 ? 12 : dt.hour % 12;
      final m = dt.minute.toString().padLeft(2, '0');
      final period = dt.hour < 12 ? 'AM' : 'PM';
      return '$h:$m $period';
    }
    final s = fmt(start);
    if (endsAt == null) return s;
    final end = DateTime.tryParse(endsAt)?.toLocal();
    if (end == null) return s;
    return '$s – ${fmt(end)}';
  }
}

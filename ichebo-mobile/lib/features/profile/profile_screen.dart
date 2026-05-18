import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/auth/auth_provider.dart';
import '../../shared/tokens/tokens.dart';
import '../../shared/widgets/ichebo_app_bar.dart';
import '../../shared/widgets/ichebo_card.dart';
import '../../shared/widgets/badges.dart';
import '../../shared/widgets/ichebo_button.dart';
import '../../shared/widgets/empty_state.dart';

class ProfileScreen extends ConsumerWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(currentUserProvider);

    return Scaffold(
      appBar: const IcheboAppBar(title: 'Profile', watermarkText: 'PROFILE'),
      body: user == null
          ? const EmptyState(message: 'Loading profile...')
          : _ProfileBody(user: user),
    );
  }
}

class _ProfileBody extends ConsumerWidget {
  const _ProfileBody({required this.user});

  final dynamic user;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return ListView(
      padding: const EdgeInsets.all(IcheboSpacing.s),
      children: [
        IcheboCard(
          accent: true,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const LabelTag(label: 'Formation Journey'),
              const SizedBox(height: IcheboSpacing.xs),
              Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          user.displayName as String,
                          style: Theme.of(context).textTheme.titleLarge,
                        ),
                        const SizedBox(height: IcheboSpacing.xs3),
                        Text(
                          user.email as String,
                          style: Theme.of(context).textTheme.bodySmall,
                        ),
                      ],
                    ),
                  ),
                  LevelBadge(level: user.competenceLevel as int),
                ],
              ),
              const SizedBox(height: IcheboSpacing.s),
              StatusBadge(
                label: user.status as String,
                variant: (user.status as String) == 'active'
                    ? StatusVariant.active
                    : StatusVariant.muted,
              ),
            ],
          ),
        ),
        const SizedBox(height: IcheboSpacing.m),
        IcheboButton(
          label: 'Sign out',
          onPressed: () => ref.read(authProvider.notifier).logout(),
          variant: IcheboButtonVariant.secondary,
        ),
      ],
    );
  }
}

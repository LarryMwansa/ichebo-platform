import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/auth/auth_provider.dart';
import '../../shared/tokens/tokens.dart';
import '../../shared/widgets/ichebo_app_bar.dart';
import '../../shared/widgets/ichebo_card.dart';
import '../../shared/widgets/badges.dart';
import '../../shared/widgets/empty_state.dart';

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(currentUserProvider);

    return Scaffold(
      appBar: IcheboAppBar(
        title: 'Ichebo',
        subtitle: user != null ? 'Welcome back, ${user.displayName}' : null,
        watermarkText: 'HOME',
      ),
      body: user == null
          ? const EmptyState(message: 'Loading your dashboard...')
          : _HomeBody(user: user),
    );
  }
}

class _HomeBody extends StatelessWidget {
  const _HomeBody({required this.user});

  final dynamic user;

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(IcheboSpacing.s),
      children: [
        // Formation card
        IcheboCard(
          accent: true,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const LabelTag(label: 'Formation'),
              const SizedBox(height: IcheboSpacing.xs),
              Row(
                children: [
                  Expanded(
                    child: Text(
                      user.displayName as String,
                      style: Theme.of(context).textTheme.titleLarge,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                  LevelBadge(level: user.competenceLevel as int),
                ],
              ),
            ],
          ),
        ),
        const SizedBox(height: IcheboSpacing.s),
        // Paraclete digest placeholder
        IcheboCardDark(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const LabelTag(label: 'Paraclete'),
              const SizedBox(height: IcheboSpacing.xs),
              Text(
                'Your daily intelligence digest will appear here.',
                style: IcheboTextStyles.bodyMedium.copyWith(
                  color: IcheboColors.stone.withValues(alpha: 0.7),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

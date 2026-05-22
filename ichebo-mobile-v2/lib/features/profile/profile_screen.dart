import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/auth/auth_provider.dart';
import '../../core/auth/auth_models.dart';
import '../../shared/tokens/tokens.dart';
import '../../shared/widgets/badges.dart';
import '../../shared/widgets/empty_state.dart';
import '../../shared/widgets/ichebo_app_bar.dart';
import '../../shared/widgets/ichebo_button.dart';
import '../../shared/widgets/ichebo_card.dart';
import '../../shared/widgets/progress_bar.dart';

class ProfileScreen extends ConsumerWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(currentUserProvider);

    return Scaffold(
      appBar: const IcheboAppBar(title: 'Profile', watermarkText: 'PROFILE'),
      body: user == null
          ? const EmptyState(message: 'Loading…')
          : _ProfileBody(user: user),
    );
  }
}

class _ProfileBody extends ConsumerWidget {
  const _ProfileBody({required this.user});
  final AuthUser user;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return ListView(
      padding: const EdgeInsets.all(IcheboSpacing.s),
      children: [
        // ── Formation journey card ──────────────────────────────────────
        IcheboCardDark(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const LabelTag(label: 'Formation Journey'),
              const SizedBox(height: IcheboSpacing.s),
              Row(
                children: [
                  _AvatarCircle(user: user),
                  const SizedBox(width: IcheboSpacing.s),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          user.displayName,
                          style: IcheboTextStyles.titleLarge.copyWith(
                            color: IcheboColors.stone,
                          ),
                        ),
                        const SizedBox(height: IcheboSpacing.xs3),
                        Text(
                          user.email,
                          style: IcheboTextStyles.bodySmall.copyWith(
                            color: IcheboColors.stone.withValues(alpha: 0.55),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: IcheboSpacing.s),
              LevelBadge(level: user.competenceLevel),
              const SizedBox(height: IcheboSpacing.s),
              IcheboProgressBar(
                value: _levelProgress(user.competenceLevel),
                label: _levelName(user.competenceLevel),
                color: IcheboColors.forLevel(user.competenceLevel),
              ),
            ],
          ),
        ),

        const SizedBox(height: IcheboSpacing.s),

        // ── Status ──────────────────────────────────────────────────────
        IcheboCard(
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text('Account status', style: Theme.of(context).textTheme.bodyMedium),
              StatusBadge(
                label: user.status,
                variant: user.isActive ? StatusVariant.active : StatusVariant.muted,
              ),
            ],
          ),
        ),

        const SizedBox(height: IcheboSpacing.s),

        // ── Settings section ────────────────────────────────────────────
        IcheboCard(
          child: Column(
            children: [
              _SettingsRow(
                icon: Icons.notifications_outlined,
                label: 'Notifications',
                onTap: () {},
              ),
              const Divider(height: 1),
              _SettingsRow(
                icon: Icons.palette_outlined,
                label: 'Appearance',
                onTap: () {},
              ),
              const Divider(height: 1),
              _SettingsRow(
                icon: Icons.menu_book_outlined,
                label: 'Bible translation',
                onTap: () {},
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

        const SizedBox(height: IcheboSpacing.xl),
      ],
    );
  }

  double _levelProgress(int level) {
    // Visual only — progress within current level band (0.0–1.0).
    // Actual progress requires the certification API; use 0.5 as placeholder.
    if (level == 0) return 0.1;
    if (level >= 5) return 1.0;
    return 0.5;
  }

  String _levelName(int level) {
    const names = ['Seeker', 'Member', 'Disciple', 'Steward', 'Senior Steward', 'Architect'];
    return level < names.length ? names[level] : 'Level $level';
  }
}

class _AvatarCircle extends StatelessWidget {
  const _AvatarCircle({required this.user});
  final AuthUser user;

  @override
  Widget build(BuildContext context) {
    final initials = user.displayName.trim().split(' ')
        .map((w) => w.isNotEmpty ? w[0].toUpperCase() : '')
        .take(2)
        .join();
    final color = IcheboColors.forLevel(user.competenceLevel);

    return CircleAvatar(
      radius: 28,
      backgroundColor: color.withValues(alpha: 0.2),
      child: Text(
        initials,
        style: IcheboTextStyles.titleLarge.copyWith(color: color),
      ),
    );
  }
}

class _SettingsRow extends StatelessWidget {
  const _SettingsRow({required this.icon, required this.label, required this.onTap});
  final IconData icon;
  final String label;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: IcheboSpacing.xs),
        child: Row(
          children: [
            Icon(icon, size: 20, color: IcheboColors.muted),
            const SizedBox(width: IcheboSpacing.xs),
            Expanded(
              child: Text(label, style: Theme.of(context).textTheme.bodyMedium),
            ),
            const Icon(Icons.chevron_right, size: 18, color: IcheboColors.mutedLight),
          ],
        ),
      ),
    );
  }
}

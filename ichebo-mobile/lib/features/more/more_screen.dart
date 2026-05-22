import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../core/theme/tokens.dart';

class MoreScreen extends StatelessWidget {
  const MoreScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return Scaffold(
      appBar: AppBar(title: const Text('More')),
      body: ListView(
        children: [
          _MoreTile(
            icon: Icons.school_outlined,
            label: 'Learn',
            subtitle: 'Formation programmes & lessons',
            isDark: isDark,
            onTap: () => context.push('/learn'),
          ),
          _MoreTile(
            icon: Icons.gavel_outlined,
            label: 'Governance',
            subtitle: 'Reference library & mandates',
            isDark: isDark,
            onTap: () => context.push('/governance'),
          ),
          _MoreTile(
            icon: Icons.sync_outlined,
            label: 'Sync',
            subtitle: 'Sync status & conflict queue',
            isDark: isDark,
            onTap: () => context.push('/sync'),
          ),
          _MoreTile(
            icon: Icons.person_outline,
            label: 'Profile',
            subtitle: 'Formation journey & level badge',
            isDark: isDark,
            onTap: () => context.push('/profile'),
          ),
          _MoreTile(
            icon: Icons.settings_outlined,
            label: 'Settings',
            subtitle: 'Appearance, device & about',
            isDark: isDark,
            onTap: () => context.push('/settings'),
          ),
        ],
      ),
    );
  }
}

class _MoreTile extends StatelessWidget {
  const _MoreTile({
    required this.icon,
    required this.label,
    required this.subtitle,
    required this.isDark,
    required this.onTap,
  });
  final IconData icon;
  final String   label;
  final String   subtitle;
  final bool     isDark;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return ListTile(
      leading: Icon(icon, color: IcsColors.accentRed, size: 22),
      title: Text(label, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600)),
      subtitle: Text(subtitle, style: TextStyle(
        fontSize: 12,
        color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted,
      )),
      trailing: Icon(
        Icons.chevron_right,
        size: 18,
        color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted,
      ),
      onTap: onTap,
    );
  }
}

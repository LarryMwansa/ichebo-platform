import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/state/auth_state.dart';
import '../../core/theme/tokens.dart';

class ProfileScreen extends ConsumerWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authProvider);

    return Scaffold(
      backgroundColor: IcsColors.inkBg,
      appBar: AppBar(
        backgroundColor: IcsColors.stone1,
        title: const Text('Profile'),
      ),
      body: ListView(
        padding: const EdgeInsets.all(IcsSpacing.m),
        children: [
          _AvatarCard(auth: auth),
          const SizedBox(height: IcsSpacing.m),
          _InfoCard(auth: auth),
          const SizedBox(height: IcsSpacing.xl),
        ],
      ),
    );
  }
}

// ── Avatar card ───────────────────────────────────────────────────────────────

class _AvatarCard extends StatelessWidget {
  const _AvatarCard({required this.auth});
  final AuthState auth;

  @override
  Widget build(BuildContext context) {
    final initials = _initials(auth.email ?? '');

    return Container(
      padding: const EdgeInsets.all(IcsSpacing.l),
      decoration: BoxDecoration(
        color: IcsColors.stone1,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: IcsColors.borderDark),
      ),
      child: Column(
        children: [
          CircleAvatar(
            radius: 36,
            backgroundColor: IcsColors.accentBlue.withAlpha(51),
            child: Text(
              initials,
              style: const TextStyle(
                  color: IcsColors.accentBlue,
                  fontSize: 22,
                  fontWeight: FontWeight.w600),
            ),
          ),
          const SizedBox(height: IcsSpacing.m),
          Text(
            auth.email ?? '—',
            style: const TextStyle(
                color: Colors.white,
                fontSize: 16,
                fontWeight: FontWeight.w500),
          ),
          const SizedBox(height: IcsSpacing.xs),
          Text(
            auth.tenantName ?? '—',
            style: const TextStyle(
                color: IcsColors.textMuted, fontSize: 13),
          ),
        ],
      ),
    );
  }

  static String _initials(String email) {
    final name = email.split('@').first;
    final parts = name.split('.');
    if (parts.length >= 2) {
      return '${parts.first[0]}${parts[1][0]}'.toUpperCase();
    }
    return name.isNotEmpty ? name[0].toUpperCase() : '?';
  }
}

// ── Info card ─────────────────────────────────────────────────────────────────

class _InfoCard extends StatelessWidget {
  const _InfoCard({required this.auth});
  final AuthState auth;

  static const _levelNames = [
    'Seeker', 'Foundational', 'Active', 'Functional', 'Leader', 'Apostolic',
  ];

  @override
  Widget build(BuildContext context) {
    final levelName = _levelNames[auth.competenceLevel.clamp(0, 5)];
    final rows = <(String, String)>[
      ('Level', 'L${auth.competenceLevel} — $levelName'),
      ('Tenant', auth.tenantName ?? '—'),
    ];

    return Container(
      decoration: BoxDecoration(
        color: IcsColors.stone1,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: IcsColors.borderDark),
      ),
      child: Column(
        children: rows.indexed.map((entry) {
          final (i, row) = entry;
          final (label, value) = row;
          return Column(
            children: [
              if (i > 0) const Divider(height: 1, color: IcsColors.borderDark),
              Padding(
                padding: const EdgeInsets.symmetric(
                    horizontal: IcsSpacing.m, vertical: IcsSpacing.s + 2),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(label,
                        style: const TextStyle(
                            color: IcsColors.textMuted, fontSize: 13)),
                    Text(value,
                        style: const TextStyle(
                            color: Colors.white, fontSize: 13)),
                  ],
                ),
              ),
            ],
          );
        }).toList(),
      ),
    );
  }
}

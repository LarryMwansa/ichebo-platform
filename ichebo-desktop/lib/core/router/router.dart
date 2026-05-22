import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../../features/activity/activity_screen.dart';
import '../../features/governance/governance_screen.dart';
import '../../features/home/home_screen.dart';
import '../../features/people/people_screen.dart';
import '../../features/settings/settings_screen.dart';
import '../../features/sync/sync_screen.dart';
import '../../features/video/video_screen.dart';
import '../../features/wizard/wizard_screen.dart';
import '../../shell/desktop_shell.dart';
import '../state/shell_state.dart';

// ── Section placeholder screen ────────────────────────────────────────────────

class SectionPlaceholder extends StatelessWidget {
  const SectionPlaceholder({super.key, required this.section});
  final ShellSection section;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(section.icon, size: 48, color: Theme.of(context).colorScheme.primary.withValues(alpha: 0.3)),
          const SizedBox(height: 16),
          Text(
            section.label,
            style: Theme.of(context).textTheme.headlineMedium,
          ),
          const SizedBox(height: 8),
          Text(
            'Coming in a future phase.',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: Theme.of(context).textTheme.bodySmall?.color,
                ),
          ),
        ],
      ),
    );
  }
}

// ── Router ────────────────────────────────────────────────────────────────────

final appRouter = GoRouter(
  initialLocation: '/dashboard',
  redirect: (context, state) async {
    if (state.matchedLocation == '/wizard') return null;
    final prefs = await SharedPreferences.getInstance();
    final done = prefs.getBool('ics_wizard_done') ?? false;
    if (!done) return '/wizard';
    return null;
  },
  routes: [
    // First-run wizard — fullscreen, outside the shell
    GoRoute(
      path: '/wizard',
      builder: (context, state) => const WizardScreen(),
    ),
    ShellRoute(
      builder: (context, state, child) => DesktopShell(child: child),
      routes: [
        // Dashboard / Home section — live
        GoRoute(
          path: '/dashboard',
          builder: (context, state) => const HomeScreen(),
        ),
        // People section — live
        GoRoute(
          path: '/community',
          builder: (context, state) => const PeopleScreen(),
        ),
        // Activity section — live
        GoRoute(
          path: '/activity',
          builder: (context, state) => const ActivityScreen(),
        ),
        // Governance section — live
        GoRoute(
          path: '/governance',
          builder: (context, state) => const GovernanceScreen(),
        ),
        // Sync section — live
        GoRoute(
          path: '/sync',
          builder: (context, state) => const SyncScreen(),
        ),
        // Settings — live
        GoRoute(
          path: '/settings',
          builder: (context, state) => const SettingsScreen(),
        ),
        // Video & Broadcast — live
        GoRoute(
          path: '/video',
          builder: (context, state) => const VideoScreen(),
        ),
        // All other sections — placeholders
        for (final section in ShellSection.values)
          if (section != ShellSection.dashboard &&
              section != ShellSection.community &&
              section != ShellSection.activity &&
              section != ShellSection.governance &&
              section != ShellSection.sync &&
              section != ShellSection.video)
            GoRoute(
              path: section.route,
              builder: (context, state) => SectionPlaceholder(section: section),
            ),
      ],
    ),
  ],
);

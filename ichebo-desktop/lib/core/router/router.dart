import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
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
  routes: [
    ShellRoute(
      builder: (context, state, child) => DesktopShell(child: child),
      routes: [
        for (final section in ShellSection.values)
          GoRoute(
            path: section.route,
            builder: (context, state) => SectionPlaceholder(section: section),
          ),
      ],
    ),
  ],
);

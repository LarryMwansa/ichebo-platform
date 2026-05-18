import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../auth/auth_provider.dart';

// Nav items visible to all users.
const _baseItems = [
  _NavItem(path: '/home', label: 'Home', icon: Icons.home_outlined, activeIcon: Icons.home),
  _NavItem(path: '/bible', label: 'Bible', icon: Icons.menu_book_outlined, activeIcon: Icons.menu_book),
  _NavItem(path: '/learn', label: 'Learn', icon: Icons.school_outlined, activeIcon: Icons.school),
  _NavItem(path: '/activity', label: 'Activity', icon: Icons.check_circle_outline, activeIcon: Icons.check_circle),
  _NavItem(path: '/community', label: 'Community', icon: Icons.people_outline, activeIcon: Icons.people),
  _NavItem(path: '/profile', label: 'Profile', icon: Icons.person_outline, activeIcon: Icons.person),
];

// Governance tab — only shown to Level 3+ users.
const _governanceItem = _NavItem(
  path: '/governance',
  label: 'Governance',
  icon: Icons.account_balance_outlined,
  activeIcon: Icons.account_balance,
);

class BottomNavShell extends ConsumerWidget {
  const BottomNavShell({super.key, required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(currentUserProvider);
    final hasGov = user?.hasGovernanceAccess ?? false;

    final items = [
      ..._baseItems,
      if (hasGov) _governanceItem,
    ];

    final location = GoRouterState.of(context).uri.path;
    final currentIndex = _indexFor(items, location);

    return Scaffold(
      body: child,
      bottomNavigationBar: NavigationBar(
        selectedIndex: currentIndex.clamp(0, items.length - 1),
        onDestinationSelected: (i) => context.go(items[i].path),
        destinations: items
            .map((item) => NavigationDestination(
                  icon: Icon(item.icon),
                  selectedIcon: Icon(item.activeIcon),
                  label: item.label,
                  tooltip: item.label,
                ))
            .toList(),
      ),
    );
  }

  int _indexFor(List<_NavItem> items, String location) {
    for (var i = 0; i < items.length; i++) {
      if (location.startsWith(items[i].path)) return i;
    }
    return 0;
  }
}

class _NavItem {
  const _NavItem({
    required this.path,
    required this.label,
    required this.icon,
    required this.activeIcon,
  });

  final String path;
  final String label;
  final IconData icon;
  final IconData activeIcon;
}

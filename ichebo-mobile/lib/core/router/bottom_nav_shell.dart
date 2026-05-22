import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

class BottomNavShell extends StatelessWidget {
  const BottomNavShell({super.key, required this.child});
  final Widget child;

  static const _tabs = [
    _Tab('/home',      Icons.home_outlined,      Icons.home,      'Home'),
    _Tab('/community', Icons.groups_outlined,     Icons.groups,    'Community'),
    _Tab('/activity',  Icons.task_alt_outlined,   Icons.task_alt,  'Activity'),
    _Tab('/bible',     Icons.menu_book_outlined,  Icons.menu_book, 'Bible'),
    _Tab('/more',      Icons.grid_view_outlined,  Icons.grid_view, 'More'),
  ];

  int _currentIndex(BuildContext context) {
    final location = GoRouterState.of(context).matchedLocation;
    for (var i = 0; i < _tabs.length; i++) {
      if (location.startsWith(_tabs[i].path)) return i;
    }
    return 0;
  }

  @override
  Widget build(BuildContext context) {
    final current = _currentIndex(context);
    return Scaffold(
      body: child,
      bottomNavigationBar: NavigationBar(
        selectedIndex: current,
        onDestinationSelected: (i) => context.go(_tabs[i].path),
        destinations: _tabs.map((t) => NavigationDestination(
          icon:         Icon(t.icon),
          selectedIcon: Icon(t.selectedIcon),
          label:        t.label,
        )).toList(),
      ),
    );
  }
}

class _Tab {
  const _Tab(this.path, this.icon, this.selectedIcon, this.label);
  final String   path;
  final IconData icon;
  final IconData selectedIcon;
  final String   label;
}

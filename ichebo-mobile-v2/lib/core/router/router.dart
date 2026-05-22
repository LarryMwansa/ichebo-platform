import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../auth/auth_provider.dart';
import '../../features/auth/login_screen.dart';
import '../../features/auth/register_screen.dart';
import '../../features/auth/forgot_password_screen.dart';
import '../../features/home/home_screen.dart';
import '../../features/bible/bible_screen.dart';
import '../../features/learn/learn_screen.dart';
import '../../features/activity/activity_screen.dart';
import '../../features/community/community_screen.dart';
import '../../features/profile/profile_screen.dart';
import '../../features/governance/governance_screen.dart';
import '../../features/coordinator/coordinator_screen.dart';
import 'bottom_nav_shell.dart';

final routerProvider = Provider<GoRouter>((ref) {
  final authState = ref.watch(authProvider);

  return GoRouter(
    initialLocation: '/home',
    redirect: (context, state) {
      final isLoading = authState.isLoading;
      if (isLoading) return null;

      final auth = authState.valueOrNull;
      final isAuthed = auth is AuthAuthenticated;
      final isAuthRoute =
          state.uri.path.startsWith('/login') ||
          state.uri.path.startsWith('/register') ||
          state.uri.path.startsWith('/forgot-password');

      if (!isAuthed && !isAuthRoute) return '/login';
      if (isAuthed && isAuthRoute) return '/home';
      return null;
    },
    routes: [
      // ── Auth routes (no shell) ──────────────────────────────────────────
      GoRoute(
        path: '/login',
        builder: (ctx, state) => const LoginScreen(),
      ),
      GoRoute(
        path: '/register',
        builder: (ctx, state) => const RegisterScreen(),
      ),
      GoRoute(
        path: '/forgot-password',
        builder: (ctx, state) => const ForgotPasswordScreen(),
      ),

      // ── Shell routes (with bottom nav) ─────────────────────────────────
      ShellRoute(
        builder: (context, state, child) => BottomNavShell(child: child),
        routes: [
          GoRoute(
            path: '/home',
            builder: (ctx, state) => const HomeScreen(),
          ),
          GoRoute(
            path: '/bible',
            builder: (ctx, state) => const BibleScreen(),
          ),
          GoRoute(
            path: '/learn',
            builder: (ctx, state) => const LearnScreen(),
          ),
          GoRoute(
            path: '/activity',
            builder: (ctx, state) => const ActivityScreen(),
          ),
          GoRoute(
            path: '/community',
            builder: (ctx, state) => const CommunityScreen(),
          ),
          GoRoute(
            path: '/profile',
            builder: (ctx, state) => const ProfileScreen(),
          ),
          GoRoute(
            path: '/governance',
            builder: (ctx, state) => const GovernanceScreen(),
          ),
          GoRoute(
            path: '/coordinator',
            builder: (ctx, state) => const CoordinatorScreen(),
          ),
        ],
      ),
    ],
    errorBuilder: (_, state) => Scaffold(
      body: Center(child: Text('Page not found: ${state.uri}')),
    ),
  );
});

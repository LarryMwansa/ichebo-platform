import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../api/api_client.dart';
import 'auth_models.dart';

// ── Auth state ────────────────────────────────────────────────────────────────

sealed class AuthState {
  const AuthState();
}

class AuthLoading extends AuthState {
  const AuthLoading();
}

class AuthAuthenticated extends AuthState {
  const AuthAuthenticated(this.user);
  final AuthUser user;
}

class AuthUnauthenticated extends AuthState {
  const AuthUnauthenticated({this.error});
  final String? error;
}

// ── Notifier ──────────────────────────────────────────────────────────────────

class AuthNotifier extends AsyncNotifier<AuthState> {
  @override
  Future<AuthState> build() async {
    final client = ref.read(apiClientProvider);
    if (!await client.hasToken()) {
      return const AuthUnauthenticated();
    }
    try {
      final res = await client.get<Map<String, dynamic>>('auth/me/');
      final user = AuthUser.fromJson(res.data!);
      return AuthAuthenticated(user);
    } catch (_) {
      await client.deleteToken();
      return const AuthUnauthenticated();
    }
  }

  Future<void> login(String email, String password) async {
    state = const AsyncData(AuthLoading());
    final client = ref.read(apiClientProvider);
    try {
      final res = await client.post<Map<String, dynamic>>(
        'auth/login/',
        data: LoginRequest(email: email, password: password).toJson(),
      );
      final token = res.data!['token'] as String;
      await client.saveToken(token);
      final me = await client.get<Map<String, dynamic>>('auth/me/');
      final user = AuthUser.fromJson(me.data!);
      state = AsyncData(AuthAuthenticated(user));
    } on Exception catch (e) {
      state = AsyncData(AuthUnauthenticated(error: _friendlyError(e)));
    }
  }

  Future<void> register(String email, String password, String displayName) async {
    state = const AsyncData(AuthLoading());
    final client = ref.read(apiClientProvider);
    try {
      final res = await client.post<Map<String, dynamic>>(
        'auth/register/',
        data: RegisterRequest(
          email: email,
          password: password,
          displayName: displayName,
        ).toJson(),
      );
      final token = res.data!['token'] as String;
      await client.saveToken(token);
      final me = await client.get<Map<String, dynamic>>('auth/me/');
      final user = AuthUser.fromJson(me.data!);
      state = AsyncData(AuthAuthenticated(user));
    } on Exception catch (e) {
      state = AsyncData(AuthUnauthenticated(error: _friendlyError(e)));
    }
  }

  Future<void> logout() async {
    final client = ref.read(apiClientProvider);
    try {
      await client.post<void>('auth/logout/');
    } catch (_) {}
    await client.deleteToken();
    state = const AsyncData(AuthUnauthenticated());
  }

  String _friendlyError(Exception e) {
    final msg = e.toString();
    if (msg.contains('401') || msg.contains('Invalid')) {
      return 'Invalid email or password.';
    }
    if (msg.contains('400')) return 'Please check your details and try again.';
    if (msg.contains('SocketException') || msg.contains('connect')) {
      return 'No internet connection.';
    }
    return 'Something went wrong. Please try again.';
  }
}

final authProvider =
    AsyncNotifierProvider<AuthNotifier, AuthState>(AuthNotifier.new);

/// Convenience: current user or null.
final currentUserProvider = Provider<AuthUser?>((ref) {
  final auth = ref.watch(authProvider).valueOrNull;
  if (auth is AuthAuthenticated) return auth.user;
  return null;
});

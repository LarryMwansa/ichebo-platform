import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

const _tokenKey  = 'ics_auth_token';
const _emailKey  = 'ics_auth_email';
const _levelKey  = 'ics_competence_level';
const _tenantKey = 'ics_tenant_id';
const _nameKey   = 'ics_tenant_name';

class AuthState {
  const AuthState({
    this.token,
    this.email,
    this.competenceLevel = 0,
    this.tenantId,
    this.tenantName,
  });

  final String? token;
  final String? email;
  final int    competenceLevel;
  final String? tenantId;
  final String? tenantName;

  bool get isAuthenticated => token != null && token!.isNotEmpty;

  AuthState copyWith({
    String? token,
    String? email,
    int?    competenceLevel,
    String? tenantId,
    String? tenantName,
  }) => AuthState(
    token:            token           ?? this.token,
    email:            email           ?? this.email,
    competenceLevel:  competenceLevel ?? this.competenceLevel,
    tenantId:         tenantId        ?? this.tenantId,
    tenantName:       tenantName      ?? this.tenantName,
  );
}

class AuthNotifier extends Notifier<AuthState> {
  @override
  AuthState build() {
    _load();
    return const AuthState();
  }

  Future<void> _load() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString(_tokenKey);
    if (token != null && token.isNotEmpty) {
      state = AuthState(
        token:           token,
        email:           prefs.getString(_emailKey),
        competenceLevel: prefs.getInt(_levelKey) ?? 0,
        tenantId:        prefs.getString(_tenantKey),
        tenantName:      prefs.getString(_nameKey),
      );
    }
  }

  Future<void> login({
    required String token,
    required String email,
    required int    competenceLevel,
    required String tenantId,
    required String tenantName,
  }) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_tokenKey,  token);
    await prefs.setString(_emailKey,  email);
    await prefs.setInt(_levelKey,     competenceLevel);
    await prefs.setString(_tenantKey, tenantId);
    await prefs.setString(_nameKey,   tenantName);
    state = AuthState(
      token:           token,
      email:           email,
      competenceLevel: competenceLevel,
      tenantId:        tenantId,
      tenantName:      tenantName,
    );
  }

  Future<void> logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_tokenKey);
    await prefs.remove(_emailKey);
    await prefs.remove(_levelKey);
    await prefs.remove(_tenantKey);
    await prefs.remove(_nameKey);
    state = const AuthState();
  }
}

final authProvider = NotifierProvider<AuthNotifier, AuthState>(AuthNotifier.new);

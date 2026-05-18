// Auth models — mirrors /api/auth/me/ and /api/auth/login/ responses.

class AuthUser {
  const AuthUser({
    required this.id,
    required this.email,
    required this.displayName,
    required this.competenceLevel,
    required this.status,
    this.avatarUrl,
    this.fcmToken,
  });

  final String id;
  final String email;
  final String displayName;
  final int competenceLevel;
  final String status; // seeker | active | suspended | pending_verification
  final String? avatarUrl;
  final String? fcmToken;

  bool get isActive => status == 'active';
  bool get isSeeker => status == 'seeker';

  /// Level 3+ unlocks governance and coordinator features.
  bool get hasGovernanceAccess => competenceLevel >= 3;

  factory AuthUser.fromJson(Map<String, dynamic> json) => AuthUser(
        id: json['id'] as String,
        email: json['email'] as String,
        displayName: (json['display_name'] as String?) ?? json['email'] as String,
        competenceLevel: (json['competence_level'] as num?)?.toInt() ?? 0,
        status: (json['status'] as String?) ?? 'seeker',
        avatarUrl: json['avatar_url'] as String?,
        fcmToken: json['fcm_token'] as String?,
      );
}

class LoginRequest {
  const LoginRequest({required this.email, required this.password});

  final String email;
  final String password;

  Map<String, dynamic> toJson() => {'email': email, 'password': password};
}

class RegisterRequest {
  const RegisterRequest({
    required this.email,
    required this.password,
    required this.displayName,
  });

  final String email;
  final String password;
  final String displayName;

  Map<String, dynamic> toJson() => {
        'email': email,
        'password': password,
        'display_name': displayName,
      };
}

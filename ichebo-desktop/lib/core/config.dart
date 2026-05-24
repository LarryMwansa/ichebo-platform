import 'package:flutter/foundation.dart';

/// Single source of truth for the Ichebo Cloud base URL.
/// In debug builds, points to the local dev server.
/// In release builds, points to production.
class AppConfig {
  AppConfig._();

  static const String _prodBase = 'https://api.ichebo.org';
  static const String _devBase  = 'http://127.0.0.1:8001';

  static String get baseUrl => kDebugMode ? _devBase : _prodBase;

  static String get validateLicenceUrl => '$baseUrl/api/sync/validate-licence/';
  static String get syncPushUrl        => '$baseUrl/api/sync/push/';
  static String get syncPullUrl        => '$baseUrl/api/sync/pull/';
  static String get loginUrl           => '$baseUrl/api/auth/login/';
}

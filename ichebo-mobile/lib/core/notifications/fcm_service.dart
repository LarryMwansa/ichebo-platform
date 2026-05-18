import 'dart:io';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../api/api_client.dart';

// Top-level handler required by firebase_messaging for background messages.
@pragma('vm:entry-point')
Future<void> firebaseBackgroundMessageHandler(RemoteMessage message) async {
  // No app state available here — notification is shown by the OS automatically
  // when the app is in background/terminated.
}

final fcmServiceProvider = Provider<FcmService>((ref) {
  return FcmService(ref.read(apiClientProvider));
});

class FcmService {
  FcmService(this._client);

  final ApiClient _client;
  final _messaging = FirebaseMessaging.instance;
  final _localNotifications = FlutterLocalNotificationsPlugin();

  static const _androidChannel = AndroidNotificationChannel(
    'ichebo_default',
    'Ichebo Notifications',
    description: 'Formation, activity, and community notifications.',
    importance: Importance.high,
  );

  Future<void> initialise() async {
    // Register background handler.
    FirebaseMessaging.onBackgroundMessage(firebaseBackgroundMessageHandler);

    // Request permission (iOS / Android 13+).
    await _messaging.requestPermission(
      alert: true,
      badge: true,
      sound: true,
    );

    // Set up local notifications for foreground display.
    await _localNotifications.initialize(
      const InitializationSettings(
        android: AndroidInitializationSettings('@mipmap/ic_launcher'),
        iOS: DarwinInitializationSettings(),
      ),
    );

    if (Platform.isAndroid) {
      await _localNotifications
          .resolvePlatformSpecificImplementation<
              AndroidFlutterLocalNotificationsPlugin>()
          ?.createNotificationChannel(_androidChannel);
    }

    // Foreground messages — show via local notifications.
    FirebaseMessaging.onMessage.listen(_handleForeground);

    // Register token and refresh listener.
    await _uploadToken();
    _messaging.onTokenRefresh.listen((_) => _uploadToken());
  }

  Future<void> _uploadToken() async {
    try {
      final token = await _messaging.getToken();
      if (token == null) return;
      await _client.post<void>(
        'auth/fcm-token/',
        data: {'fcm_token': token},
      );
    } catch (e) {
      // Non-fatal — token will be re-uploaded on next launch.
      debugPrint('[FCM] token upload failed: $e');
    }
  }

  void _handleForeground(RemoteMessage message) {
    final notification = message.notification;
    final android = message.notification?.android;
    if (notification == null) return;

    _localNotifications.show(
      notification.hashCode,
      notification.title ?? 'Ichebo',
      notification.body,
      NotificationDetails(
        android: AndroidNotificationDetails(
          _androidChannel.id,
          _androidChannel.name,
          channelDescription: _androidChannel.description,
          icon: android?.smallIcon ?? '@mipmap/ic_launcher',
          importance: Importance.high,
          priority: Priority.high,
        ),
        iOS: const DarwinNotificationDetails(),
      ),
    );
  }
}

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';
import 'core/router/router.dart';
import 'core/theme/app_theme.dart';
import 'sync/sync_engine.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();

  // sqflite_common_ffi is required on desktop (Linux/macOS/Windows).
  // On Android/iOS the default databaseFactory is already set by sqflite.
  if (!kIsWeb && defaultTargetPlatform != TargetPlatform.android &&
      defaultTargetPlatform != TargetPlatform.iOS) {
    sqfliteFfiInit();
    databaseFactory = databaseFactoryFfi;
  }

  SyncEngine.instance.load();
  runApp(const ProviderScope(child: IcsMobileApp()));
}

class IcsMobileApp extends ConsumerWidget {
  const IcsMobileApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(routerProvider);
    return MaterialApp.router(
      title: 'Ichebo',
      debugShowCheckedModeBanner: false,
      theme:        IcsTheme.light,
      darkTheme:    IcsTheme.dark,
      themeMode:    ThemeMode.system,
      routerConfig: router,
    );
  }
}

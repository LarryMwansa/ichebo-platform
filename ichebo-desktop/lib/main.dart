import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'core/database/db.dart';
import 'core/router/router.dart';
import 'core/state/shell_state.dart';
import 'core/theme/theme.dart';
import 'sync/sync_engine.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  initSqfliteForDesktop();
  SyncEngine.instance.load(); // best-effort — app runs without it
  runApp(const ProviderScope(child: IcheboDesktopApp()));
}

class IcheboDesktopApp extends ConsumerWidget {
  const IcheboDesktopApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final themeMode = ref.watch(shellProvider).themeMode;

    return MaterialApp.router(
      title: 'Ichebo',
      debugShowCheckedModeBanner: false,
      theme: lightTheme(),
      darkTheme: darkTheme(),
      themeMode: themeMode,
      routerConfig: appRouter,
    );
  }
}

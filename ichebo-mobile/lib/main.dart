import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'core/router/router.dart';
import 'core/theme/app_theme.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
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

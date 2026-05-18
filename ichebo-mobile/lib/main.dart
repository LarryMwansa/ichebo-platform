import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'core/router/router.dart';
import 'shared/tokens/app_theme.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const ProviderScope(child: IcheboApp()));
}

class IcheboApp extends ConsumerWidget {
  const IcheboApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(routerProvider);

    return MaterialApp.router(
      title: 'Ichebo',
      debugShowCheckedModeBanner: false,
      theme: IcheboTheme.light,
      darkTheme: IcheboTheme.dark,
      themeMode: ThemeMode.system,
      routerConfig: router,
    );
  }
}

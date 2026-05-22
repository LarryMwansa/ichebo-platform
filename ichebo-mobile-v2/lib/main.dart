import 'package:firebase_core/firebase_core.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'core/notifications/fcm_service.dart';
import 'core/router/router.dart';
import 'shared/tokens/app_theme.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Firebase.initializeApp();
  runApp(const ProviderScope(child: IcheboApp()));
}

class IcheboApp extends ConsumerStatefulWidget {
  const IcheboApp({super.key});

  @override
  ConsumerState<IcheboApp> createState() => _IcheboAppState();
}

class _IcheboAppState extends ConsumerState<IcheboApp> {
  @override
  void initState() {
    super.initState();
    ref.read(fcmServiceProvider).initialise();
  }

  @override
  Widget build(BuildContext context) {
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

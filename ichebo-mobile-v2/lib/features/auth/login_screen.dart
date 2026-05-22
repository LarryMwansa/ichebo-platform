import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../core/auth/auth_provider.dart';
import '../../shared/tokens/tokens.dart';
import '../../shared/widgets/ichebo_button.dart';

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _emailCtrl = TextEditingController();
  final _passwordCtrl = TextEditingController();
  final _form = GlobalKey<FormState>();
  bool _obscure = true;

  @override
  void dispose() {
    _emailCtrl.dispose();
    _passwordCtrl.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_form.currentState!.validate()) return;
    await ref
        .read(authProvider.notifier)
        .login(_emailCtrl.text.trim(), _passwordCtrl.text);
  }

  @override
  Widget build(BuildContext context) {
    final auth = ref.watch(authProvider);
    final isLoading = auth.valueOrNull is AuthLoading;
    final error = auth.valueOrNull is AuthUnauthenticated
        ? (auth.valueOrNull as AuthUnauthenticated).error
        : null;

    return Scaffold(
      backgroundColor: IcheboColors.ink,
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(IcheboSpacing.s),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: IcheboSpacing.xl),
              // Dark Ink Hero header
              Text(
                'Welcome\nback.',
                style: IcheboTextStyles.displayMedium.copyWith(
                  color: IcheboColors.stone,
                  height: 1.1,
                ),
              ),
              const SizedBox(height: IcheboSpacing.xs3),
              Text(
                'Sign in to your Ichebo account.',
                style: IcheboTextStyles.bodyMedium.copyWith(
                  color: IcheboColors.stone.withValues(alpha: 0.55),
                ),
              ),
              const SizedBox(height: IcheboSpacing.xl),
              Form(
                key: _form,
                child: Column(
                  children: [
                    TextFormField(
                      controller: _emailCtrl,
                      keyboardType: TextInputType.emailAddress,
                      textInputAction: TextInputAction.next,
                      style: IcheboTextStyles.bodyMedium.copyWith(
                        color: IcheboColors.stone,
                      ),
                      decoration: InputDecoration(
                        labelText: 'Email address',
                        fillColor: IcheboColors.inkLight,
                        filled: true,
                        enabledBorder: OutlineInputBorder(
                          borderRadius: IcheboRadius.m,
                          borderSide: const BorderSide(
                              color: IcheboColors.darkBorder),
                        ),
                        focusedBorder: const OutlineInputBorder(
                          borderRadius: IcheboRadius.m,
                          borderSide: BorderSide(
                              color: IcheboColors.primary, width: 1.5),
                        ),
                        border: OutlineInputBorder(
                            borderRadius: IcheboRadius.m),
                        labelStyle: IcheboTextStyles.bodySmall.copyWith(
                            color: IcheboColors.mutedLight),
                      ),
                      validator: (v) =>
                          (v == null || !v.contains('@')) ? 'Enter a valid email' : null,
                    ),
                    const SizedBox(height: IcheboSpacing.xs),
                    TextFormField(
                      controller: _passwordCtrl,
                      obscureText: _obscure,
                      textInputAction: TextInputAction.done,
                      onFieldSubmitted: (_) => _submit(),
                      style: IcheboTextStyles.bodyMedium.copyWith(
                        color: IcheboColors.stone,
                      ),
                      decoration: InputDecoration(
                        labelText: 'Password',
                        fillColor: IcheboColors.inkLight,
                        filled: true,
                        enabledBorder: OutlineInputBorder(
                          borderRadius: IcheboRadius.m,
                          borderSide: const BorderSide(
                              color: IcheboColors.darkBorder),
                        ),
                        focusedBorder: const OutlineInputBorder(
                          borderRadius: IcheboRadius.m,
                          borderSide: BorderSide(
                              color: IcheboColors.primary, width: 1.5),
                        ),
                        border: OutlineInputBorder(
                            borderRadius: IcheboRadius.m),
                        labelStyle: IcheboTextStyles.bodySmall.copyWith(
                            color: IcheboColors.mutedLight),
                        suffixIcon: IconButton(
                          icon: Icon(
                            _obscure ? Icons.visibility_outlined : Icons.visibility_off_outlined,
                            color: IcheboColors.mutedLight,
                          ),
                          onPressed: () => setState(() => _obscure = !_obscure),
                        ),
                      ),
                      validator: (v) =>
                          (v == null || v.length < 6) ? 'Password too short' : null,
                    ),
                    if (error != null) ...[
                      const SizedBox(height: IcheboSpacing.xs),
                      Text(
                        error,
                        style: IcheboTextStyles.bodySmall.copyWith(
                          color: IcheboColors.errorDark,
                        ),
                      ),
                    ],
                    const SizedBox(height: IcheboSpacing.m),
                    IcheboButton(
                      label: 'Sign in',
                      onPressed: _submit,
                      loading: isLoading,
                    ),
                    const SizedBox(height: IcheboSpacing.xs3),
                    TextButton(
                      onPressed: () => context.go('/forgot-password'),
                      child: Text(
                        'Forgot password?',
                        style: IcheboTextStyles.bodySmall.copyWith(
                          color: IcheboColors.stone.withValues(alpha: 0.6),
                        ),
                      ),
                    ),
                    TextButton(
                      onPressed: () => context.go('/register'),
                      child: Text(
                        "Don't have an account? Register",
                        style: IcheboTextStyles.bodySmall.copyWith(
                          color: IcheboColors.stone.withValues(alpha: 0.6),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

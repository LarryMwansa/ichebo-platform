import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../core/auth/auth_provider.dart';
import '../../shared/tokens/tokens.dart';
import '../../shared/widgets/ichebo_button.dart';

class RegisterScreen extends ConsumerStatefulWidget {
  const RegisterScreen({super.key});

  @override
  ConsumerState<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends ConsumerState<RegisterScreen> {
  final _emailCtrl = TextEditingController();
  final _nameCtrl = TextEditingController();
  final _passwordCtrl = TextEditingController();
  final _form = GlobalKey<FormState>();
  bool _obscure = true;

  @override
  void dispose() {
    _emailCtrl.dispose();
    _nameCtrl.dispose();
    _passwordCtrl.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_form.currentState!.validate()) return;
    await ref.read(authProvider.notifier).register(
          _emailCtrl.text.trim(),
          _passwordCtrl.text,
          _nameCtrl.text.trim(),
        );
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
              Text(
                'Create your\naccount.',
                style: IcheboTextStyles.displayMedium.copyWith(
                  color: IcheboColors.stone,
                  height: 1.1,
                ),
              ),
              const SizedBox(height: IcheboSpacing.xs3),
              Text(
                'Begin your formation journey.',
                style: IcheboTextStyles.bodyMedium.copyWith(
                  color: IcheboColors.stone.withValues(alpha: 0.55),
                ),
              ),
              const SizedBox(height: IcheboSpacing.xl),
              Form(
                key: _form,
                child: Column(
                  children: [
                    _darkField(
                      controller: _nameCtrl,
                      label: 'Display name',
                      action: TextInputAction.next,
                      validator: (v) =>
                          (v == null || v.trim().isEmpty) ? 'Enter your name' : null,
                    ),
                    const SizedBox(height: IcheboSpacing.xs),
                    _darkField(
                      controller: _emailCtrl,
                      label: 'Email address',
                      keyboardType: TextInputType.emailAddress,
                      action: TextInputAction.next,
                      validator: (v) =>
                          (v == null || !v.contains('@')) ? 'Enter a valid email' : null,
                    ),
                    const SizedBox(height: IcheboSpacing.xs),
                    _darkField(
                      controller: _passwordCtrl,
                      label: 'Password',
                      obscure: _obscure,
                      action: TextInputAction.done,
                      onSubmitted: (_) => _submit(),
                      suffixIcon: IconButton(
                        icon: Icon(
                          _obscure ? Icons.visibility_outlined : Icons.visibility_off_outlined,
                          color: IcheboColors.mutedLight,
                        ),
                        onPressed: () => setState(() => _obscure = !_obscure),
                      ),
                      validator: (v) =>
                          (v == null || v.length < 8) ? 'Minimum 8 characters' : null,
                    ),
                    if (error != null) ...[
                      const SizedBox(height: IcheboSpacing.xs),
                      Text(
                        error,
                        style: IcheboTextStyles.bodySmall
                            .copyWith(color: IcheboColors.errorDark),
                      ),
                    ],
                    const SizedBox(height: IcheboSpacing.m),
                    IcheboButton(
                      label: 'Create account',
                      onPressed: _submit,
                      loading: isLoading,
                    ),
                    const SizedBox(height: IcheboSpacing.s),
                    TextButton(
                      onPressed: () => context.go('/login'),
                      child: Text(
                        'Already have an account? Sign in',
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

  Widget _darkField({
    required TextEditingController controller,
    required String label,
    TextInputType keyboardType = TextInputType.text,
    TextInputAction action = TextInputAction.next,
    bool obscure = false,
    Widget? suffixIcon,
    ValueChanged<String>? onSubmitted,
    FormFieldValidator<String>? validator,
  }) {
    return TextFormField(
      controller: controller,
      keyboardType: keyboardType,
      textInputAction: action,
      obscureText: obscure,
      onFieldSubmitted: onSubmitted,
      style: IcheboTextStyles.bodyMedium.copyWith(color: IcheboColors.stone),
      decoration: InputDecoration(
        labelText: label,
        fillColor: IcheboColors.inkLight,
        filled: true,
        enabledBorder: OutlineInputBorder(
          borderRadius: IcheboRadius.m,
          borderSide: const BorderSide(color: IcheboColors.darkBorder),
        ),
        focusedBorder: const OutlineInputBorder(
          borderRadius: IcheboRadius.m,
          borderSide: BorderSide(color: IcheboColors.primary, width: 1.5),
        ),
        border: OutlineInputBorder(borderRadius: IcheboRadius.m),
        labelStyle:
            IcheboTextStyles.bodySmall.copyWith(color: IcheboColors.mutedLight),
        suffixIcon: suffixIcon,
      ),
      validator: validator,
    );
  }
}

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../core/api/api_client.dart';
import '../../shared/tokens/tokens.dart';
import '../../shared/widgets/ichebo_button.dart';

class ForgotPasswordScreen extends ConsumerStatefulWidget {
  const ForgotPasswordScreen({super.key});

  @override
  ConsumerState<ForgotPasswordScreen> createState() =>
      _ForgotPasswordScreenState();
}

class _ForgotPasswordScreenState extends ConsumerState<ForgotPasswordScreen> {
  final _emailCtrl = TextEditingController();
  final _form = GlobalKey<FormState>();
  bool _loading = false;
  bool _sent = false;
  String? _error;

  @override
  void dispose() {
    _emailCtrl.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_form.currentState!.validate()) return;
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      await ref.read(apiClientProvider).post<void>(
        'auth/password-reset/',
        data: {'email': _emailCtrl.text.trim()},
      );
      if (mounted) setState(() => _sent = true);
    } catch (_) {
      // Don't reveal whether the email exists — just show success regardless.
      if (mounted) setState(() => _sent = true);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: IcheboColors.ink,
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(IcheboSpacing.s),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: IcheboSpacing.xl),
              IconButton(
                icon: const Icon(Icons.arrow_back,
                    color: IcheboColors.mutedLight),
                onPressed: () => context.go('/login'),
                padding: EdgeInsets.zero,
              ),
              const SizedBox(height: IcheboSpacing.s),
              Text(
                'Reset your\npassword.',
                style: IcheboTextStyles.displayMedium.copyWith(
                  color: IcheboColors.stone,
                  height: 1.1,
                ),
              ),
              const SizedBox(height: IcheboSpacing.xs3),
              Text(
                _sent
                    ? 'Check your email for a reset link.'
                    : 'Enter your email and we\'ll send you a reset link.',
                style: IcheboTextStyles.bodyMedium.copyWith(
                  color: IcheboColors.stone.withValues(alpha: 0.55),
                ),
              ),
              const SizedBox(height: IcheboSpacing.xl),
              if (_sent) ...[
                Container(
                  padding: const EdgeInsets.all(IcheboSpacing.s),
                  decoration: BoxDecoration(
                    color: IcheboColors.success.withValues(alpha: 0.12),
                    borderRadius: IcheboRadius.m,
                    border: Border.all(
                        color: IcheboColors.success.withValues(alpha: 0.3)),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.check_circle_outline,
                          color: IcheboColors.successDark, size: 20),
                      const SizedBox(width: IcheboSpacing.xs),
                      Expanded(
                        child: Text(
                          'If an account exists for ${_emailCtrl.text.trim()}, a reset link has been sent.',
                          style: IcheboTextStyles.bodySmall
                              .copyWith(color: IcheboColors.successDark),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: IcheboSpacing.m),
                IcheboButton(
                  label: 'Back to sign in',
                  onPressed: () => context.go('/login'),
                  variant: IcheboButtonVariant.secondary,
                ),
              ] else ...[
                Form(
                  key: _form,
                  child: Column(
                    children: [
                      TextFormField(
                        controller: _emailCtrl,
                        keyboardType: TextInputType.emailAddress,
                        textInputAction: TextInputAction.done,
                        onFieldSubmitted: (_) => _submit(),
                        style: IcheboTextStyles.bodyMedium
                            .copyWith(color: IcheboColors.stone),
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
                          border:
                              OutlineInputBorder(borderRadius: IcheboRadius.m),
                          labelStyle: IcheboTextStyles.bodySmall
                              .copyWith(color: IcheboColors.mutedLight),
                        ),
                        validator: (v) => (v == null || !v.contains('@'))
                            ? 'Enter a valid email'
                            : null,
                      ),
                      if (_error != null) ...[
                        const SizedBox(height: IcheboSpacing.xs),
                        Text(
                          _error!,
                          style: IcheboTextStyles.bodySmall
                              .copyWith(color: IcheboColors.errorDark),
                        ),
                      ],
                      const SizedBox(height: IcheboSpacing.m),
                      IcheboButton(
                        label: 'Send reset link',
                        onPressed: _submit,
                        loading: _loading,
                      ),
                      const SizedBox(height: IcheboSpacing.s),
                      TextButton(
                        onPressed: () => context.go('/login'),
                        child: Text(
                          'Back to sign in',
                          style: IcheboTextStyles.bodySmall.copyWith(
                            color: IcheboColors.stone.withValues(alpha: 0.6),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../../core/config.dart';
import '../../core/theme/tokens.dart';
import 'wizard_state.dart';

class StepAccount extends ConsumerStatefulWidget {
  const StepAccount({super.key});

  @override
  ConsumerState<StepAccount> createState() => _StepAccountState();
}

class _StepAccountState extends ConsumerState<StepAccount> {
  final _nameController = TextEditingController();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmController = TextEditingController();
  bool _obscurePassword = true;
  bool _obscureConfirm = true;

  @override
  void dispose() {
    _nameController.dispose();
    _emailController.dispose();
    _passwordController.dispose();
    _confirmController.dispose();
    super.dispose();
  }

  String? _validate() {
    if (_nameController.text.trim().isEmpty) return 'Enter your name.';
    if (_emailController.text.trim().isEmpty) return 'Enter your email.';
    if (!_emailController.text.contains('@')) return 'Enter a valid email address.';
    if (_passwordController.text.length < 8) return 'Password must be at least 8 characters.';
    if (_passwordController.text != _confirmController.text) return 'Passwords do not match.';
    return null;
  }

  Future<void> _createAccount() async {
    final err = _validate();
    if (err != null) {
      ref.read(wizardProvider.notifier).setError(err);
      return;
    }

    ref.read(wizardProvider.notifier).setLoading(true);
    final wizard = ref.read(wizardProvider);

    try {
      final response = await http.post(
        Uri.parse(AppConfig.loginUrl),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'email': _emailController.text.trim(),
          'password': _passwordController.text,
          'tenant_id': wizard.tenantId,
        }),
      ).timeout(const Duration(seconds: 15));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as Map<String, dynamic>;
        final token = data['token'] as String? ?? data['access'] as String? ?? '';
        final prefs = await SharedPreferences.getInstance();
        await prefs.setString('ics_auth_token', token);
        await prefs.setString('ics_admin_name', _nameController.text.trim());
        await prefs.setString('ics_admin_email', _emailController.text.trim());
        ref.read(wizardProvider.notifier).setAccountDetails(
          name: _nameController.text.trim(),
          email: _emailController.text.trim(),
        );
        ref.read(wizardProvider.notifier).advanceToSync();
      } else {
        final data = jsonDecode(response.body) as Map<String, dynamic>;
        ref.read(wizardProvider.notifier).setError(
          data['detail'] as String? ?? 'Login failed. Check your credentials.',
        );
      }
    } catch (e) {
      ref.read(wizardProvider.notifier).setError(
        'Could not reach Ichebo Cloud. Check your internet connection.',
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final wizard = ref.watch(wizardProvider);

    return Column(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text(
          'Set up your account',
          style: const TextStyle(
            fontFamily: 'Playfair Display',
            fontSize: 24,
            fontWeight: FontWeight.w700,
            color: Colors.white,
          ),
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: IcsSpacing.xs),
        Text(
          'Create the administrator account for this device.',
          style: TextStyle(fontSize: 13, color: IcsColors.textMutedDark),
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: IcsSpacing.xl),
        _WizardField(label: 'Your name', controller: _nameController, hint: 'Full name'),
        const SizedBox(height: IcsSpacing.m),
        _WizardField(
          label: 'Email',
          controller: _emailController,
          hint: 'admin@community.org',
          keyboardType: TextInputType.emailAddress,
        ),
        const SizedBox(height: IcsSpacing.m),
        _WizardField(
          label: 'Password',
          controller: _passwordController,
          hint: '••••••••',
          obscure: _obscurePassword,
          onToggleObscure: () => setState(() => _obscurePassword = !_obscurePassword),
        ),
        const SizedBox(height: IcsSpacing.m),
        _WizardField(
          label: 'Confirm password',
          controller: _confirmController,
          hint: '••••••••',
          obscure: _obscureConfirm,
          onToggleObscure: () => setState(() => _obscureConfirm = !_obscureConfirm),
          onSubmitted: (_) => _createAccount(),
        ),
        if (wizard.error != null) ...[
          const SizedBox(height: IcsSpacing.s),
          Text(
            wizard.error!,
            style: TextStyle(fontSize: 12, color: IcsColors.error),
            textAlign: TextAlign.center,
          ),
        ],
        const SizedBox(height: IcsSpacing.m),
        SizedBox(
          height: 44,
          child: ElevatedButton(
            onPressed: wizard.isLoading ? null : _createAccount,
            style: ElevatedButton.styleFrom(
              backgroundColor: IcsColors.accentRed,
              foregroundColor: Colors.white,
              disabledBackgroundColor: IcsColors.accentRed.withValues(alpha: 0.5),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.all(IcsRadius.s),
              ),
            ),
            child: wizard.isLoading
                ? const SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                  )
                : const Text(
                    'Create account and continue',
                    style: TextStyle(fontWeight: FontWeight.w600),
                  ),
          ),
        ),
      ],
    );
  }
}

class _WizardField extends StatelessWidget {
  const _WizardField({
    required this.label,
    required this.controller,
    required this.hint,
    this.keyboardType,
    this.obscure = false,
    this.onToggleObscure,
    this.onSubmitted,
  });

  final String label;
  final TextEditingController controller;
  final String hint;
  final TextInputType? keyboardType;
  final bool obscure;
  final VoidCallback? onToggleObscure;
  final ValueChanged<String>? onSubmitted;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: IcsColors.textMutedDark),
        ),
        const SizedBox(height: 6),
        TextField(
          controller: controller,
          keyboardType: keyboardType,
          obscureText: obscure,
          onSubmitted: onSubmitted,
          style: const TextStyle(fontSize: 14, color: Colors.white),
          decoration: InputDecoration(
            hintText: hint,
            hintStyle: TextStyle(color: IcsColors.textMutedDark.withValues(alpha: 0.4)),
            filled: true,
            fillColor: const Color(0xFF1A1A1A),
            border: OutlineInputBorder(
              borderRadius: BorderRadius.all(IcsRadius.s),
              borderSide: BorderSide(color: IcsColors.borderDark),
            ),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.all(IcsRadius.s),
              borderSide: BorderSide(color: IcsColors.accentRed, width: 1.5),
            ),
            contentPadding: const EdgeInsets.symmetric(
              horizontal: IcsSpacing.m,
              vertical: 12,
            ),
            suffixIcon: onToggleObscure != null
                ? IconButton(
                    icon: Icon(
                      obscure ? Icons.visibility_off_outlined : Icons.visibility_outlined,
                      size: 16,
                      color: IcsColors.textMutedDark,
                    ),
                    onPressed: onToggleObscure,
                  )
                : null,
          ),
        ),
      ],
    );
  }
}

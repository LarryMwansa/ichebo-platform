import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../core/api/providers.dart';
import '../../core/state/auth_state.dart';
import '../../core/theme/tokens.dart';

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _formKey    = GlobalKey<FormState>();
  final _emailCtrl  = TextEditingController();
  final _passCtrl   = TextEditingController();
  bool  _loading    = false;
  bool  _obscure    = true;
  String? _error;

  @override
  void dispose() {
    _emailCtrl.dispose();
    _passCtrl.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() { _loading = true; _error = null; });
    try {
      final api  = ref.read(apiClientProvider);
      final data = await api.post('/auth/login/', {
        'email':    _emailCtrl.text.trim(),
        'password': _passCtrl.text,
      });
      final user = data['user'] as Map<String, dynamic>;
      await ref.read(authProvider.notifier).login(
        token:           data['token'] as String,
        email:           user['email'] as String,
        competenceLevel: (user['competence_level'] as num?)?.toInt() ?? 0,
        tenantId:        user['tenant_id'] as String? ?? '',
        tenantName:      user['tenant_name'] as String? ?? '',
      );
      if (mounted) context.go('/home');
    } catch (e) {
      setState(() { _error = e.toString(); });
    } finally {
      if (mounted) setState(() { _loading = false; });
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(IcsSpacing.l),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const SizedBox(height: IcsSpacing.xl),
                Text('Ichebo',
                    style: Theme.of(context).textTheme.headlineLarge?.copyWith(
                      color: IcsColors.accentRed,
                    )),
                const SizedBox(height: IcsSpacing.xs),
                Text('Sign in to your community',
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted,
                    )),
                const SizedBox(height: IcsSpacing.xl),
                TextFormField(
                  controller: _emailCtrl,
                  keyboardType: TextInputType.emailAddress,
                  textInputAction: TextInputAction.next,
                  decoration: const InputDecoration(
                    labelText: 'Email',
                    prefixIcon: Icon(Icons.email_outlined, size: 18),
                  ),
                  validator: (v) =>
                      (v == null || !v.contains('@')) ? 'Enter a valid email' : null,
                ),
                const SizedBox(height: IcsSpacing.m),
                TextFormField(
                  controller: _passCtrl,
                  obscureText: _obscure,
                  textInputAction: TextInputAction.done,
                  onFieldSubmitted: (_) => _submit(),
                  decoration: InputDecoration(
                    labelText: 'Password',
                    prefixIcon: const Icon(Icons.lock_outline, size: 18),
                    suffixIcon: IconButton(
                      icon: Icon(
                        _obscure ? Icons.visibility_outlined : Icons.visibility_off_outlined,
                        size: 18,
                      ),
                      onPressed: () => setState(() => _obscure = !_obscure),
                    ),
                  ),
                  validator: (v) =>
                      (v == null || v.length < 6) ? 'Password too short' : null,
                ),
                if (_error != null) ...[
                  const SizedBox(height: IcsSpacing.m),
                  Container(
                    padding: const EdgeInsets.all(IcsSpacing.m),
                    decoration: BoxDecoration(
                      color: const Color(0xFFDC2626).withValues(alpha: 0.1),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Text(_error!,
                        style: const TextStyle(
                          fontSize: 13, color: Color(0xFFDC2626),
                        )),
                  ),
                ],
                const SizedBox(height: IcsSpacing.l),
                FilledButton(
                  onPressed: _loading ? null : _submit,
                  style: FilledButton.styleFrom(
                    backgroundColor: IcsColors.accentRed,
                    padding: const EdgeInsets.symmetric(vertical: 14),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(8),
                    ),
                  ),
                  child: _loading
                      ? const SizedBox(
                          height: 18, width: 18,
                          child: CircularProgressIndicator(
                            strokeWidth: 2, color: Colors.white,
                          ),
                        )
                      : const Text('Sign in',
                          style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600)),
                ),
                const SizedBox(height: IcsSpacing.m),
                TextButton(
                  onPressed: () => context.push('/forgot-password'),
                  child: Text('Forgot password?',
                      style: TextStyle(
                        fontSize: 13,
                        color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted,
                      )),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

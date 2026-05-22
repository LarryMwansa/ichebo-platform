import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../core/api/providers.dart';
import '../../core/state/auth_state.dart';
import '../../core/theme/tokens.dart';

class RegisterScreen extends ConsumerStatefulWidget {
  const RegisterScreen({super.key});

  @override
  ConsumerState<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends ConsumerState<RegisterScreen> {
  final _formKey      = GlobalKey<FormState>();
  final _firstCtrl    = TextEditingController();
  final _lastCtrl     = TextEditingController();
  final _emailCtrl    = TextEditingController();
  final _passCtrl     = TextEditingController();
  bool  _loading      = false;
  bool  _obscure      = true;
  String? _error;

  @override
  void dispose() {
    _firstCtrl.dispose();
    _lastCtrl.dispose();
    _emailCtrl.dispose();
    _passCtrl.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() { _loading = true; _error = null; });
    try {
      final api  = ref.read(apiClientProvider);
      final data = await api.post('/auth/register/', {
        'first_name': _firstCtrl.text.trim(),
        'last_name':  _lastCtrl.text.trim(),
        'email':      _emailCtrl.text.trim(),
        'password':   _passCtrl.text,
      });
      await ref.read(authProvider.notifier).login(
        token:           data['token'] as String,
        email:           data['email'] as String,
        competenceLevel: (data['competence_level'] as num?)?.toInt() ?? 0,
        tenantId:        data['tenant_id'] as String? ?? '',
        tenantName:      data['tenant_name'] as String? ?? '',
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
      appBar: AppBar(title: const Text('Create account')),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(IcsSpacing.l),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Row(children: [
                  Expanded(
                    child: TextFormField(
                      controller: _firstCtrl,
                      textInputAction: TextInputAction.next,
                      decoration: const InputDecoration(labelText: 'First name'),
                      validator: (v) => (v == null || v.trim().isEmpty)
                          ? 'Required' : null,
                    ),
                  ),
                  const SizedBox(width: IcsSpacing.m),
                  Expanded(
                    child: TextFormField(
                      controller: _lastCtrl,
                      textInputAction: TextInputAction.next,
                      decoration: const InputDecoration(labelText: 'Last name'),
                      validator: (v) => (v == null || v.trim().isEmpty)
                          ? 'Required' : null,
                    ),
                  ),
                ]),
                const SizedBox(height: IcsSpacing.m),
                TextFormField(
                  controller: _emailCtrl,
                  keyboardType: TextInputType.emailAddress,
                  textInputAction: TextInputAction.next,
                  decoration: const InputDecoration(labelText: 'Email'),
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
                    suffixIcon: IconButton(
                      icon: Icon(
                        _obscure ? Icons.visibility_outlined : Icons.visibility_off_outlined,
                        size: 18,
                      ),
                      onPressed: () => setState(() => _obscure = !_obscure),
                    ),
                  ),
                  validator: (v) =>
                      (v == null || v.length < 8) ? 'At least 8 characters' : null,
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
                        style: const TextStyle(fontSize: 13, color: Color(0xFFDC2626))),
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
                      : const Text('Create account',
                          style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600)),
                ),
                const SizedBox(height: IcsSpacing.m),
                Row(mainAxisAlignment: MainAxisAlignment.center, children: [
                  Text('Already have an account? ',
                      style: TextStyle(
                        fontSize: 13,
                        color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted,
                      )),
                  TextButton(
                    onPressed: () => context.go('/login'),
                    style: TextButton.styleFrom(padding: EdgeInsets.zero),
                    child: const Text('Sign in',
                        style: TextStyle(
                          fontSize: 13, color: IcsColors.accentRed,
                          fontWeight: FontWeight.w600,
                        )),
                  ),
                ]),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

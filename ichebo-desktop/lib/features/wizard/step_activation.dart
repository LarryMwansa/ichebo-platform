import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:uuid/uuid.dart';
import '../../core/config.dart';
import '../../core/theme/tokens.dart';
import 'wizard_state.dart';

class StepActivation extends ConsumerStatefulWidget {
  const StepActivation({super.key});

  @override
  ConsumerState<StepActivation> createState() => _StepActivationState();
}

class _StepActivationState extends ConsumerState<StepActivation> {
  final _controller = TextEditingController();
  final _focusNode = FocusNode();

  @override
  void dispose() {
    _controller.dispose();
    _focusNode.dispose();
    super.dispose();
  }

  Future<void> _activate() async {
    final key = _controller.text.trim().toUpperCase();
    if (key.isEmpty) return;

    ref.read(wizardProvider.notifier).setLicenceKey(key);
    ref.read(wizardProvider.notifier).setLoading(true);

    try {
      final response = await http.post(
        Uri.parse(AppConfig.validateLicenceUrl),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'licence_key': key}),
      ).timeout(const Duration(seconds: 15));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as Map<String, dynamic>;
        final deviceId = const Uuid().v4();
        final prefs = await SharedPreferences.getInstance();
        await prefs.setString('ics_tenant_id', data['tenant_id'] as String);
        await prefs.setString('ics_device_id', deviceId);
        await prefs.setString('ics_tenant_name', data['tenant_name'] as String? ?? '');
        ref.read(wizardProvider.notifier).setActivationResult(
          tenantId: data['tenant_id'] as String,
          tenantName: data['tenant_name'] as String? ?? '',
          deviceId: deviceId,
        );
      } else {
        final data = jsonDecode(response.body) as Map<String, dynamic>;
        ref.read(wizardProvider.notifier).setError(
          data['detail'] as String? ?? _statusMessage(response.statusCode),
        );
      }
    } catch (e) {
      ref.read(wizardProvider.notifier).setError(
        'Could not reach Ichebo Cloud. Check your internet connection.',
      );
    }
  }

  String _statusMessage(int code) => switch (code) {
        403 => 'Licence key revoked.',
        404 => 'Licence key not found.',
        410 => 'Licence key expired.',
        _ => 'Activation failed (error $code). Contact support.',
      };

  @override
  Widget build(BuildContext context) {
    final wizard = ref.watch(wizardProvider);

    return Column(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text(
          'Welcome to Ichebo Desktop',
          style: TextStyle(
            fontFamily: 'Playfair Display',
            fontSize: 28,
            fontWeight: FontWeight.w700,
            color: Colors.white,
          ),
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: IcsSpacing.s),
        Text(
          'Your community\'s operating system.\nWorks offline. Syncs when connected.',
          style: TextStyle(fontSize: 14, color: IcsColors.textMutedDark, height: 1.5),
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: IcsSpacing.xl),
        Text(
          'To begin, enter your licence key.',
          style: TextStyle(fontSize: 13, color: IcsColors.textMutedDark),
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: IcsSpacing.m),
        TextField(
          controller: _controller,
          focusNode: _focusNode,
          autofocus: true,
          textCapitalization: TextCapitalization.characters,
          inputFormatters: [
            FilteringTextInputFormatter.allow(RegExp(r'[A-Za-z0-9\-]')),
            LengthLimitingTextInputFormatter(39),
          ],
          style: const TextStyle(
            fontFamily: 'monospace',
            fontSize: 18,
            color: Colors.white,
            letterSpacing: 2,
          ),
          decoration: InputDecoration(
            hintText: 'XXXX-XXXX-XXXX-XXXX',
            hintStyle: TextStyle(color: IcsColors.textMutedDark.withValues(alpha: 0.4), letterSpacing: 2),
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
              vertical: IcsSpacing.m,
            ),
          ),
          onSubmitted: (_) => _activate(),
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
            onPressed: wizard.isLoading ? null : _activate,
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
                : const Text('Activate', style: TextStyle(fontWeight: FontWeight.w600)),
          ),
        ),
        const SizedBox(height: IcsSpacing.m),
        Text(
          "Don't have a key? Apply at ichebo.org",
          style: TextStyle(fontSize: 11, color: IcsColors.textMutedDark.withValues(alpha: 0.6)),
          textAlign: TextAlign.center,
        ),
      ],
    );
  }
}

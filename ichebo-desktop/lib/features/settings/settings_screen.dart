import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../../core/theme/tokens.dart';
import '../../core/state/shell_state.dart';

class SettingsScreen extends ConsumerWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final shell  = ref.watch(shellProvider);
    final notifier = ref.read(shellProvider.notifier);
    final isDark = shell.themeMode == ThemeMode.dark;

    return SingleChildScrollView(
      padding: const EdgeInsets.all(IcsSpacing.l),
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: IcsDimensions.canvasMaxWidth),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              _SectionHeader(title: 'Appearance', isDark: isDark),
              _ThemeRow(isDark: isDark, notifier: notifier, current: shell.themeMode),
              _Divider(isDark: isDark),
              _SectionHeader(title: 'Device', isDark: isDark),
              _DeviceInfoRow(isDark: isDark),
              _Divider(isDark: isDark),
              _SectionHeader(title: 'About', isDark: isDark),
              _AboutRow(isDark: isDark),
            ],
          ),
        ),
      ),
    );
  }
}

// ── Theme row ─────────────────────────────────────────────────────────────────

class _ThemeRow extends StatelessWidget {
  const _ThemeRow({
    required this.isDark,
    required this.notifier,
    required this.current,
  });
  final bool isDark;
  final ShellNotifier notifier;
  final ThemeMode current;

  @override
  Widget build(BuildContext context) {
    return _SettingsRow(
      icon: Icons.dark_mode_outlined,
      label: 'Appearance',
      isDark: isDark,
      trailing: _ThemeSegment(current: current, notifier: notifier, isDark: isDark),
    );
  }
}

class _ThemeSegment extends StatelessWidget {
  const _ThemeSegment({
    required this.current,
    required this.notifier,
    required this.isDark,
  });
  final ThemeMode current;
  final ShellNotifier notifier;
  final bool isDark;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        _ThemeChip(
          label: 'Dark',
          selected: current == ThemeMode.dark,
          isDark: isDark,
          onTap: () => notifier.setThemeMode(ThemeMode.dark),
        ),
        const SizedBox(width: IcsSpacing.xs),
        _ThemeChip(
          label: 'Light',
          selected: current == ThemeMode.light,
          isDark: isDark,
          onTap: () => notifier.setThemeMode(ThemeMode.light),
        ),
        const SizedBox(width: IcsSpacing.xs),
        _ThemeChip(
          label: 'System',
          selected: current == ThemeMode.system,
          isDark: isDark,
          onTap: () => notifier.setThemeMode(ThemeMode.system),
        ),
      ],
    );
  }
}

class _ThemeChip extends StatelessWidget {
  const _ThemeChip({
    required this.label,
    required this.selected,
    required this.isDark,
    required this.onTap,
  });
  final String label;
  final bool selected, isDark;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: IcsSpacing.s, vertical: 4),
        decoration: BoxDecoration(
          color: selected
              ? IcsColors.accentRed
              : (isDark ? const Color(0xFF1A1A1A) : IcsColors.stone2),
          borderRadius: BorderRadius.circular(6),
          border: Border.all(
            color: selected
                ? IcsColors.accentRed
                : (isDark ? IcsColors.borderDark : IcsColors.borderLight),
          ),
        ),
        child: Text(label,
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w600,
              color: selected
                  ? Colors.white
                  : (isDark ? IcsColors.textMutedDark : IcsColors.textMuted),
            )),
      ),
    );
  }
}

// ── Device info row ───────────────────────────────────────────────────────────

class _DeviceInfoRow extends StatefulWidget {
  const _DeviceInfoRow({required this.isDark});
  final bool isDark;

  @override
  State<_DeviceInfoRow> createState() => _DeviceInfoRowState();
}

class _DeviceInfoRowState extends State<_DeviceInfoRow> {
  String _deviceId   = '—';
  String _tenantName = '—';
  String _tenantId   = '—';

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final prefs = await SharedPreferences.getInstance();
    if (mounted) {
      setState(() {
        _deviceId   = prefs.getString('ics_device_id')   ?? '—';
        _tenantName = prefs.getString('ics_tenant_name') ?? '—';
        _tenantId   = prefs.getString('ics_tenant_id')   ?? '—';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final short = _deviceId.length > 18
        ? '${_deviceId.substring(0, 8)}…${_deviceId.substring(_deviceId.length - 6)}'
        : _deviceId;

    return Column(children: [
      _SettingsRow(
        icon: Icons.apartment_outlined,
        label: 'Community',
        value: _tenantName,
        isDark: widget.isDark,
      ),
      _SettingsRow(
        icon: Icons.fingerprint_outlined,
        label: 'Device ID',
        value: short,
        isDark: widget.isDark,
      ),
      _SettingsRow(
        icon: Icons.vpn_key_outlined,
        label: 'Tenant ID',
        value: _tenantId.length > 18
            ? '${_tenantId.substring(0, 8)}…'
            : _tenantId,
        isDark: widget.isDark,
      ),
    ]);
  }
}

// ── About row ─────────────────────────────────────────────────────────────────

class _AboutRow extends StatelessWidget {
  const _AboutRow({required this.isDark});
  final bool isDark;

  @override
  Widget build(BuildContext context) {
    return _SettingsRow(
      icon: Icons.info_outline,
      label: 'Version',
      value: 'Ichebo Desktop 1.0.0',
      isDark: isDark,
    );
  }
}

// ── Shared primitives ─────────────────────────────────────────────────────────

class _SectionHeader extends StatelessWidget {
  const _SectionHeader({required this.title, required this.isDark});
  final String title;
  final bool isDark;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(IcsSpacing.m, IcsSpacing.l, IcsSpacing.m, IcsSpacing.xs),
      child: Text(title.toUpperCase(),
          style: TextStyle(
            fontSize: 10,
            fontWeight: FontWeight.w700,
            letterSpacing: 0.8,
            color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted,
          )),
    );
  }
}

class _SettingsRow extends StatelessWidget {
  const _SettingsRow({
    required this.icon,
    required this.label,
    required this.isDark,
    this.value,
    this.trailing,
  });
  final IconData icon;
  final String label;
  final bool isDark;
  final String? value;
  final Widget? trailing;

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 48,
      padding: const EdgeInsets.symmetric(horizontal: IcsSpacing.m),
      child: Row(children: [
        Icon(icon, size: 16,
            color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted),
        const SizedBox(width: IcsSpacing.m),
        Expanded(child: Text(label,
            style: TextStyle(fontSize: 13,
                color: isDark ? Colors.white : IcsColors.inkBg))),
        if (trailing != null)
          trailing!
        else if (value != null)
          Text(value!,
              style: TextStyle(fontSize: 12,
                  color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted)),
      ]),
    );
  }
}

class _Divider extends StatelessWidget {
  const _Divider({required this.isDark});
  final bool isDark;

  @override
  Widget build(BuildContext context) => Divider(
      height: 1, color: isDark ? IcsColors.borderDark : IcsColors.borderLight);
}

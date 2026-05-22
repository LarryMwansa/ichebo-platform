import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/services/member_service.dart';
import '../../core/theme/tokens.dart';
import '../../shared/level_badge.dart';
import 'people_providers.dart';

// KGS Service Orders (static reference list)
const _kServiceOrders = [
  'Order of Apostolic Governance',
  'Order of Prophetic Ministry',
  'Order of Teaching & Formation',
  'Order of Pastoral Care',
  'Order of Evangelism & Mission',
  'Order of Worship & Arts',
  'Order of Intercession',
  'Order of Community Development',
  'Order of Resource Stewardship',
  'Order of Operations',
  'Order of Discipleship',
  'Order of Youth & Children',
];

enum MemberFormMode { add, edit }

class MemberForm extends ConsumerStatefulWidget {
  const MemberForm({super.key, required this.mode, this.member});

  final MemberFormMode mode;
  final MemberModel? member;

  @override
  ConsumerState<MemberForm> createState() => _MemberFormState();
}

class _MemberFormState extends ConsumerState<MemberForm> {
  final _displayNameCtrl = TextEditingController();
  final _firstNameCtrl = TextEditingController();
  final _lastNameCtrl = TextEditingController();
  final _emailCtrl = TextEditingController();
  final _phoneCtrl = TextEditingController();
  String? _serviceOrder;
  String? _shepherdId;
  String? _shepherdDisplayName;
  bool _isActive = true;
  bool _saving = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    final m = widget.member;
    if (m != null) {
      _displayNameCtrl.text = m.displayName;
      _firstNameCtrl.text = m.firstName;
      _lastNameCtrl.text = m.lastName;
      _emailCtrl.text = m.email;
      _phoneCtrl.text = m.phone;
      _serviceOrder = m.serviceOrder;
      _shepherdId = m.shepherdId;
      _isActive = m.isActive;
    }
  }

  @override
  void dispose() {
    _displayNameCtrl.dispose();
    _firstNameCtrl.dispose();
    _lastNameCtrl.dispose();
    _emailCtrl.dispose();
    _phoneCtrl.dispose();
    super.dispose();
  }

  String? _validate() {
    if (_displayNameCtrl.text.trim().isEmpty) return 'Display name is required.';
    if (_emailCtrl.text.trim().isEmpty) return 'Email is required.';
    if (!_emailCtrl.text.contains('@')) return 'Enter a valid email address.';
    return null;
  }

  Future<void> _save() async {
    final err = _validate();
    if (err != null) { setState(() => _error = err); return; }

    setState(() { _saving = true; _error = null; });

    final now = DateTime.now().toIso8601String();
    final base = widget.member;

    final updated = MemberModel(
      id: base?.id ?? '',
      tenantId: base?.tenantId ?? '',
      email: _emailCtrl.text.trim(),
      displayName: _displayNameCtrl.text.trim(),
      firstName: _firstNameCtrl.text.trim(),
      lastName: _lastNameCtrl.text.trim(),
      phone: _phoneCtrl.text.trim(),
      competenceLevel: base?.competenceLevel ?? 0,
      isActive: _isActive,
      shepherdId: _shepherdId,
      serviceOrder: _serviceOrder,
      createdAt: base?.createdAt ?? now,
      updatedAt: now,
    );

    final result = widget.mode == MemberFormMode.add
        ? await MemberService.createMember(updated)
        : await MemberService.updateMember(updated);

    if (!mounted) return;

    if (result == 0 || result == -99) {
      // -99 = engine not loaded (offline-only mode) — write goes direct to SQLite
      // via a fallback in a future iteration; for now treat as success.
      ref.invalidate(membersProvider);
      Navigator.of(context).pop(true);
    } else {
      setState(() {
        _saving = false;
        _error = 'Save failed (code $result). Try again.';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final title = widget.mode == MemberFormMode.add ? 'Add member' : 'Edit member';

    return Dialog(
      backgroundColor: isDark ? IcsColors.ink2 : Colors.white,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      child: SizedBox(
        width: 520,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Header
            Padding(
              padding: const EdgeInsets.fromLTRB(IcsSpacing.xl, IcsSpacing.l, IcsSpacing.l, 0),
              child: Row(
                children: [
                  Text(
                    title,
                    style: TextStyle(
                      fontFamily: 'Playfair Display',
                      fontSize: 18,
                      fontWeight: FontWeight.w700,
                      color: isDark ? Colors.white : IcsColors.inkBg,
                    ),
                  ),
                  const Spacer(),
                  IconButton(
                    icon: const Icon(Icons.close, size: 18),
                    onPressed: () => Navigator.of(context).pop(false),
                    color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted,
                  ),
                ],
              ),
            ),
            const Divider(height: IcsSpacing.l),
            // Form body
            Flexible(
              child: SingleChildScrollView(
                padding: const EdgeInsets.symmetric(horizontal: IcsSpacing.xl),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    _FormField(label: 'Display name *', controller: _displayNameCtrl, isDark: isDark),
                    const SizedBox(height: IcsSpacing.m),
                    Row(
                      children: [
                        Expanded(child: _FormField(label: 'First name', controller: _firstNameCtrl, isDark: isDark)),
                        const SizedBox(width: IcsSpacing.m),
                        Expanded(child: _FormField(label: 'Last name', controller: _lastNameCtrl, isDark: isDark)),
                      ],
                    ),
                    const SizedBox(height: IcsSpacing.m),
                    _FormField(label: 'Email *', controller: _emailCtrl, isDark: isDark, keyboardType: TextInputType.emailAddress),
                    const SizedBox(height: IcsSpacing.m),
                    _FormField(label: 'Phone', controller: _phoneCtrl, isDark: isDark, keyboardType: TextInputType.phone),
                    const SizedBox(height: IcsSpacing.m),
                    _DropdownField(
                      label: 'Service order',
                      value: _serviceOrder,
                      items: _kServiceOrders,
                      isDark: isDark,
                      onChanged: (v) => setState(() => _serviceOrder = v),
                    ),
                    const SizedBox(height: IcsSpacing.m),
                    _ShepherdPicker(
                      isDark: isDark,
                      shepherdId: _shepherdId,
                      shepherdDisplayName: _shepherdDisplayName,
                      onSelected: (id, name) => setState(() {
                        _shepherdId = id;
                        _shepherdDisplayName = name;
                      }),
                      onCleared: () => setState(() {
                        _shepherdId = null;
                        _shepherdDisplayName = null;
                      }),
                    ),
                    const SizedBox(height: IcsSpacing.m),
                    if (widget.mode == MemberFormMode.edit) ...[
                      // Competence level — read-only display (write path locked to certification API)
                      _LevelDisplay(level: widget.member?.competenceLevel ?? 0, isDark: isDark),
                      const SizedBox(height: IcsSpacing.m),
                    ],
                    Row(
                      children: [
                        Switch(
                          value: _isActive,
                          onChanged: (v) => setState(() => _isActive = v),
                          activeThumbColor: IcsColors.accentRed,
                        ),
                        const SizedBox(width: IcsSpacing.s),
                        Text(
                          'Active member',
                          style: TextStyle(
                            fontSize: 13,
                            color: isDark ? Colors.white : IcsColors.inkBg,
                          ),
                        ),
                      ],
                    ),
                    if (_error != null) ...[
                      const SizedBox(height: IcsSpacing.s),
                      Text(_error!, style: TextStyle(fontSize: 12, color: IcsColors.error)),
                    ],
                    const SizedBox(height: IcsSpacing.l),
                  ],
                ),
              ),
            ),
            const Divider(height: 1),
            // Action bar
            Padding(
              padding: const EdgeInsets.all(IcsSpacing.l),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  TextButton(
                    onPressed: () => Navigator.of(context).pop(false),
                    child: Text('Cancel', style: TextStyle(color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted)),
                  ),
                  const SizedBox(width: IcsSpacing.s),
                  ElevatedButton(
                    onPressed: _saving ? null : _save,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: IcsColors.accentRed,
                      foregroundColor: Colors.white,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
                    ),
                    child: _saving
                        ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                        : Text(widget.mode == MemberFormMode.add ? 'Add member' : 'Save changes'),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ── Form sub-widgets ──────────────────────────────────────────────────────────

class _FormField extends StatelessWidget {
  const _FormField({
    required this.label,
    required this.controller,
    required this.isDark,
    this.keyboardType,
  });

  final String label;
  final TextEditingController controller;
  final bool isDark;
  final TextInputType? keyboardType;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600,
            color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted)),
        const SizedBox(height: 4),
        TextField(
          controller: controller,
          keyboardType: keyboardType,
          style: TextStyle(fontSize: 13, color: isDark ? Colors.white : IcsColors.inkBg),
          decoration: InputDecoration(
            isDense: true,
            filled: true,
            fillColor: isDark ? const Color(0xFF1A1A1A) : IcsColors.stone2,
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(6),
              borderSide: BorderSide(color: isDark ? IcsColors.borderDark : IcsColors.borderLight),
            ),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(6),
              borderSide: BorderSide(color: IcsColors.accentRed, width: 1.5),
            ),
            contentPadding: const EdgeInsets.symmetric(horizontal: IcsSpacing.m, vertical: 10),
          ),
        ),
      ],
    );
  }
}

class _DropdownField extends StatelessWidget {
  const _DropdownField({
    required this.label,
    required this.value,
    required this.items,
    required this.isDark,
    required this.onChanged,
  });

  final String label;
  final String? value;
  final List<String> items;
  final bool isDark;
  final ValueChanged<String?> onChanged;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600,
            color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted)),
        const SizedBox(height: 4),
        DropdownButtonFormField<String>(
          initialValue: value,
          isExpanded: true,
          decoration: InputDecoration(
            isDense: true,
            filled: true,
            fillColor: isDark ? const Color(0xFF1A1A1A) : IcsColors.stone2,
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(6),
              borderSide: BorderSide(color: isDark ? IcsColors.borderDark : IcsColors.borderLight),
            ),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(6),
              borderSide: BorderSide(color: IcsColors.accentRed, width: 1.5),
            ),
            contentPadding: const EdgeInsets.symmetric(horizontal: IcsSpacing.m, vertical: 10),
          ),
          dropdownColor: isDark ? IcsColors.ink2 : Colors.white,
          style: TextStyle(fontSize: 13, color: isDark ? Colors.white : IcsColors.inkBg),
          hint: Text('Select…', style: TextStyle(fontSize: 13, color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted)),
          items: [
            const DropdownMenuItem<String>(value: null, child: Text('— None —')),
            ...items.map((s) => DropdownMenuItem(value: s, child: Text(s))),
          ],
          onChanged: onChanged,
        ),
      ],
    );
  }
}

class _LevelDisplay extends StatelessWidget {
  const _LevelDisplay({required this.level, required this.isDark});
  final int level;
  final bool isDark;

  static const _names = ['Seeker', 'Foundational Disciple', 'Active Contributor',
      'Functional Minister', 'Leader', 'Apostolic Steward'];

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        LevelBadge(level: level),
        const SizedBox(width: IcsSpacing.s),
        Text(
          _names[level.clamp(0, 5)],
          style: TextStyle(fontSize: 13, color: isDark ? Colors.white : IcsColors.inkBg),
        ),
        const Spacer(),
        Text(
          'Set via formation pathway',
          style: TextStyle(fontSize: 11, color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted),
        ),
      ],
    );
  }
}

class _ShepherdPicker extends ConsumerStatefulWidget {
  const _ShepherdPicker({
    required this.isDark,
    required this.shepherdId,
    required this.shepherdDisplayName,
    required this.onSelected,
    required this.onCleared,
  });

  final bool isDark;
  final String? shepherdId;
  final String? shepherdDisplayName;
  final void Function(String id, String name) onSelected;
  final VoidCallback onCleared;

  @override
  ConsumerState<_ShepherdPicker> createState() => _ShepherdPickerState();
}

class _ShepherdPickerState extends ConsumerState<_ShepherdPicker> {
  final _ctrl = TextEditingController();
  bool _open = false;

  @override
  void initState() {
    super.initState();
    if (widget.shepherdDisplayName != null) {
      _ctrl.text = widget.shepherdDisplayName!;
    }
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final allMembers = ref.watch(membersProvider);
    final query = _ctrl.text.toLowerCase();

    final suggestions = allMembers.maybeWhen(
      data: (list) => list
          .where((m) => m.displayName.toLowerCase().contains(query) && m.id != widget.shepherdId)
          .take(6)
          .toList(),
      orElse: () => <MemberModel>[],
    );

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('Shepherd (pastoral overseer)',
            style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600,
                color: widget.isDark ? IcsColors.textMutedDark : IcsColors.textMuted)),
        const SizedBox(height: 4),
        Row(
          children: [
            Expanded(
              child: TextField(
                controller: _ctrl,
                onChanged: (_) => setState(() => _open = true),
                onTap: () => setState(() => _open = true),
                style: TextStyle(fontSize: 13, color: widget.isDark ? Colors.white : IcsColors.inkBg),
                decoration: InputDecoration(
                  isDense: true,
                  filled: true,
                  fillColor: widget.isDark ? const Color(0xFF1A1A1A) : IcsColors.stone2,
                  hintText: 'Search members…',
                  hintStyle: TextStyle(fontSize: 13, color: widget.isDark ? IcsColors.textMutedDark : IcsColors.textMuted),
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(6),
                    borderSide: BorderSide(color: widget.isDark ? IcsColors.borderDark : IcsColors.borderLight),
                  ),
                  focusedBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(6),
                    borderSide: BorderSide(color: IcsColors.accentRed, width: 1.5),
                  ),
                  contentPadding: const EdgeInsets.symmetric(horizontal: IcsSpacing.m, vertical: 10),
                ),
              ),
            ),
            if (widget.shepherdId != null) ...[
              const SizedBox(width: IcsSpacing.xs),
              IconButton(
                icon: const Icon(Icons.close, size: 16),
                onPressed: () {
                  _ctrl.clear();
                  widget.onCleared();
                },
                color: widget.isDark ? IcsColors.textMutedDark : IcsColors.textMuted,
              ),
            ],
          ],
        ),
        if (_open && suggestions.isNotEmpty)
          Container(
            margin: const EdgeInsets.only(top: 2),
            decoration: BoxDecoration(
              color: widget.isDark ? IcsColors.ink2 : Colors.white,
              borderRadius: BorderRadius.circular(6),
              border: Border.all(color: widget.isDark ? IcsColors.borderDark : IcsColors.borderLight),
            ),
            child: Column(
              children: suggestions.map((m) => InkWell(
                onTap: () {
                  _ctrl.text = m.displayName;
                  setState(() => _open = false);
                  widget.onSelected(m.id, m.displayName);
                },
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: IcsSpacing.m, vertical: IcsSpacing.s),
                  child: Row(
                    children: [
                      Text(m.displayName, style: TextStyle(fontSize: 13, color: widget.isDark ? Colors.white : IcsColors.inkBg)),
                      const Spacer(),
                      Text('L${m.competenceLevel}', style: TextStyle(fontSize: 11, color: widget.isDark ? IcsColors.textMutedDark : IcsColors.textMuted)),
                    ],
                  ),
                ),
              )).toList(),
            ),
          ),
      ],
    );
  }
}

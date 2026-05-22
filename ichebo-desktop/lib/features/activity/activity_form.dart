import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../../core/services/activity_service.dart';
import '../../core/theme/tokens.dart';
import '../../features/people/people_providers.dart';
import '../../shared/activity_type_badge.dart';
import 'activity_providers.dart';

enum ActivityFormMode { add, edit }

const _kActivityTypes = [
  'gathering', 'event', 'task', 'campaign', 'goal', 'habit', 'project', 'reminder',
];

const _kGatheringFormats = ['in_person', 'digital', 'hybrid'];
const _kFormatLabels = {'in_person': 'In person', 'digital': 'Digital', 'hybrid': 'Hybrid'};

class ActivityForm extends ConsumerStatefulWidget {
  const ActivityForm({super.key, required this.mode, this.activity, this.initialType});

  final ActivityFormMode mode;
  final ActivityModel? activity;
  final String? initialType; // pre-select type when opened from + button context

  @override
  ConsumerState<ActivityForm> createState() => _ActivityFormState();
}

class _ActivityFormState extends ConsumerState<ActivityForm> {
  final _titleCtrl       = TextEditingController();
  final _descCtrl        = TextEditingController();
  final _locationCtrl    = TextEditingController();
  final _durationCtrl    = TextEditingController();

  String _type = 'task';
  String _status = 'pending';
  String _format = 'in_person';
  DateTime? _scheduledAt;
  DateTime? _dueAt;
  String? _assignedTo;
  String? _assignedName;
  bool _saving = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    final a = widget.activity;
    if (a != null) {
      _titleCtrl.text = a.title;
      _descCtrl.text = a.description;
      _type = a.activityType;
      _status = a.status;
      _assignedTo = a.assignedTo;
      if (a.scheduledAt != null && a.scheduledAt!.isNotEmpty) {
        _scheduledAt = DateTime.tryParse(a.scheduledAt!);
      }
      if (a.dueAt != null && a.dueAt!.isNotEmpty) {
        _dueAt = DateTime.tryParse(a.dueAt!);
      }
      final meta = a.metadataMap;
      if (meta['format'] != null) _format = meta['format'] as String;
      if (meta['location'] != null) _locationCtrl.text = meta['location'] as String;
      if (meta['duration_minutes'] != null) {
        _durationCtrl.text = meta['duration_minutes'].toString();
      }
    } else {
      _type = widget.initialType ?? 'task';
    }
  }

  @override
  void dispose() {
    _titleCtrl.dispose();
    _descCtrl.dispose();
    _locationCtrl.dispose();
    _durationCtrl.dispose();
    super.dispose();
  }

  String? _validate() {
    if (_titleCtrl.text.trim().isEmpty) return 'Title is required.';
    if (_type == 'gathering' && _scheduledAt == null) return 'Scheduled date is required for a gathering.';
    return null;
  }

  Future<void> _save() async {
    final err = _validate();
    if (err != null) {
      setState(() => _error = err);
      return;
    }
    setState(() { _saving = true; _error = null; });

    final prefs = await SharedPreferences.getInstance();
    final tenantId = prefs.getString('ics_tenant_id') ?? '';
    final createdBy = prefs.getString('ics_admin_email') ?? 'device';

    int result;

    if (_type == 'gathering' && widget.mode == ActivityFormMode.add) {
      result = await ActivityService.createGathering(
        title: _titleCtrl.text.trim(),
        scheduledAt: _scheduledAt!.toIso8601String(),
        format: _format,
        location: _locationCtrl.text.trim(),
        durationMinutes: int.tryParse(_durationCtrl.text) ?? 0,
        tenantId: tenantId,
        createdBy: createdBy,
      );
    } else {
      final meta = jsonEncode({
        if (_type == 'gathering') ...{
          'format': _format,
          'location': _locationCtrl.text.trim(),
          'duration_minutes': int.tryParse(_durationCtrl.text) ?? 0,
        },
        'source_app': 'community',
      });

      final base = widget.activity;
      final model = ActivityModel(
        id: base?.id ?? '',
        tenantId: base?.tenantId ?? tenantId,
        activityType: _type,
        title: _titleCtrl.text.trim(),
        description: _descCtrl.text.trim(),
        status: _status,
        progress: base?.progress ?? 0,
        assignedTo: _assignedTo,
        linkedRecordId: base?.linkedRecordId,
        scheduledAt: _scheduledAt?.toIso8601String(),
        dueAt: _dueAt?.toIso8601String(),
        completedAt: _status == 'completed' ? DateTime.now().toIso8601String() : base?.completedAt,
        metadata: meta,
        createdBy: base?.createdBy ?? createdBy,
        createdAt: base?.createdAt ?? DateTime.now().toIso8601String(),
        updatedAt: DateTime.now().toIso8601String(),
      );

      result = widget.mode == ActivityFormMode.add
          ? await ActivityService.createActivity(model)
          : await ActivityService.updateActivity(model);
    }

    if (!mounted) return;

    if (result == 0 || result == -99) {
      ref.invalidate(activitiesProvider);
      Navigator.of(context).pop(true);
    } else {
      setState(() {
        _saving = false;
        _error = 'Save failed (code $result). Try again.';
      });
    }
  }

  Future<void> _pickDate(bool isScheduled) async {
    final initial = isScheduled ? (_scheduledAt ?? DateTime.now()) : (_dueAt ?? DateTime.now());
    final picked = await showDatePicker(
      context: context,
      initialDate: initial,
      firstDate: DateTime(2020),
      lastDate: DateTime(2035),
    );
    if (picked == null || !mounted) return;
    final time = await showTimePicker(context: context, initialTime: TimeOfDay.fromDateTime(initial));
    if (!mounted) return;
    final dt = time != null
        ? DateTime(picked.year, picked.month, picked.day, time.hour, time.minute)
        : picked;
    setState(() { if (isScheduled) { _scheduledAt = dt; } else { _dueAt = dt; } });
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final isGathering = _type == 'gathering';
    final title = widget.mode == ActivityFormMode.add ? 'New activity' : 'Edit activity';

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
                  Text(title, style: TextStyle(
                    fontFamily: 'Playfair Display', fontSize: 18, fontWeight: FontWeight.w700,
                    color: isDark ? Colors.white : IcsColors.inkBg,
                  )),
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
            Flexible(
              child: SingleChildScrollView(
                padding: const EdgeInsets.symmetric(horizontal: IcsSpacing.xl),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    // Type selector (only for add mode)
                    if (widget.mode == ActivityFormMode.add) ...[
                      _Label('Type', isDark),
                      const SizedBox(height: 4),
                      Wrap(
                        spacing: IcsSpacing.xs,
                        runSpacing: IcsSpacing.xs,
                        children: _kActivityTypes.map((t) => GestureDetector(
                          onTap: () => setState(() => _type = t),
                          child: Container(
                            decoration: BoxDecoration(
                              borderRadius: BorderRadius.circular(16),
                              border: Border.all(
                                color: _type == t ? _typeColor(t) : (isDark ? IcsColors.borderDark : IcsColors.borderLight),
                                width: _type == t ? 2 : 1,
                              ),
                            ),
                            child: Padding(
                              padding: const EdgeInsets.all(2),
                              child: ActivityTypeBadge(type: t, large: true),
                            ),
                          ),
                        )).toList(),
                      ),
                      const SizedBox(height: IcsSpacing.m),
                    ],
                    // Title
                    _FormTextField(label: 'Title *', controller: _titleCtrl, isDark: isDark),
                    const SizedBox(height: IcsSpacing.m),
                    // Gathering-specific fields
                    if (isGathering) ...[
                      _Label('Format', isDark),
                      const SizedBox(height: 4),
                      Row(
                        children: _kGatheringFormats.map((f) {
                          final selected = _format == f;
                          return Padding(
                            padding: const EdgeInsets.only(right: IcsSpacing.s),
                            child: GestureDetector(
                              onTap: () => setState(() => _format = f),
                              child: Container(
                                padding: const EdgeInsets.symmetric(horizontal: IcsSpacing.m, vertical: 7),
                                decoration: BoxDecoration(
                                  color: selected ? IcsColors.accentRed : Colors.transparent,
                                  borderRadius: BorderRadius.circular(6),
                                  border: Border.all(
                                    color: selected ? IcsColors.accentRed : (isDark ? IcsColors.borderDark : IcsColors.borderLight),
                                  ),
                                ),
                                child: Text(
                                  _kFormatLabels[f] ?? f,
                                  style: TextStyle(
                                    fontSize: 12,
                                    fontWeight: FontWeight.w600,
                                    color: selected ? Colors.white : (isDark ? IcsColors.textMutedDark : IcsColors.textMuted),
                                  ),
                                ),
                              ),
                            ),
                          );
                        }).toList(),
                      ),
                      const SizedBox(height: IcsSpacing.m),
                      _FormTextField(label: 'Location', controller: _locationCtrl, isDark: isDark),
                      const SizedBox(height: IcsSpacing.m),
                      _FormTextField(
                        label: 'Duration (minutes)',
                        controller: _durationCtrl,
                        isDark: isDark,
                        keyboardType: TextInputType.number,
                        inputFormatters: [FilteringTextInputFormatter.digitsOnly],
                      ),
                      const SizedBox(height: IcsSpacing.m),
                    ] else ...[
                      // Description (non-gathering)
                      _FormTextField(
                        label: 'Description',
                        controller: _descCtrl,
                        isDark: isDark,
                        maxLines: 3,
                      ),
                      const SizedBox(height: IcsSpacing.m),
                    ],
                    // Scheduled at
                    _DateField(
                      label: isGathering ? 'Date & time *' : 'Scheduled at',
                      value: _scheduledAt,
                      isDark: isDark,
                      onTap: () => _pickDate(true),
                      onClear: () => setState(() => _scheduledAt = null),
                    ),
                    if (!isGathering) ...[
                      const SizedBox(height: IcsSpacing.m),
                      _DateField(
                        label: 'Due at',
                        value: _dueAt,
                        isDark: isDark,
                        onTap: () => _pickDate(false),
                        onClear: () => setState(() => _dueAt = null),
                      ),
                    ],
                    const SizedBox(height: IcsSpacing.m),
                    // Assigned to
                    _AssignedToPicker(
                      isDark: isDark,
                      assignedTo: _assignedTo,
                      assignedName: _assignedName,
                      onSelected: (id, name) => setState(() { _assignedTo = id; _assignedName = name; }),
                      onCleared: () => setState(() { _assignedTo = null; _assignedName = null; }),
                    ),
                    if (widget.mode == ActivityFormMode.edit) ...[
                      const SizedBox(height: IcsSpacing.m),
                      _Label('Status', isDark),
                      const SizedBox(height: 4),
                      DropdownButtonFormField<String>(
                        initialValue: _status,
                        decoration: _dropdownDecor(isDark),
                        dropdownColor: isDark ? IcsColors.ink2 : Colors.white,
                        style: TextStyle(fontSize: 13, color: isDark ? Colors.white : IcsColors.inkBg),
                        items: ['pending','in_progress','completed','cancelled','deferred']
                            .map((s) => DropdownMenuItem(value: s, child: Text(s)))
                            .toList(),
                        onChanged: (v) => setState(() => _status = v!),
                      ),
                    ],
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
                      backgroundColor: IcsColors.accentRed, foregroundColor: Colors.white,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
                    ),
                    child: _saving
                        ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                        : Text(widget.mode == ActivityFormMode.add ? 'Create' : 'Save changes'),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Color _typeColor(String t) => switch (t) {
    'gathering' => const Color(0xFFAF3236),
    'event'     => const Color(0xFF2196F3),
    'task'      => const Color(0xFFFF9800),
    'campaign'  => const Color(0xFF9C27B0),
    'goal'      => const Color(0xFF10B981),
    'habit'     => const Color(0xFF00BCD4),
    _           => const Color(0xFF9E9E9E),
  };

  InputDecoration _dropdownDecor(bool isDark) => InputDecoration(
    isDense: true,
    filled: true,
    fillColor: isDark ? const Color(0xFF1A1A1A) : IcsColors.stone2,
    border: OutlineInputBorder(borderRadius: BorderRadius.circular(6),
        borderSide: BorderSide(color: isDark ? IcsColors.borderDark : IcsColors.borderLight)),
    focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(6),
        borderSide: const BorderSide(color: IcsColors.accentRed, width: 1.5)),
    contentPadding: const EdgeInsets.symmetric(horizontal: IcsSpacing.m, vertical: 10),
  );
}

// ── Sub-widgets ───────────────────────────────────────────────────────────────

class _Label extends StatelessWidget {
  const _Label(this.text, this.isDark);
  final String text;
  final bool isDark;

  @override
  Widget build(BuildContext context) => Text(
        text,
        style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600,
            color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted),
      );
}

class _FormTextField extends StatelessWidget {
  const _FormTextField({
    required this.label,
    required this.controller,
    required this.isDark,
    this.keyboardType,
    this.inputFormatters,
    this.maxLines = 1,
  });

  final String label;
  final TextEditingController controller;
  final bool isDark;
  final TextInputType? keyboardType;
  final List<TextInputFormatter>? inputFormatters;
  final int maxLines;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _Label(label, isDark),
        const SizedBox(height: 4),
        TextField(
          controller: controller,
          keyboardType: keyboardType,
          inputFormatters: inputFormatters,
          maxLines: maxLines,
          style: TextStyle(fontSize: 13, color: isDark ? Colors.white : IcsColors.inkBg),
          decoration: InputDecoration(
            isDense: true,
            filled: true,
            fillColor: isDark ? const Color(0xFF1A1A1A) : IcsColors.stone2,
            border: OutlineInputBorder(borderRadius: BorderRadius.circular(6),
                borderSide: BorderSide(color: isDark ? IcsColors.borderDark : IcsColors.borderLight)),
            focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(6),
                borderSide: const BorderSide(color: IcsColors.accentRed, width: 1.5)),
            contentPadding: const EdgeInsets.symmetric(horizontal: IcsSpacing.m, vertical: 10),
          ),
        ),
      ],
    );
  }
}

class _DateField extends StatelessWidget {
  const _DateField({
    required this.label,
    required this.value,
    required this.isDark,
    required this.onTap,
    required this.onClear,
  });

  final String label;
  final DateTime? value;
  final bool isDark;
  final VoidCallback onTap;
  final VoidCallback onClear;

  String _fmt(DateTime dt) {
    final months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
    final h = dt.hour.toString().padLeft(2, '0');
    final m = dt.minute.toString().padLeft(2, '0');
    return '${dt.day} ${months[dt.month - 1]} ${dt.year}  $h:$m';
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _Label(label, isDark),
        const SizedBox(height: 4),
        GestureDetector(
          onTap: onTap,
          child: Container(
            height: 40,
            padding: const EdgeInsets.symmetric(horizontal: IcsSpacing.m),
            decoration: BoxDecoration(
              color: isDark ? const Color(0xFF1A1A1A) : IcsColors.stone2,
              borderRadius: BorderRadius.circular(6),
              border: Border.all(color: isDark ? IcsColors.borderDark : IcsColors.borderLight),
            ),
            child: Row(
              children: [
                Icon(Icons.calendar_today_outlined, size: 14,
                    color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted),
                const SizedBox(width: IcsSpacing.s),
                Expanded(
                  child: Text(
                    value != null ? _fmt(value!) : 'Select date & time…',
                    style: TextStyle(fontSize: 13,
                        color: value != null
                            ? (isDark ? Colors.white : IcsColors.inkBg)
                            : (isDark ? IcsColors.textMutedDark : IcsColors.textMuted)),
                  ),
                ),
                if (value != null)
                  GestureDetector(
                    onTap: onClear,
                    child: Icon(Icons.close, size: 14,
                        color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted),
                  ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}

class _AssignedToPicker extends ConsumerStatefulWidget {
  const _AssignedToPicker({
    required this.isDark,
    required this.assignedTo,
    required this.assignedName,
    required this.onSelected,
    required this.onCleared,
  });

  final bool isDark;
  final String? assignedTo;
  final String? assignedName;
  final void Function(String id, String name) onSelected;
  final VoidCallback onCleared;

  @override
  ConsumerState<_AssignedToPicker> createState() => _AssignedToPickerState();
}

class _AssignedToPickerState extends ConsumerState<_AssignedToPicker> {
  final _ctrl = TextEditingController();
  bool _open = false;

  @override
  void initState() {
    super.initState();
    if (widget.assignedName != null) _ctrl.text = widget.assignedName!;
  }

  @override
  void dispose() { _ctrl.dispose(); super.dispose(); }

  @override
  Widget build(BuildContext context) {
    final allMembers = ref.watch(membersProvider);
    final query = _ctrl.text.toLowerCase();
    final suggestions = allMembers.maybeWhen(
      data: (list) => list.where((m) => m.displayName.toLowerCase().contains(query)).take(6).toList(),
      orElse: () => [],
    );

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _Label('Assigned to', widget.isDark),
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
                  isDense: true, hintText: 'Search members…',
                  hintStyle: TextStyle(fontSize: 13, color: widget.isDark ? IcsColors.textMutedDark : IcsColors.textMuted),
                  filled: true, fillColor: widget.isDark ? const Color(0xFF1A1A1A) : IcsColors.stone2,
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(6),
                      borderSide: BorderSide(color: widget.isDark ? IcsColors.borderDark : IcsColors.borderLight)),
                  focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(6),
                      borderSide: const BorderSide(color: IcsColors.accentRed, width: 1.5)),
                  contentPadding: const EdgeInsets.symmetric(horizontal: IcsSpacing.m, vertical: 10),
                ),
              ),
            ),
            if (widget.assignedTo != null)
              IconButton(
                icon: const Icon(Icons.close, size: 16),
                onPressed: () { _ctrl.clear(); widget.onCleared(); },
                color: widget.isDark ? IcsColors.textMutedDark : IcsColors.textMuted,
              ),
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
                onTap: () { _ctrl.text = m.displayName; setState(() => _open = false); widget.onSelected(m.id, m.displayName); },
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: IcsSpacing.m, vertical: IcsSpacing.s),
                  child: Row(children: [
                    Text(m.displayName, style: TextStyle(fontSize: 13, color: widget.isDark ? Colors.white : IcsColors.inkBg)),
                    const Spacer(),
                    Text('L${m.competenceLevel}', style: TextStyle(fontSize: 11, color: widget.isDark ? IcsColors.textMutedDark : IcsColors.textMuted)),
                  ]),
                ),
              )).toList(),
            ),
          ),
      ],
    );
  }
}

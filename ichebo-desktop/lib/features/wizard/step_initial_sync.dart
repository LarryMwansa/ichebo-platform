import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';
import '../../core/config.dart';
import '../../core/theme/tokens.dart';
import 'wizard_state.dart';

class StepInitialSync extends ConsumerStatefulWidget {
  const StepInitialSync({super.key});

  @override
  ConsumerState<StepInitialSync> createState() => _StepInitialSyncState();
}

class _StepInitialSyncState extends ConsumerState<StepInitialSync> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _runSync());
  }

  Future<void> _runSync() async {
    final prefs = await SharedPreferences.getInstance();
    final tenantId = prefs.getString('ics_tenant_id') ?? '';
    final deviceId = prefs.getString('ics_device_id') ?? '';
    final token = prefs.getString('ics_auth_token') ?? '';

    ref.read(wizardProvider.notifier).updateSyncProgress(progress: 0.05);

    try {
      final uri = Uri.parse(
        '${AppConfig.syncPullUrl}?since=1970-01-01T00:00:00Z'
        '&device_id=$deviceId&tenant_id=$tenantId',
      );
      final response = await http.get(
        uri,
        headers: {'Authorization': 'Bearer $token'},
      ).timeout(const Duration(seconds: 60));

      if (response.statusCode != 200) {
        ref.read(wizardProvider.notifier).setError(
          'Sync failed (${response.statusCode}). You can retry after activation.',
        );
        await _markDone();
        return;
      }

      ref.read(wizardProvider.notifier).updateSyncProgress(progress: 0.3);

      final data = jsonDecode(response.body) as Map<String, dynamic>;
      final members = (data['members'] as List<dynamic>?) ?? [];
      final activities = (data['activities'] as List<dynamic>?) ?? [];
      final records = (data['records'] as List<dynamic>?) ?? [];

      await _writeToSqlite(prefs, members, activities, records);

      ref.read(wizardProvider.notifier).updateSyncProgress(
        progress: 1.0,
        members: members.length,
        activities: activities.length,
        records: records.length,
      );

      await Future<void>.delayed(const Duration(milliseconds: 800));
      await _markDone();
    } catch (e) {
      // Network unavailable — mark done anyway so app is usable offline.
      ref.read(wizardProvider.notifier).updateSyncProgress(progress: 1.0);
      await Future<void>.delayed(const Duration(milliseconds: 400));
      await _markDone();
    }
  }

  Future<void> _writeToSqlite(
    SharedPreferences prefs,
    List<dynamic> members,
    List<dynamic> activities,
    List<dynamic> records,
  ) async {
    final dbPath = await databaseFactory.getDatabasesPath();
    final db = await databaseFactory.openDatabase('$dbPath/ichebo.db');

    final now = DateTime.now().toIso8601String();
    final tenantId = prefs.getString('ics_tenant_id') ?? '';

    final batch = db.batch();
    int written = 0;

    for (final raw in members) {
      final m = raw as Map<String, dynamic>;
      batch.insert(
        'members',
        {
          'id': m['id'],
          'tenant_id': tenantId,
          'email': m['email'] ?? '',
          'display_name': m['display_name'] ?? '',
          'first_name': m['first_name'] ?? '',
          'last_name': m['last_name'] ?? '',
          'phone': m['phone'] ?? '',
          'avatar_url': '',
          'competence_level': m['competence_level'] ?? 0,
          'is_active': (m['is_active'] == true) ? 1 : 0,
          'shepherd_id': null,
          'service_order': null,
          'custom_fields': '{}',
          'created_by': m['id'] ?? '',
          'created_at': m['created_at'] ?? now,
          'updated_at': m['updated_at'] ?? now,
          'deleted_at': m['deleted_at'],
        },
        conflictAlgorithm: ConflictAlgorithm.replace,
      );
      written++;
      if (written % 50 == 0) {
        ref.read(wizardProvider.notifier).updateSyncProgress(
          progress: 0.3 + (written / members.length) * 0.4,
          members: written,
        );
      }
    }

    for (final raw in activities) {
      final a = raw as Map<String, dynamic>;
      // assigned_to may be a UUID string or a nested user object from the API
      final assignedTo = a['assigned_to'] is Map
          ? (a['assigned_to'] as Map)['id'] as String?
          : a['assigned_to'] as String?;
      final linkedRecord = a['linked_record'] is Map
          ? (a['linked_record'] as Map)['id'] as String?
          : a['linked_record'] as String?;
      batch.insert(
        'activities',
        {
          'id': a['id'],
          'tenant_id': tenantId,
          'activity_type': a['activity_type'] ?? 'task',
          'title': a['title'] ?? '',
          'description': a['description'] ?? '',
          'status': a['status'] ?? 'pending',
          'progress': a['progress'] ?? 0,
          'assigned_to': assignedTo,
          'linked_record_id': linkedRecord,
          'scheduled_at': a['scheduled_at'],
          'due_at': a['due_at'],
          'completed_at': a['completed_at'],
          'source_app': '',
          'custom_fields': jsonEncode(a['custom_fields'] ?? {}),
          'metadata': jsonEncode(a['metadata'] ?? {}),
          'created_by': a['created_by'] ?? '',
          'created_at': a['created_at'] ?? now,
          'updated_at': a['updated_at'] ?? now,
          'deleted_at': a['deleted_at'],
        },
        conflictAlgorithm: ConflictAlgorithm.replace,
      );
    }

    for (final raw in records) {
      final r = raw as Map<String, dynamic>;
      // API uses 'content' for body text; merge into metadata for Flutter queries
      final meta = Map<String, dynamic>.from(r['metadata'] as Map? ?? {});
      if (r['content'] != null) meta['body'] = r['content'];
      batch.insert(
        'records',
        {
          'id': r['id'],
          'tenant_id': tenantId,
          'record_class': r['record_class'] ?? 'organizational',
          'record_family': r['record_family'] ?? '',
          'record_type': r['record_type'] ?? '',
          'title': r['title'] ?? '',
          'status': r['status'] ?? 'active',
          'custom_fields': jsonEncode(r['custom_fields'] ?? {}),
          'metadata': jsonEncode(meta),
          'permissions': jsonEncode(r['permissions_data'] ?? {}),
          'created_by': r['created_by'] ?? '',
          'created_at': r['created_at'] ?? now,
          'updated_at': r['updated_at'] ?? now,
          'deleted_at': r['deleted_at'],
        },
        conflictAlgorithm: ConflictAlgorithm.replace,
      );
    }

    await batch.commit(noResult: true);
    await db.close();

    ref.read(wizardProvider.notifier).updateSyncProgress(
      progress: 0.95,
      members: members.length,
      activities: activities.length,
      records: records.length,
    );
  }

  Future<void> _markDone() async {
    await ref.read(wizardProvider.notifier).markDone();
  }

  @override
  Widget build(BuildContext context) {
    final wizard = ref.watch(wizardProvider);

    return Column(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text(
          'Loading your community',
          style: const TextStyle(
            fontFamily: 'Playfair Display',
            fontSize: 24,
            fontWeight: FontWeight.w700,
            color: Colors.white,
          ),
          textAlign: TextAlign.center,
        ),
        if (wizard.tenantName != null) ...[
          const SizedBox(height: IcsSpacing.xs),
          Text(
            wizard.tenantName!,
            style: TextStyle(fontSize: 15, fontWeight: FontWeight.w600, color: IcsColors.accentRed),
            textAlign: TextAlign.center,
          ),
        ],
        if (wizard.adminName != null) ...[
          const SizedBox(height: 4),
          Text(
            'Licensed to: ${wizard.adminName}',
            style: TextStyle(fontSize: 12, color: IcsColors.textMutedDark),
            textAlign: TextAlign.center,
          ),
        ],
        const SizedBox(height: IcsSpacing.xl),
        ClipRRect(
          borderRadius: BorderRadius.all(IcsRadius.s),
          child: LinearProgressIndicator(
            value: wizard.syncProgress,
            minHeight: 6,
            backgroundColor: const Color(0xFF2A2A2A),
            color: IcsColors.accentRed,
          ),
        ),
        const SizedBox(height: IcsSpacing.s),
        Text(
          '${(wizard.syncProgress * 100).toInt()}%',
          style: TextStyle(fontSize: 11, color: IcsColors.textMutedDark),
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: IcsSpacing.l),
        _CountRow(label: 'Members', count: wizard.syncMemberCount, ready: wizard.syncMemberCount > 0),
        const SizedBox(height: IcsSpacing.s),
        _CountRow(label: 'Activities', count: wizard.syncActivityCount, ready: wizard.syncActivityCount > 0),
        const SizedBox(height: IcsSpacing.s),
        _CountRow(label: 'Governance records', count: wizard.syncRecordCount, ready: wizard.syncRecordCount > 0),
        const SizedBox(height: IcsSpacing.s),
        _CountRow(label: 'Bible data', count: 0, ready: true, readyLabel: 'bundled'),
        if (wizard.error != null) ...[
          const SizedBox(height: IcsSpacing.m),
          Text(
            wizard.error!,
            style: TextStyle(fontSize: 12, color: IcsColors.warning),
            textAlign: TextAlign.center,
          ),
        ],
        const SizedBox(height: IcsSpacing.xl),
        Text(
          'This usually takes 30–60 seconds.\nYour device will work offline after this completes.',
          style: TextStyle(fontSize: 11, color: IcsColors.textMutedDark.withValues(alpha: 0.6), height: 1.6),
          textAlign: TextAlign.center,
        ),
      ],
    );
  }
}

class _CountRow extends StatelessWidget {
  const _CountRow({
    required this.label,
    required this.count,
    required this.ready,
    this.readyLabel,
  });

  final String label;
  final int count;
  final bool ready;
  final String? readyLabel;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(
          ready ? Icons.check_circle_outline : Icons.radio_button_unchecked,
          size: 14,
          color: ready ? IcsColors.success : IcsColors.textMutedDark,
        ),
        const SizedBox(width: IcsSpacing.s),
        Text(
          label,
          style: TextStyle(fontSize: 13, color: IcsColors.textMutedDark),
        ),
        const Spacer(),
        Text(
          ready
              ? (readyLabel ?? '$count loaded')
              : 'waiting…',
          style: TextStyle(
            fontSize: 12,
            fontWeight: FontWeight.w600,
            color: ready ? Colors.white : IcsColors.textMutedDark,
          ),
        ),
      ],
    );
  }
}

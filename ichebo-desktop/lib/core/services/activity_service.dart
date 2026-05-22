import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:uuid/uuid.dart';
import '../../sync/sync_engine.dart';
import '../../features/activity/activity_providers.dart';

class ActivityService {
  // ── Single activity create/update ─────────────────────────────────────────

  static Future<int> createActivity(ActivityModel a) async {
    final prefs = await SharedPreferences.getInstance();
    final tenantId = prefs.getString('ics_tenant_id') ?? '';
    final createdBy = prefs.getString('ics_admin_email') ?? 'device';
    final now = DateTime.now().toIso8601String();
    final id = const Uuid().v4();

    final payload = jsonEncode({
      'id': id,
      'tenant_id': tenantId,
      'activity_type': a.activityType,
      'title': a.title,
      'description': a.description,
      'status': a.status,
      'progress': a.progress,
      'assigned_to': a.assignedTo ?? '',
      'linked_record_id': a.linkedRecordId ?? '',
      'parent_activity_id': '',
      'due_at': a.dueAt ?? '',
      'scheduled_at': a.scheduledAt ?? '',
      'completed_at': a.completedAt ?? '',
      'source_app': 'community',
      'metadata': a.metadata,
      'created_by': createdBy,
      'created_at': now,
      'updated_at': now,
    });
    return SyncEngine.instance.activityCreate(payload);
  }

  static Future<int> updateActivity(ActivityModel a) async {
    final now = DateTime.now().toIso8601String();
    final payload = jsonEncode({
      'id': a.id,
      'tenant_id': a.tenantId,
      'activity_type': a.activityType,
      'title': a.title,
      'description': a.description,
      'status': a.status,
      'progress': a.progress,
      'assigned_to': a.assignedTo ?? '',
      'linked_record_id': a.linkedRecordId ?? '',
      'parent_activity_id': '',
      'due_at': a.dueAt ?? '',
      'scheduled_at': a.scheduledAt ?? '',
      'completed_at': a.completedAt ?? '',
      'source_app': 'community',
      'metadata': a.metadata,
      'created_by': a.createdBy,
      'created_at': a.createdAt,
      'updated_at': now,
    });
    return SyncEngine.instance.activityUpdate(payload);
  }

  // ── Gathering dual-write ──────────────────────────────────────────────────

  static Future<int> createGathering({
    required String title,
    required String scheduledAt,
    required String format,   // in_person | digital | hybrid
    required String location,
    required int durationMinutes,
    required String tenantId,
    required String createdBy,
  }) async {
    final now = DateTime.now().toIso8601String();
    final recordId = const Uuid().v4();
    final activityId = const Uuid().v4();

    final customFields = jsonEncode({
      'format': format,
      'location': location,
      'start_at': scheduledAt,
      'duration_minutes': durationMinutes,
    });

    final payload = jsonEncode({
      'record': {
        'id': recordId,
        'tenant_id': tenantId,
        'record_class': 'organizational',
        'record_family': 'community',
        'record_type': 'gathering',
        'title': title,
        'status': 'active',
        'custom_fields': customFields,
        'metadata': '{}',
        'permissions': '{}',
        'created_by': createdBy,
        'created_at': now,
        'updated_at': now,
      },
      'activity': {
        'id': activityId,
        'tenant_id': tenantId,
        'activity_type': 'gathering',
        'title': title,
        'description': '',
        'status': 'pending',
        'progress': 0,
        'assigned_to': '',
        'linked_record_id': recordId,
        'parent_activity_id': '',
        'due_at': scheduledAt,
        'scheduled_at': scheduledAt,
        'completed_at': '',
        'source_app': 'community',
        'metadata': jsonEncode({
          'format': format,
          'location': location,
          'duration_minutes': durationMinutes,
        }),
        'created_by': createdBy,
        'created_at': now,
        'updated_at': now,
      },
    });
    return SyncEngine.instance.gatheringCreate(payload);
  }

  // ── Attendance save ───────────────────────────────────────────────────────

  static Future<int> saveAttendance({
    required String activityId,
    required List<String> presentMemberIds,
  }) async {
    final prefs = await SharedPreferences.getInstance();
    final changedBy = prefs.getString('ics_admin_email') ?? 'device';
    final now = DateTime.now().toIso8601String();

    final payload = jsonEncode({
      'activity_id': activityId,
      'changed_by': changedBy,
      'present_member_ids': presentMemberIds,
      'now': now,
    });
    return SyncEngine.instance.attendanceSave(payload);
  }
}

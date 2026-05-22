import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:uuid/uuid.dart';
import '../../sync/sync_engine.dart';
import '../../features/people/people_providers.dart';

class MemberService {
  static Future<int> createMember(MemberModel m) async {
    final prefs = await SharedPreferences.getInstance();
    final tenantId = prefs.getString('ics_tenant_id') ?? '';
    final createdBy = prefs.getString('ics_admin_email') ?? m.createdAt;
    final now = DateTime.now().toIso8601String();
    final id = const Uuid().v4();

    final payload = jsonEncode({
      'id': id,
      'tenant_id': tenantId,
      'email': m.email,
      'display_name': m.displayName,
      'first_name': m.firstName,
      'last_name': m.lastName,
      'phone': m.phone,
      'competence_level': m.competenceLevel,
      'is_active': m.isActive,
      'shepherd_id': m.shepherdId ?? '',
      'service_order': m.serviceOrder ?? '',
      'custom_fields': '{}',
      'created_by': createdBy,
      'created_at': now,
      'updated_at': now,
    });

    return SyncEngine.instance.memberCreate(payload);
  }

  static Future<int> updateMember(MemberModel m) async {
    final now = DateTime.now().toIso8601String();
    final payload = jsonEncode({
      'id': m.id,
      'tenant_id': m.tenantId,
      'email': m.email,
      'display_name': m.displayName,
      'first_name': m.firstName,
      'last_name': m.lastName,
      'phone': m.phone,
      'competence_level': m.competenceLevel,
      'is_active': m.isActive,
      'shepherd_id': m.shepherdId ?? '',
      'service_order': m.serviceOrder ?? '',
      'custom_fields': '{}',
      'created_by': m.id,
      'created_at': m.createdAt,
      'updated_at': now,
    });

    return SyncEngine.instance.memberUpdate(payload);
  }
}

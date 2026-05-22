import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../../core/database/db.dart';
import '../../core/database/schema.dart';

// ── Member model ──────────────────────────────────────────────────────────────

class MemberModel {
  const MemberModel({
    required this.id,
    required this.tenantId,
    required this.email,
    required this.displayName,
    required this.firstName,
    required this.lastName,
    required this.phone,
    required this.competenceLevel,
    required this.isActive,
    this.shepherdId,
    this.serviceOrder,
    required this.createdAt,
    required this.updatedAt,
  });

  final String id;
  final String tenantId;
  final String email;
  final String displayName;
  final String firstName;
  final String lastName;
  final String phone;
  final int competenceLevel;
  final bool isActive;
  final String? shepherdId;
  final String? serviceOrder;
  final String createdAt;
  final String updatedAt;

  factory MemberModel.fromMap(Map<String, dynamic> m) => MemberModel(
        id: m[cId] as String,
        tenantId: m[cTenantId] as String,
        email: m[cEmail] as String? ?? '',
        displayName: m[cDisplayName] as String? ?? '',
        firstName: m[cFirstName] as String? ?? '',
        lastName: m[cLastName] as String? ?? '',
        phone: m[cPhone] as String? ?? '',
        competenceLevel: m[cCompetenceLevel] as int? ?? 0,
        isActive: (m[cIsActive] as int? ?? 1) == 1,
        shepherdId: m[cShepherdId] as String?,
        serviceOrder: m[cServiceOrder] as String?,
        createdAt: m[cCreatedAt] as String? ?? '',
        updatedAt: m[cUpdatedAt] as String? ?? '',
      );

  MemberModel copyWith({
    String? email,
    String? displayName,
    String? firstName,
    String? lastName,
    String? phone,
    int? competenceLevel,
    bool? isActive,
    String? shepherdId,
    String? serviceOrder,
  }) {
    return MemberModel(
      id: id,
      tenantId: tenantId,
      email: email ?? this.email,
      displayName: displayName ?? this.displayName,
      firstName: firstName ?? this.firstName,
      lastName: lastName ?? this.lastName,
      phone: phone ?? this.phone,
      competenceLevel: competenceLevel ?? this.competenceLevel,
      isActive: isActive ?? this.isActive,
      shepherdId: shepherdId ?? this.shepherdId,
      serviceOrder: serviceOrder ?? this.serviceOrder,
      createdAt: createdAt,
      updatedAt: updatedAt,
    );
  }
}

// ── Raw member list from SQLite ───────────────────────────────────────────────

final membersProvider = FutureProvider<List<MemberModel>>((ref) async {
  final db = await ref.watch(dbProvider.future);
  final prefs = await SharedPreferences.getInstance();
  final tenantId = prefs.getString('ics_tenant_id') ?? '';

  final rows = await db.query(
    tMembers,
    where: '$cTenantId = ? AND $cDeletedAt IS NULL',
    whereArgs: [tenantId],
    orderBy: '$cDisplayName ASC',
  );
  return rows.map(MemberModel.fromMap).toList();
});

// ── Single member by id ───────────────────────────────────────────────────────

final memberByIdProvider =
    FutureProvider.family<MemberModel?, String>((ref, id) async {
  final db = await ref.watch(dbProvider.future);
  final rows = await db.query(
    tMembers,
    where: '$cId = ?',
    whereArgs: [id],
    limit: 1,
  );
  if (rows.isEmpty) return null;
  return MemberModel.fromMap(rows.first);
});

// ── Search + filter state ─────────────────────────────────────────────────────

final memberSearchProvider = StateProvider<String>((_) => '');
final memberFilterLevelProvider = StateProvider<int?>((_) => null);
final memberFilterServiceOrderProvider = StateProvider<String?>((_) => null);
final selectedMemberIdProvider = StateProvider<String?>((_) => null);

// ── Derived: filtered list (pure Dart — no extra SQL) ────────────────────────

final filteredMembersProvider = Provider<AsyncValue<List<MemberModel>>>((ref) {
  final all = ref.watch(membersProvider);
  final query = ref.watch(memberSearchProvider).toLowerCase();
  final levelFilter = ref.watch(memberFilterLevelProvider);
  final soFilter = ref.watch(memberFilterServiceOrderProvider);

  return all.whenData((list) {
    return list.where((m) {
      if (query.isNotEmpty) {
        final nameMatch = m.displayName.toLowerCase().contains(query) ||
            m.firstName.toLowerCase().contains(query) ||
            m.lastName.toLowerCase().contains(query) ||
            m.email.toLowerCase().contains(query);
        if (!nameMatch) return false;
      }
      if (levelFilter != null && m.competenceLevel != levelFilter) return false;
      if (soFilter != null && m.serviceOrder != soFilter) return false;
      return true;
    }).toList();
  });
});

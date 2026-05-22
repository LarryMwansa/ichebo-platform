import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../../core/database/db.dart';
import '../../core/database/schema.dart';

// ── Member model ──────────────────────────────────────────────────────────────

class MemberModel {
  const MemberModel({
    required this.id,
    required this.displayName,
    required this.firstName,
    required this.lastName,
    required this.email,
    required this.phone,
    required this.competenceLevel,
    required this.isActive,
    this.shepherdId,
    this.serviceOrder,
    required this.updatedAt,
  });

  final String  id;
  final String  displayName;
  final String  firstName;
  final String  lastName;
  final String  email;
  final String  phone;
  final int     competenceLevel;
  final bool    isActive;
  final String? shepherdId;
  final String? serviceOrder;
  final String  updatedAt;

  String get initials {
    final parts = displayName.trim().split(' ');
    if (parts.length >= 2) return '${parts.first[0]}${parts.last[0]}'.toUpperCase();
    return displayName.isNotEmpty ? displayName[0].toUpperCase() : '?';
  }

  static const _levelNames = [
    'Seeker', 'Foundational', 'Active', 'Functional', 'Leader', 'Apostolic',
  ];
  String get levelName => _levelNames[competenceLevel.clamp(0, 5)];

  factory MemberModel.fromMap(Map<String, dynamic> m) => MemberModel(
    id:              m[cId]             as String,
    displayName:     m[cDisplayName]    as String? ?? '',
    firstName:       m[cFirstName]      as String? ?? '',
    lastName:        m[cLastName]       as String? ?? '',
    email:           m[cEmail]          as String? ?? '',
    phone:           m[cPhone]          as String? ?? '',
    competenceLevel: m[cCompetenceLevel] as int?   ?? 0,
    isActive:        (m[cIsActive]      as int?    ?? 1) == 1,
    shepherdId:      m[cShepherdId]     as String?,
    serviceOrder:    m[cServiceOrder]   as String?,
    updatedAt:       m[cUpdatedAt]      as String? ?? '',
  );
}

// ── All members for this tenant ───────────────────────────────────────────────

final membersProvider = FutureProvider<List<MemberModel>>((ref) async {
  final db     = await ref.watch(dbProvider.future);
  final prefs  = await SharedPreferences.getInstance();
  final tenant = prefs.getString('ics_tenant_id') ?? '';

  final rows = await db.query(
    tMembers,
    where:    '$cTenantId = ? AND ($cDeletedAt IS NULL OR $cDeletedAt = \'\')',
    whereArgs: [tenant],
    orderBy:  '$cDisplayName ASC',
  );
  return rows.map(MemberModel.fromMap).toList();
});

// ── Single member by id (family provider) ────────────────────────────────────

final memberByIdProvider =
    FutureProvider.family<MemberModel?, String>((ref, id) async {
  final db   = await ref.watch(dbProvider.future);
  final rows = await db.query(
    tMembers,
    where:    '$cId = ?',
    whereArgs: [id],
    limit:    1,
  );
  if (rows.isEmpty) return null;
  return MemberModel.fromMap(rows.first);
});

// ── Search + filter state ─────────────────────────────────────────────────────

final memberSearchProvider      = StateProvider<String>((_) => '');
final memberFilterLevelProvider = StateProvider<int?>((_) => null);
final selectedMemberIdProvider  = StateProvider<String?>((_) => null);

// ── Derived filtered list ─────────────────────────────────────────────────────

final filteredMembersProvider = Provider<AsyncValue<List<MemberModel>>>((ref) {
  final all    = ref.watch(membersProvider);
  final query  = ref.watch(memberSearchProvider).toLowerCase();
  final level  = ref.watch(memberFilterLevelProvider);

  return all.whenData((list) => list.where((m) {
    if (query.isNotEmpty) {
      final hit = m.displayName.toLowerCase().contains(query) ||
          m.firstName.toLowerCase().contains(query)  ||
          m.lastName.toLowerCase().contains(query)   ||
          m.email.toLowerCase().contains(query);
      if (!hit) return false;
    }
    if (level != null && m.competenceLevel != level) return false;
    return true;
  }).toList());
});

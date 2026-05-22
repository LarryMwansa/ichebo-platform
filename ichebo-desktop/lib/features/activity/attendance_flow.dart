import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/services/activity_service.dart';
import '../../core/theme/tokens.dart';
import '../../shared/level_badge.dart';
import '../people/people_providers.dart';
import 'activity_providers.dart';

class AttendanceFlow extends ConsumerStatefulWidget {
  const AttendanceFlow({super.key, required this.activity});
  final ActivityModel activity;

  @override
  ConsumerState<AttendanceFlow> createState() => _AttendanceFlowState();
}

class _AttendanceFlowState extends ConsumerState<AttendanceFlow> {
  final _searchCtrl = TextEditingController();
  String _query = '';
  // present member IDs — starts empty, pre-populated once prior attendance loads
  final Set<String> _present = {};
  bool _loaded = false;
  bool _saving = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadPrior();
  }

  Future<void> _loadPrior() async {
    final prior = await ref.read(attendanceMembersProvider(widget.activity.id).future);
    if (mounted) {
      setState(() {
        _present.addAll(prior);
        _loaded = true;
      });
    }
  }

  @override
  void dispose() {
    _searchCtrl.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    setState(() { _saving = true; _error = null; });

    final result = await ActivityService.saveAttendance(
      activityId: widget.activity.id,
      presentMemberIds: _present.toList(),
    );

    if (!mounted) return;

    if (result == 0 || result == -99) {
      ref.invalidate(activitiesProvider);
      ref.invalidate(activityByIdProvider(widget.activity.id));
      ref.invalidate(attendanceCountProvider(widget.activity.id));
      ref.invalidate(attendanceMembersProvider(widget.activity.id));
      Navigator.of(context).pop();
    } else {
      setState(() { _saving = false; _error = 'Save failed (code $result). Try again.'; });
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final membersAsync = ref.watch(membersProvider);

    return Scaffold(
      backgroundColor: isDark ? IcsColors.inkBg : IcsColors.stoneBg,
      body: Column(
        children: [
          // ── Top bar ─────────────────────────────────────────────────────
          Container(
            height: 56,
            padding: const EdgeInsets.symmetric(horizontal: IcsSpacing.l),
            decoration: BoxDecoration(
              color: isDark ? IcsColors.ink2 : Colors.white,
              border: Border(
                bottom: BorderSide(color: isDark ? IcsColors.borderDark : IcsColors.borderLight),
              ),
            ),
            child: Row(
              children: [
                TextButton(
                  onPressed: () => Navigator.of(context).pop(),
                  child: Text('Cancel',
                      style: TextStyle(color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted)),
                ),
                const SizedBox(width: IcsSpacing.m),
                Expanded(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text(
                        'Mark attendance',
                        style: TextStyle(
                          fontSize: 14, fontWeight: FontWeight.w700,
                          color: isDark ? Colors.white : IcsColors.inkBg,
                        ),
                      ),
                      Text(
                        widget.activity.title,
                        style: TextStyle(fontSize: 11,
                            color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted),
                        overflow: TextOverflow.ellipsis,
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: IcsSpacing.m),
                ElevatedButton(
                  onPressed: _saving ? null : _save,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: IcsColors.accentRed,
                    foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
                  ),
                  child: _saving
                      ? const SizedBox(width: 16, height: 16,
                          child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                      : Text('Save attendance (${_present.length})',
                          style: const TextStyle(fontWeight: FontWeight.w600)),
                ),
              ],
            ),
          ),

          // ── Search bar ───────────────────────────────────────────────────
          Container(
            padding: const EdgeInsets.fromLTRB(IcsSpacing.l, IcsSpacing.m, IcsSpacing.l, IcsSpacing.s),
            color: isDark ? IcsColors.inkBg : IcsColors.stoneBg,
            child: TextField(
              controller: _searchCtrl,
              onChanged: (v) => setState(() => _query = v.toLowerCase()),
              style: TextStyle(fontSize: 13, color: isDark ? Colors.white : IcsColors.inkBg),
              decoration: InputDecoration(
                isDense: true,
                hintText: 'Search members…',
                hintStyle: TextStyle(fontSize: 13,
                    color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted),
                prefixIcon: Icon(Icons.search, size: 16,
                    color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted),
                filled: true,
                fillColor: isDark ? const Color(0xFF1A1A1A) : Colors.white,
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(8),
                  borderSide: BorderSide(
                      color: isDark ? IcsColors.borderDark : IcsColors.borderLight),
                ),
                focusedBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(8),
                  borderSide: const BorderSide(color: IcsColors.accentRed, width: 1.5),
                ),
                contentPadding: const EdgeInsets.symmetric(horizontal: IcsSpacing.m, vertical: 10),
                suffixIcon: _query.isNotEmpty
                    ? IconButton(
                        icon: const Icon(Icons.close, size: 14),
                        onPressed: () { _searchCtrl.clear(); setState(() => _query = ''); },
                        color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted,
                      )
                    : null,
              ),
            ),
          ),

          // ── Summary strip ────────────────────────────────────────────────
          membersAsync.maybeWhen(
            data: (members) => Container(
              padding: const EdgeInsets.symmetric(horizontal: IcsSpacing.l, vertical: 6),
              color: isDark ? IcsColors.inkBg : IcsColors.stoneBg,
              child: Row(
                children: [
                  Text(
                    '${_present.length} of ${members.length} marked present',
                    style: TextStyle(fontSize: 12,
                        color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted),
                  ),
                  const Spacer(),
                  TextButton(
                    onPressed: () => setState(() {
                      _present.addAll(members.map((m) => m.id));
                    }),
                    child: const Text('Select all',
                        style: TextStyle(fontSize: 12, color: IcsColors.accentRed)),
                  ),
                  TextButton(
                    onPressed: () => setState(() => _present.clear()),
                    child: Text('Clear all',
                        style: TextStyle(fontSize: 12,
                            color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted)),
                  ),
                ],
              ),
            ),
            orElse: () => const SizedBox.shrink(),
          ),

          Divider(height: 1, color: isDark ? IcsColors.borderDark : IcsColors.borderLight),

          if (_error != null)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: IcsSpacing.l, vertical: IcsSpacing.s),
              color: IcsColors.error.withValues(alpha: 0.1),
              child: Text(_error!, style: const TextStyle(fontSize: 12, color: IcsColors.error)),
            ),

          // ── Member list ──────────────────────────────────────────────────
          Expanded(
            child: !_loaded
                ? const Center(child: CircularProgressIndicator())
                : membersAsync.when(
                    loading: () => const Center(child: CircularProgressIndicator()),
                    error: (e, _) => Center(child: Text('Error: $e')),
                    data: (members) {
                      final filtered = _query.isEmpty
                          ? members
                          : members
                              .where((m) =>
                                  m.displayName.toLowerCase().contains(_query) ||
                                  m.email.toLowerCase().contains(_query))
                              .toList();

                      if (filtered.isEmpty) {
                        return Center(
                          child: Text('No members match.',
                              style: TextStyle(
                                  color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted)),
                        );
                      }

                      return ListView.builder(
                        itemCount: filtered.length,
                        itemBuilder: (context, i) {
                          final m = filtered[i];
                          final isPresent = _present.contains(m.id);
                          return _AttendanceTile(
                            member: m,
                            isPresent: isPresent,
                            isDark: isDark,
                            onToggle: () => setState(() {
                              if (isPresent) {
                                _present.remove(m.id);
                              } else {
                                _present.add(m.id);
                              }
                            }),
                          );
                        },
                      );
                    },
                  ),
          ),
        ],
      ),
    );
  }
}

// ── Single attendance row ─────────────────────────────────────────────────────

class _AttendanceTile extends StatefulWidget {
  const _AttendanceTile({
    required this.member,
    required this.isPresent,
    required this.isDark,
    required this.onToggle,
  });

  final MemberModel member;
  final bool isPresent;
  final bool isDark;
  final VoidCallback onToggle;

  @override
  State<_AttendanceTile> createState() => _AttendanceTileState();
}

class _AttendanceTileState extends State<_AttendanceTile> {
  bool _hovered = false;

  @override
  Widget build(BuildContext context) {
    final bgPresent = IcsColors.success.withValues(alpha: 0.08);
    final bgHover   = (widget.isDark ? Colors.white : Colors.black).withValues(alpha: 0.04);

    return MouseRegion(
      onEnter: (_) => setState(() => _hovered = true),
      onExit:  (_) => setState(() => _hovered = false),
      child: GestureDetector(
        onTap: widget.onToggle,
        child: Container(
          height: 52,
          padding: const EdgeInsets.symmetric(horizontal: IcsSpacing.l),
          decoration: BoxDecoration(
            color: widget.isPresent ? bgPresent : (_hovered ? bgHover : Colors.transparent),
            border: widget.isPresent
                ? const Border(left: BorderSide(color: IcsColors.success, width: 3))
                : null,
          ),
          child: Row(
            children: [
              LevelBadge(level: widget.member.competenceLevel),
              const SizedBox(width: IcsSpacing.m),
              Expanded(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      widget.member.displayName,
                      style: TextStyle(
                        fontSize: 13, fontWeight: FontWeight.w600,
                        color: widget.isDark ? Colors.white : IcsColors.inkBg,
                      ),
                    ),
                    Text(
                      widget.member.email,
                      style: TextStyle(fontSize: 11,
                          color: widget.isDark ? IcsColors.textMutedDark : IcsColors.textMuted),
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                ),
              ),
              // Present checkbox
              AnimatedContainer(
                duration: const Duration(milliseconds: 150),
                width: 22, height: 22,
                decoration: BoxDecoration(
                  color: widget.isPresent ? IcsColors.success : Colors.transparent,
                  borderRadius: BorderRadius.circular(4),
                  border: Border.all(
                    color: widget.isPresent
                        ? IcsColors.success
                        : (widget.isDark ? IcsColors.borderDark : IcsColors.borderLight),
                    width: 1.5,
                  ),
                ),
                child: widget.isPresent
                    ? const Icon(Icons.check, size: 14, color: Colors.white)
                    : null,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

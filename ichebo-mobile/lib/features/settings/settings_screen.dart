import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/state/auth_state.dart';
import '../../core/theme/tokens.dart';
import '../../sync/sync_engine.dart';
import '../../sync/sync_state.dart';

class SettingsScreen extends ConsumerWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth   = ref.watch(authProvider);
    final status = ref.watch(syncStateProvider);

    return Scaffold(
      backgroundColor: IcsColors.inkBg,
      appBar: AppBar(
        backgroundColor: IcsColors.stone1,
        title: const Text('Settings'),
      ),
      body: ListView(
        padding: const EdgeInsets.all(IcsSpacing.m),
        children: [
          _SectionLabel(label: 'Account'),
          _InfoTile(label: 'Email',  value: auth.email  ?? '—'),
          _InfoTile(label: 'Tenant', value: auth.tenantName ?? '—'),
          const SizedBox(height: IcsSpacing.m),

          _SectionLabel(label: 'Sync'),
          _InfoTile(
            label: 'Engine',
            value: SyncEngine.instance.isLoaded ? 'Active' : 'Not loaded',
          ),
          _InfoTile(
            label: 'Status',
            value: _statusLabel(status.state),
          ),
          _InfoTile(
            label: 'Pending',
            value: '${status.pendingCount} changes',
          ),
          const SizedBox(height: IcsSpacing.m),

          _SectionLabel(label: 'App'),
          _InfoTile(label: 'Version', value: '1.0.0+1'),
          const SizedBox(height: IcsSpacing.m),

          _DangerSection(ref: ref),
          const SizedBox(height: IcsSpacing.xl),
        ],
      ),
    );
  }

  static String _statusLabel(SyncState s) => switch (s) {
    SyncState.synced   => 'Synced',
    SyncState.syncing  => 'Syncing',
    SyncState.conflict => 'Conflicts present',
    SyncState.blocked  => 'Blocked',
    SyncState.offline  => 'Offline',
  };
}

// ── Section label ─────────────────────────────────────────────────────────────

class _SectionLabel extends StatelessWidget {
  const _SectionLabel({required this.label});
  final String label;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: IcsSpacing.s),
      child: Text(
        label.toUpperCase(),
        style: const TextStyle(
          color: IcsColors.textMuted,
          fontSize: 11,
          letterSpacing: 1.2,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }
}

// ── Info tile ─────────────────────────────────────────────────────────────────

class _InfoTile extends StatelessWidget {
  const _InfoTile({required this.label, required this.value});
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 1),
      padding: const EdgeInsets.symmetric(
          horizontal: IcsSpacing.m, vertical: IcsSpacing.s + 2),
      decoration: BoxDecoration(
        color: IcsColors.stone1,
        border: Border.all(color: IcsColors.borderDark),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label,
              style: const TextStyle(
                  color: IcsColors.textMuted, fontSize: 13)),
          Text(value,
              style: const TextStyle(
                  color: Colors.white, fontSize: 13)),
        ],
      ),
    );
  }
}

// ── Danger section ────────────────────────────────────────────────────────────

class _DangerSection extends StatelessWidget {
  const _DangerSection({required this.ref});
  final WidgetRef ref;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: double.infinity,
      child: OutlinedButton(
        onPressed: () => _confirmLogout(context, ref),
        style: OutlinedButton.styleFrom(
          foregroundColor: IcsColors.accentRed,
          side: const BorderSide(color: IcsColors.accentRed),
        ),
        child: const Text('Sign out'),
      ),
    );
  }

  Future<void> _confirmLogout(BuildContext context, WidgetRef ref) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: IcsColors.stone1,
        title: const Text('Sign out?',
            style: TextStyle(color: Colors.white)),
        content: const Text(
          'Unsynced changes will remain on this device and sync '
          'when you sign in again.',
          style: TextStyle(color: IcsColors.textMuted),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            style: TextButton.styleFrom(foregroundColor: IcsColors.accentRed),
            child: const Text('Sign out'),
          ),
        ],
      ),
    );
    if (confirmed == true) {
      SyncEngine.instance.stop();
      ref.read(authProvider.notifier).logout();
    }
  }
}

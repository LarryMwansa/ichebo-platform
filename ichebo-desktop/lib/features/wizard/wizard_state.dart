import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

enum WizardStep { activation, account, sync, done }

class WizardStateModel {
  const WizardStateModel({
    this.step = WizardStep.activation,
    this.licenceKey = '',
    this.tenantId,
    this.tenantName,
    this.deviceId,
    this.adminName,
    this.adminEmail,
    this.syncProgress = 0.0,
    this.syncMemberCount = 0,
    this.syncActivityCount = 0,
    this.syncRecordCount = 0,
    this.error,
    this.isLoading = false,
  });

  final WizardStep step;
  final String licenceKey;
  final String? tenantId;
  final String? tenantName;
  final String? deviceId;
  final String? adminName;
  final String? adminEmail;
  final double syncProgress;
  final int syncMemberCount;
  final int syncActivityCount;
  final int syncRecordCount;
  final String? error;
  final bool isLoading;

  WizardStateModel copyWith({
    WizardStep? step,
    String? licenceKey,
    String? tenantId,
    String? tenantName,
    String? deviceId,
    String? adminName,
    String? adminEmail,
    double? syncProgress,
    int? syncMemberCount,
    int? syncActivityCount,
    int? syncRecordCount,
    String? error,
    bool? isLoading,
    bool clearError = false,
  }) {
    return WizardStateModel(
      step: step ?? this.step,
      licenceKey: licenceKey ?? this.licenceKey,
      tenantId: tenantId ?? this.tenantId,
      tenantName: tenantName ?? this.tenantName,
      deviceId: deviceId ?? this.deviceId,
      adminName: adminName ?? this.adminName,
      adminEmail: adminEmail ?? this.adminEmail,
      syncProgress: syncProgress ?? this.syncProgress,
      syncMemberCount: syncMemberCount ?? this.syncMemberCount,
      syncActivityCount: syncActivityCount ?? this.syncActivityCount,
      syncRecordCount: syncRecordCount ?? this.syncRecordCount,
      error: clearError ? null : (error ?? this.error),
      isLoading: isLoading ?? this.isLoading,
    );
  }
}

class WizardNotifier extends StateNotifier<WizardStateModel> {
  WizardNotifier() : super(const WizardStateModel());

  void setLicenceKey(String key) =>
      state = state.copyWith(licenceKey: key, clearError: true);

  void setActivationResult({
    required String tenantId,
    required String tenantName,
    required String deviceId,
  }) {
    state = state.copyWith(
      tenantId: tenantId,
      tenantName: tenantName,
      deviceId: deviceId,
      step: WizardStep.account,
      isLoading: false,
      clearError: true,
    );
  }

  void setAccountDetails({required String name, required String email}) =>
      state = state.copyWith(adminName: name, adminEmail: email, clearError: true);

  void advanceToSync() =>
      state = state.copyWith(step: WizardStep.sync, isLoading: false, clearError: true);

  void updateSyncProgress({
    required double progress,
    int? members,
    int? activities,
    int? records,
  }) {
    state = state.copyWith(
      syncProgress: progress,
      syncMemberCount: members ?? state.syncMemberCount,
      syncActivityCount: activities ?? state.syncActivityCount,
      syncRecordCount: records ?? state.syncRecordCount,
    );
  }

  void setLoading(bool loading) => state = state.copyWith(isLoading: loading);

  void setError(String message) =>
      state = state.copyWith(error: message, isLoading: false);

  Future<void> markDone() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('ics_wizard_done', true);
    state = state.copyWith(step: WizardStep.done);
  }
}

final wizardProvider =
    StateNotifierProvider<WizardNotifier, WizardStateModel>(
  (_) => WizardNotifier(),
);

// Read-only provider: has the wizard been completed?
final wizardDoneProvider = FutureProvider<bool>((ref) async {
  final prefs = await SharedPreferences.getInstance();
  return prefs.getBool('ics_wizard_done') ?? false;
});

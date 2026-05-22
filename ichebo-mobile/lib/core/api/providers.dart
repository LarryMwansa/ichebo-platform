import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../state/auth_state.dart';
import 'api_client.dart';

final apiClientProvider = Provider<ApiClient>((ref) {
  final token = ref.watch(authProvider).token;
  return ApiClient(token: token);
});

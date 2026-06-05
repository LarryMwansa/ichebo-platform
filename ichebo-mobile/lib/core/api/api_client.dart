import 'dart:convert';
import 'package:http/http.dart' as http;

const bool _kRelease = bool.fromEnvironment('dart.vm.product');
const _baseUrl = _kRelease ? 'https://app.ichebo.org/api' : 'http://localhost:8001/api';

class ApiException implements Exception {
  const ApiException(this.statusCode, this.message);
  final int    statusCode;
  final String message;
  @override
  String toString() => 'ApiException($statusCode): $message';
}

class ApiClient {
  ApiClient({this.token});
  final String? token;

  Map<String, String> get _headers => {
    'Content-Type': 'application/json',
    if (token != null) 'Authorization': 'Token $token',
  };

  Future<Map<String, dynamic>> post(String path, Map<String, dynamic> body) async {
    final res = await http.post(
      Uri.parse('$_baseUrl$path'),
      headers: _headers,
      body: jsonEncode(body),
    );
    final data = jsonDecode(res.body) as Map<String, dynamic>;
    if (res.statusCode >= 400) {
      final msg = data['detail']
          ?? (data['non_field_errors'] as List?)?.first
          ?? res.body;
      throw ApiException(res.statusCode, msg.toString());
    }
    return data;
  }

  Future<dynamic> get(String path) async {
    final res = await http.get(
      Uri.parse('$_baseUrl$path'),
      headers: _headers,
    );
    if (res.statusCode >= 400) {
      throw ApiException(res.statusCode, res.body);
    }
    return jsonDecode(res.body);
  }
}

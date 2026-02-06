import 'api_client.dart';
import 'api_config.dart';

class AdminRoleService {
  AdminRoleService({ApiClient? client}) : _client = client ?? ApiClient.instance;
  final ApiClient _client;

  Future<List<dynamic>> pending({int limit = 50}) async {
    try {
      final res = await _client.dio.get(ApiConfig.api('/admin/roles/pending') + '?limit=$limit');
      final data = res.data;
      if (data is Map && data['items'] is List) return data['items'] as List;
      return <dynamic>[];
    } catch (_) {
      return <dynamic>[];
    }
  }

  Future<bool> approve({int? userId, String? email}) async {
    try {
      final payload = <String, dynamic>{};
      if (userId != null) payload['user_id'] = userId;
      if (email != null && email.isNotEmpty) payload['email'] = email;
      final res = await _client.dio.post(ApiConfig.api('/admin/roles/approve'), data: payload);
      final code = res.statusCode ?? 0;
      return code >= 200 && code < 300;
    } catch (_) {
      return false;
    }
  }

  Future<bool> reject({int? userId, String? email, String reason = 'Rejected'}) async {
    try {
      final payload = <String, dynamic>{'reason': reason};
      if (userId != null) payload['user_id'] = userId;
      if (email != null && email.isNotEmpty) payload['email'] = email;
      final res = await _client.dio.post(ApiConfig.api('/admin/roles/reject'), data: payload);
      final code = res.statusCode ?? 0;
      return code >= 200 && code < 300;
    } catch (_) {
      return false;
    }
  }
}

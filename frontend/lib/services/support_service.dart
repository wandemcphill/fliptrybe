import 'api_client.dart';
import 'api_config.dart';

class SupportService {
  SupportService({ApiClient? client}) : _client = client ?? ApiClient.instance;
  final ApiClient _client;

  Future<List<dynamic>> listTickets({bool all = false}) async {
    final url = ApiConfig.api('/support/tickets') + (all ? '?all=1' : '');
    try {
      final res = await _client.dio.get(url);
      final data = res.data;
      if (data is Map && data['items'] is List) return data['items'] as List;
      return <dynamic>[];
    } catch (_) {
      return <dynamic>[];
    }
  }

  Future<Map<String, dynamic>?> createTicket({required String subject, required String message}) async {
    try {
      final res = await _client.dio.post(ApiConfig.api('/support/tickets'), data: {
        'subject': subject,
        'message': message,
      });
      final data = res.data;
      if (data is Map && data['ticket'] is Map) return Map<String, dynamic>.from(data['ticket'] as Map);
      return null;
    } catch (_) {
      return null;
    }
  }

  Future<bool> updateStatus(int ticketId, String status) async {
    try {
      final res = await _client.dio.post(ApiConfig.api('/support/tickets/$ticketId/status'), data: {'status': status});
      final code = res.statusCode ?? 0;
      return code >= 200 && code < 300;
    } catch (_) {
      return false;
    }
  }
}

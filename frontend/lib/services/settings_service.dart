import 'api_client.dart';
import 'api_config.dart';

class SettingsService {
  final ApiClient _client = ApiClient.instance;

  Future<Map<String, dynamic>> getSettings() async {
    try {
      final res = await _client.dio.get(ApiConfig.api('/settings'));
      final data = res.data;
      if (data is Map && data['settings'] is Map) return Map<String, dynamic>.from(data['settings'] as Map);
      return <String, dynamic>{};
    } catch (_) {
      return <String, dynamic>{};
    }
  }

  Future<bool> updateSettings({
    required bool notifInApp,
    required bool notifSms,
    required bool notifWhatsapp,
    required bool darkMode,
  }) async {
    try {
      final res = await _client.dio.post(
        ApiConfig.api('/settings'),
        data: {
          'notif_in_app': notifInApp,
          'notif_sms': notifSms,
          'notif_whatsapp': notifWhatsapp,
          'dark_mode': darkMode,
        },
      );
      final code = res.statusCode ?? 0;
      return code >= 200 && code < 300;
    } catch (_) {
      return false;
    }
  }
}

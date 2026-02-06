import 'api_client.dart';
import 'api_config.dart';

class NotificationService {
  Future<List<dynamic>> inbox() async {
    final data = await ApiClient.instance.getJson(ApiConfig.api('/notify/inbox'));
    return data is List ? data : <dynamic>[];
  }

  Future<bool> flushDemo() async {
    final res = await ApiClient.instance.postJson(ApiConfig.api('/notify/flush-demo'), {});
    return res is Map && res['ok'] == true;
  }
}

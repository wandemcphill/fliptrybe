import 'api_client.dart';
import 'api_config.dart';

class AdminNotifyQueueService {
  Future<List<dynamic>> list({String channel = "", String status = ""}) async {
    final qp = <String, String>{};
    if (channel.trim().isNotEmpty) qp['channel'] = channel.trim();
    if (status.trim().isNotEmpty) qp['status'] = status.trim();
    final uri = Uri.parse(ApiConfig.api('/admin/notify-queue')).replace(queryParameters: qp.isEmpty ? null : qp);
    final data = await ApiClient.instance.getJson(uri.toString());
    return data is List ? data : <dynamic>[];
  }
}

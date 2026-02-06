import 'api_client.dart';
import 'api_config.dart';

class InspectorService {
  final ApiClient _client = ApiClient.instance;

  Future<List<dynamic>> assignments() async {
    final data = await _client.getJson(ApiConfig.api('/inspector/assignments'));
    if (data is Map && data['items'] is List) {
      return data['items'] as List;
    }
    return <dynamic>[];
  }

  Future<bool> submitReport(int assignmentId, {required String verdict, required String report}) async {
    final data = await _client.postJson(
      ApiConfig.api('/inspector/assignments/$assignmentId/submit'),
      {'verdict': verdict, 'report': report},
    );
    return data is Map && data['status'] == 'ok';
  }
}

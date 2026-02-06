import 'api_client.dart';
import 'api_config.dart';

class DriverRosterService {
  Future<List<dynamic>> listDrivers() async {
    final data = await ApiClient.instance.getJson(ApiConfig.api("/drivers"));
    return data is List ? data : <dynamic>[];
  }
}

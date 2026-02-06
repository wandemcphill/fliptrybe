import 'api_client.dart';
import 'api_config.dart';

class AdminService {
  Future<Map<String, dynamic>> overview() async {
    return await ApiClient.instance.getJson(ApiConfig.api("/admin/overview"));
  }

  Future<Map<String, dynamic>> disableUser({required int userId, String reason = "disabled by admin"}) async {
    return await ApiClient.instance.postJson(
      ApiConfig.api("/admin/users/$userId/disable"),
      {"reason": reason},
    );
  }

  Future<Map<String, dynamic>> disableListing({required int listingId, String reason = "disabled by admin"}) async {
    return await ApiClient.instance.postJson(
      ApiConfig.api("/admin/listings/$listingId/disable"),
      {"reason": reason},
    );
  }
}

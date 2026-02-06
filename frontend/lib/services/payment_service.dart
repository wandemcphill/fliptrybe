import 'api_client.dart';
import 'api_config.dart';

class PaymentService {
  Future<Map<String, dynamic>> initialize({required double amount, String purpose = 'topup'}) async {
    final data = await ApiClient.instance.postJson(
      ApiConfig.api('/payments/initialize'),
      {'amount': amount, 'purpose': purpose},
    );
    return data is Map ? Map<String, dynamic>.from(data) : <String, dynamic>{};
  }

  Future<Map<String, dynamic>> confirmSim({required String reference}) async {
    final data = await ApiClient.instance.postJson(
      ApiConfig.api('/payments/confirm'),
      {'reference': reference},
    );
    return data is Map ? Map<String, dynamic>.from(data) : <String, dynamic>{};
  }
}

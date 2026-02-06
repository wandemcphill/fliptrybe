import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'api_config.dart';
class TokenStorage {
  static const _key = 'access_token';
  static const _secure = FlutterSecureStorage();

  Future<void> saveToken(String token) async {
    if (kIsWeb) {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(_key, token);
      return;
    }
    await _secure.write(key: _key, value: token);
  }

  Future<String?> readToken() async {
    if (kIsWeb) {
      final prefs = await SharedPreferences.getInstance();
      return prefs.getString(_key);
    }
    return _secure.read(key: _key);
  }

  Future<void> clear() async {
    if (kIsWeb) {
      final prefs = await SharedPreferences.getInstance();
      await prefs.remove(_key);
      return;
    }
    await _secure.delete(key: _key);
  }
}

class TokenStorageConfig {
  /// Override at build/run time:
  /// flutter run --dart-define=BASE_URL=http://127.0.0.1:5000
  static String api(String path) => ApiConfig.api(path);
}

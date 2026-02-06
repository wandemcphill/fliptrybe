import 'dart:io' show Platform;

import 'package:flutter/foundation.dart' show kIsWeb, kReleaseMode;

class ApiConfig {
  /// Override at build/run time:
  /// flutter run --dart-define=BASE_URL=http://127.0.0.1:5000
  static const String _baseUrlEnv = String.fromEnvironment('BASE_URL', defaultValue: '');

  /// Android-specific override (for device/LAN testing):
  /// flutter run --dart-define=ANDROID_BASE_URL=http://192.168.1.50:5000
  static const String _androidBaseUrlEnv = String.fromEnvironment('ANDROID_BASE_URL', defaultValue: '');

  static String get baseUrl {
    String candidate;
    const renderBase = 'https://tri-o-fliptrybe.onrender.com';
    if (_baseUrlEnv.isNotEmpty) {
      candidate = _baseUrlEnv;
    } else if (Platform.isAndroid && _androidBaseUrlEnv.isNotEmpty) {
      candidate = _androidBaseUrlEnv;
    } else if (kIsWeb) {
      candidate = renderBase;
    } else {
      candidate = renderBase;
    }

    // Release hard-gate: never ship an APK pointing to localhost/emulator loopback.
    if (kReleaseMode) {
      final lower = candidate.toLowerCase();
      final banned = lower.contains('10.0.2.2') || lower.contains('127.0.0.1') || lower.contains('localhost');
      if (banned) {
        throw StateError('Release build misconfigured: BASE_URL must point to production (Render), not $candidate');
      }
    }

    return candidate;
  }

  /// Builds a full API URL under /api
  /// Example: ApiConfig.api('/auth/me') -> http://127.0.0.1:5000/api/auth/me
  static String api(String path) {
    var p = path.trim();
    if (!p.startsWith('/')) p = '/$p';

    // If caller already included /api, don't double it
    if (p.startsWith('/api/')) return '$baseUrl$p';

    return '$baseUrl/api$p';
  }
}

import 'package:flutter/material.dart';

import '../services/settings_service.dart';

class SettingsDemoScreen extends StatefulWidget {
  const SettingsDemoScreen({super.key});

  @override
  State<SettingsDemoScreen> createState() => _SettingsDemoScreenState();
}

class _SettingsDemoScreenState extends State<SettingsDemoScreen> {
  final _svc = SettingsService();

  bool notifInApp = true;
  bool notifSms = false;
  bool notifWhatsapp = false;

  bool darkMode = false;

  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final s = await _svc.getSettings();
    setState(() {
      notifInApp = (s['notif_in_app'] == true);
      notifSms = (s['notif_sms'] == true);
      notifWhatsapp = (s['notif_whatsapp'] == true);
      darkMode = (s['dark_mode'] == true);
      _loading = false;
    });
  }

  Future<void> _save() async {
    await _svc.updateSettings(
      notifInApp: notifInApp,
      notifSms: notifSms,
      notifWhatsapp: notifWhatsapp,
      darkMode: darkMode,
    );
  }

  Future<void> _toggle(void Function() apply) async {
    setState(apply);
    await _save();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Settings'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _load,
          )
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.all(16),
              children: [
                const Text('Notifications', style: TextStyle(fontWeight: FontWeight.w900)),
                const SizedBox(height: 8),
                SwitchListTile(
                  title: const Text('In-app notifications'),
                  value: notifInApp,
                  onChanged: (v) => _toggle(() => notifInApp = v),
                ),
                SwitchListTile(
                  title: const Text('SMS alerts (demo-ready)'),
                  subtitle: const Text('Persisted to backend. Add Termii/NG SMS later.'),
                  value: notifSms,
                  onChanged: (v) => _toggle(() => notifSms = v),
                ),
                SwitchListTile(
                  title: const Text('WhatsApp alerts (demo-ready)'),
                  subtitle: const Text('Persisted to backend. Add WhatsApp Cloud later.'),
                  value: notifWhatsapp,
                  onChanged: (v) => _toggle(() => notifWhatsapp = v),
                ),
                const Divider(height: 26),
                const Text('Appearance', style: TextStyle(fontWeight: FontWeight.w900)),
                SwitchListTile(
                  title: const Text('Dark mode (persisted)'),
                  value: darkMode,
                  onChanged: (v) => _toggle(() => darkMode = v),
                ),
                const SizedBox(height: 14),
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(14),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: const [
                        Text('Persistence ✅', style: TextStyle(fontWeight: FontWeight.w900)),
                        SizedBox(height: 6),
                        Text('These settings are now saved to your backend per user.'),
                      ],
                    ),
                  ),
                ),
              ],
            ),
    );
  }
}

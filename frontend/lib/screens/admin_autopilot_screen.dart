import 'package:flutter/material.dart';

import '../services/admin_autopilot_service.dart';

class AdminAutopilotScreen extends StatefulWidget {
  const AdminAutopilotScreen({super.key});

  @override
  State<AdminAutopilotScreen> createState() => _AdminAutopilotScreenState();
}

class _AdminAutopilotScreenState extends State<AdminAutopilotScreen> {
  final _svc = AdminAutopilotService();
  bool _loading = true;
  bool _enabled = true;
  String _lastRun = "-";
  Map<String, dynamic> _lastTick = const {};

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    final s = await _svc.status();
    if (!mounted) return;
    setState(() {
      _enabled = (s['settings']?['enabled'] ?? true) == true;
      _lastRun = (s['settings']?['last_run_at'] ?? '-')?.toString() ?? '-';
      _loading = false;
    });
  }

  Future<void> _toggle(bool v) async {
    setState(() => _loading = true);
    await _svc.toggle(enabled: v);
    await _load();
  }

  Future<void> _tick() async {
    setState(() => _loading = true);
    final r = await _svc.tick();
    if (!mounted) return;
    setState(() {
      _lastTick = r;
      _loading = false;
    });
    await _load();
  }

  Widget _kv(String k, String v) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Row(
        children: [
          SizedBox(width: 120, child: Text(k, style: const TextStyle(fontWeight: FontWeight.w900))),
          Expanded(child: Text(v)),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Admin: Autopilot"),
        actions: [IconButton(onPressed: _load, icon: const Icon(Icons.refresh))],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.all(16),
              children: [
                SwitchListTile(
                  value: _enabled,
                  onChanged: _toggle,
                  title: const Text("Autopilot enabled"),
                  subtitle: Text("Last run: $_lastRun"),
                ),
                const SizedBox(height: 12),
                ElevatedButton.icon(
                  onPressed: _tick,
                  icon: const Icon(Icons.bolt),
                  label: const Text("Run manual tick"),
                ),
                const SizedBox(height: 16),
                const Text("Last tick result", style: TextStyle(fontWeight: FontWeight.w900)),
                const SizedBox(height: 8),
                if (_lastTick.isEmpty) const Text("No tick run yet."),
                if (_lastTick.isNotEmpty) ...[
                  _kv("Skipped", (_lastTick['skipped'] ?? '').toString()),
                  _kv("Payouts", (_lastTick['payouts'] ?? '').toString()),
                  _kv("Queue", (_lastTick['queue'] ?? '').toString()),
                  _kv("Drivers", (_lastTick['drivers'] ?? '').toString()),
                ],
              ],
            ),
    );
  }
}

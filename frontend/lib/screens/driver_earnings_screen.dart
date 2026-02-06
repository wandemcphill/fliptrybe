import 'package:flutter/material.dart';

import '../services/wallet_service.dart';

class DriverEarningsScreen extends StatefulWidget {
  const DriverEarningsScreen({super.key});

  @override
  State<DriverEarningsScreen> createState() => _DriverEarningsScreenState();
}

class _DriverEarningsScreenState extends State<DriverEarningsScreen> {
  final _svc = WalletService();

  bool _loading = true;
  List<dynamic> _ledger = const [];

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    final l = await _svc.ledger();
    setState(() {
      _ledger = l;
      _loading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    final earnings = _ledger.whereType<Map>().map((e) => Map<String, dynamic>.from(e as Map)).where((m) => (m['kind'] ?? '') == 'delivery_fee').toList();
    final total = earnings.fold<double>(0.0, (sum, m) => sum + (double.tryParse((m['amount'] ?? 0).toString()) ?? 0.0));

    return Scaffold(
      appBar: AppBar(
        title: const Text("Driver Earnings"),
        actions: [IconButton(onPressed: _load, icon: const Icon(Icons.refresh))],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.all(16),
              children: [
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text("Total earnings", style: TextStyle(fontWeight: FontWeight.w900)),
                        const SizedBox(height: 6),
                        Text("₦$total", style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w900)),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 14),
                const Text("Trips", style: TextStyle(fontWeight: FontWeight.w900)),
                const SizedBox(height: 8),
                if (earnings.isEmpty)
                  const Text("No deliveries yet.")
                else
                  ...earnings.map((m) => Card(
                        child: ListTile(
                          title: Text("₦${m['amount'] ?? 0}", style: const TextStyle(fontWeight: FontWeight.w900)),
                          subtitle: Text((m['note'] ?? '').toString()),
                        ),
                      )),
              ],
            ),
    );
  }
}

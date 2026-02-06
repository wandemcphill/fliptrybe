import 'package:flutter/material.dart';

import '../services/moneybox_service.dart';

class MoneyBoxLedgerScreen extends StatefulWidget {
  const MoneyBoxLedgerScreen({super.key});

  @override
  State<MoneyBoxLedgerScreen> createState() => _MoneyBoxLedgerScreenState();
}

class _MoneyBoxLedgerScreenState extends State<MoneyBoxLedgerScreen> {
  final _svc = MoneyBoxService();
  late Future<List<dynamic>> _data;

  @override
  void initState() {
    super.initState();
    _data = _svc.ledger();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('MoneyBox History')),
      body: FutureBuilder<List<dynamic>>(
        future: _data,
        builder: (context, snap) {
          if (snap.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          final items = snap.data ?? [];
          if (items.isEmpty) {
            return const Center(child: Text('No MoneyBox activity yet.'));
          }
          return ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: items.length,
            itemBuilder: (_, i) {
              final item = items[i] as Map;
              final type = item['type']?.toString().toUpperCase() ?? 'EVENT';
              final amount = item['amount']?.toString() ?? '0';
              final created = item['created_at']?.toString() ?? '';
              return Card(
                child: ListTile(
                  title: Text('$type • ₦$amount'),
                  subtitle: Text(created),
                ),
              );
            },
          );
        },
      ),
    );
  }
}

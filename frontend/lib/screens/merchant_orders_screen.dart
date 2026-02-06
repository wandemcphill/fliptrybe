import 'package:flutter/material.dart';
import '../services/order_service.dart';
import '../services/api_service.dart';
import 'order_detail_screen.dart';

class MerchantOrdersScreen extends StatefulWidget {
  const MerchantOrdersScreen({super.key});

  @override
  State<MerchantOrdersScreen> createState() => _MerchantOrdersScreenState();
}

class _MerchantOrdersScreenState extends State<MerchantOrdersScreen> {
  final _svc = OrderService();
  late Future<List<dynamic>> _future;

    @override
  void initState() {
    super.initState();
    _future = _load();
  }

  Future<List<dynamic>> _load() async {
    await _meId();
    return await _svc.merchantOrders();
  }

  Future<void> _reload() async {
    setState(() => _future = _load());
  }

  Future<int> _meId() async {
    try {
      final me = await ApiService.getProfile();
      final id = me['id'];
      if (id is int) return id;
      final parsed = int.tryParse(id.toString());
      if (parsed != null) return parsed;
    } catch (_) {}
    // TODO: wire real auth/identity; fallback for demo build
    return 1;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Merchant Orders")),
      body: RefreshIndicator(
        onRefresh: _reload,
        child: FutureBuilder<List<dynamic>>(
          future: _future,
          builder: (context, snap) {
            if (snap.connectionState == ConnectionState.waiting) {
              return const Center(child: CircularProgressIndicator());
            }
            final items = snap.data ?? [];
            if (items.isEmpty) {
              return ListView(
                padding: const EdgeInsets.all(16),
                children: const [
                  SizedBox(height: 50),
                  Icon(Icons.receipt_long_outlined, size: 44),
                  SizedBox(height: 12),
                  Center(child: Text("No merchant orders yet.")),
                ],
              );
            }
            return ListView.separated(
              padding: const EdgeInsets.all(12),
              itemCount: items.length,
              separatorBuilder: (_, __) => const Divider(),
              itemBuilder: (context, i) {
                final o = items[i] as Map<String, dynamic>;
                return ListTile(
                  leading: const Icon(Icons.storefront),
                  onTap: () {
                    final oid = o['id'];
                    final id = (oid is int) ? oid : int.tryParse(oid.toString());
                    if (id != null) {
                      Navigator.push(
                        context,
                        MaterialPageRoute(builder: (_) => OrderDetailScreen(orderId: id)),
                      );
                    }
                  },
                  title: Text("Order #${o['id']} • ₦${o['amount']}"),
                  subtitle: Text("${o['status']}"),
                );
              },
            );
          },
        ),
      ),
    );
  }
}

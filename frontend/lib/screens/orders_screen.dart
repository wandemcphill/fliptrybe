import 'package:flutter/material.dart';

import '../services/order_service.dart';
import 'order_detail_screen.dart';
import 'listing_detail_screen.dart';

class OrdersScreen extends StatefulWidget {
  const OrdersScreen({super.key});

  @override
  State<OrdersScreen> createState() => _OrdersScreenState();
}

class _OrdersScreenState extends State<OrdersScreen> with SingleTickerProviderStateMixin {
  final _svc = OrderService();
  bool _loading = true;
  List<dynamic> _rows = const [];

  late final TabController _tabs;

  @override
  void initState() {
    super.initState();
    _tabs = TabController(length: 4, vsync: this);
    _tabs.addListener(() {
      if (_tabs.indexIsChanging) return;
      _applyFilter();
    });
    _load();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    final rows = await _svc.myOrders();
    if (!mounted) return;
    setState(() {
      _rows = rows;
      _loading = false;
    });
  }

  String _tabStatus() {
    switch (_tabs.index) {
      case 0:
        return "all";
      case 1:
        return "pending";
      case 2:
        return "in_progress";
      case 3:
        return "completed";
    }
    return "all";
  }

  void _applyFilter() {
    setState(() {}); // filter is computed in build
  }

  List<Map<String, dynamic>> _filtered() {
    final status = _tabStatus();
    final out = <Map<String, dynamic>>[];
    for (final raw in _rows) {
      if (raw is! Map) continue;
      final m = Map<String, dynamic>.from(raw as Map);
      final s = (m["status"] ?? "").toString();
      if (status == "all") {
        out.add(m);
        continue;
      }
      if (status == "pending") {
        if (["created", "awaiting_merchant", "accepted"].contains(s)) out.add(m);
      } else if (status == "in_progress") {
        if (["assigned", "picked_up", "delivered"].contains(s)) out.add(m);
      } else if (status == "completed") {
        if (["completed", "cancelled"].contains(s)) out.add(m);
      }
    }
    return out;
  }

  @override
  void dispose() {
    _tabs.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final rows = _filtered();

    return Scaffold(
      appBar: AppBar(
        title: const Text("My Orders"),
        actions: [IconButton(onPressed: _load, icon: const Icon(Icons.refresh))],
        bottom: TabBar(
          controller: _tabs,
          tabs: const [
            Tab(text: "All"),
            Tab(text: "Pending"),
            Tab(text: "In Progress"),
            Tab(text: "Completed"),
          ],
        ),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : rows.isEmpty
              ? const Center(child: Text("No orders yet."))
              : ListView.builder(
                  itemCount: rows.length,
                  itemBuilder: (_, i) {
                    final m = rows[i];
                    final id = int.tryParse((m["id"] ?? "").toString()) ?? 0;
                    final amount = (m["amount"] ?? 0).toString();
                    final status = (m["status"] ?? "").toString();
                    final listingTitle = (m["listing_title"] ?? "Listing").toString();

                    return Card(
                      margin: const EdgeInsets.fromLTRB(12, 8, 12, 0),
                      child: ListTile(
                        title: Text("$listingTitle  •  ₦$amount", style: const TextStyle(fontWeight: FontWeight.w900)),
                        subtitle: Text("Status: $status"),
                        trailing: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            TextButton(
                              onPressed: () {
                                final listingId = int.tryParse((m["listing_id"] ?? "").toString());
                                if (listingId == null) return;
                                final listing = <String, dynamic>{
                                  "id": listingId,
                                  "owner_id": m["merchant_id"],
                                  "title": listingTitle,
                                  "price": m["amount"],
                                };
                                Navigator.push(context, MaterialPageRoute(builder: (_) => ListingDetailScreen(listing: listing)));
                              },
                              child: const Text("Reorder"),
                            ),
                            const Icon(Icons.chevron_right),
                          ],
                        ),
                        onTap: () {
                          Navigator.push(context, MaterialPageRoute(builder: (_) => OrderDetailScreen(orderId: id)));
                        },
                      ),
                    );
                  },
                ),
    );
  }
}

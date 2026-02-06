import 'package:flutter/material.dart';

import '../services/leaderboard_service.dart';
import 'merchant_detail_screen.dart';

class LeaderboardsScreen extends StatefulWidget {
  const LeaderboardsScreen({super.key});

  @override
  State<LeaderboardsScreen> createState() => _LeaderboardsScreenState();
}

class _LeaderboardsScreenState extends State<LeaderboardsScreen> {
  final _svc = LeaderboardService();

  late Future<List<dynamic>> _featured;
  late Future<Map<String, dynamic>> _states;
  late Future<Map<String, dynamic>> _cities;

  @override
  void initState() {
    super.initState();
    _featured = _svc.featured();
    _states = _svc.byStates(limit: 10);
    _cities = _svc.byCities(limit: 10);
  }

  void _reload() {
    setState(() {
      _featured = _svc.featured();
      _states = _svc.byStates(limit: 10);
      _cities = _svc.byCities(limit: 10);
    });
  }

  Widget _merchantTile(Map<String, dynamic> m) {
    final uid = int.tryParse((m['user_id'] ?? '').toString()) ?? 0;
    final name = (m['shop_name'] ?? '').toString().trim().isEmpty ? 'Merchant $uid' : (m['shop_name'] ?? '').toString();
    final badge = (m['badge'] ?? 'New').toString();
    final score = (m['score'] ?? 0).toString();
    final city = (m['city'] ?? '').toString();
    final state = (m['state'] ?? '').toString();

    return ListTile(
      leading: CircleAvatar(child: Text(name.isNotEmpty ? name[0].toUpperCase() : 'M')),
      title: Text(name, style: const TextStyle(fontWeight: FontWeight.w900)),
      subtitle: Text('$badge - Score $score\n$city, $state'),
      isThreeLine: true,
      onTap: uid > 0
          ? () => Navigator.push(context, MaterialPageRoute(builder: (_) => MerchantDetailScreen(userId: uid)))
          : null,
    );
  }

  Widget _sectionTitle(String t) => Padding(
        padding: const EdgeInsets.fromLTRB(16, 14, 16, 8),
        child: Text(t, style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 16)),
      );

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Leaderboards'),
        actions: [
          IconButton(onPressed: _reload, icon: const Icon(Icons.refresh)),
        ],
      ),
      body: DefaultTabController(
        length: 3,
        child: Column(
          children: [
            const TabBar(
              tabs: [
                Tab(text: 'Featured'),
                Tab(text: 'States'),
                Tab(text: 'Cities'),
              ],
            ),
            Expanded(
              child: TabBarView(
                children: [
                  RefreshIndicator(
                    onRefresh: () async => _reload(),
                    child: FutureBuilder<List<dynamic>>(
                      future: _featured,
                      builder: (context, snap) {
                        if (snap.connectionState == ConnectionState.waiting) {
                          return const Center(child: CircularProgressIndicator());
                        }
                        final items = snap.data ?? const [];
                        if (items.isEmpty) {
                          return ListView(
                            physics: const AlwaysScrollableScrollPhysics(),
                            padding: const EdgeInsets.all(16),
                            children: const [SizedBox(height: 120), Center(child: Text('No featured merchants yet.'))],
                          );
                        }
                        return ListView.builder(
                          physics: const AlwaysScrollableScrollPhysics(),
                          itemCount: items.length,
                          itemBuilder: (_, i) {
                            final raw = items[i];
                            if (raw is! Map) return const SizedBox.shrink();
                            return Card(child: _merchantTile(Map<String, dynamic>.from(raw as Map)));
                          },
                        );
                      },
                    ),
                  ),
                  RefreshIndicator(
                    onRefresh: () async => _reload(),
                    child: FutureBuilder<Map<String, dynamic>>(
                      future: _states,
                      builder: (context, snap) {
                        if (snap.connectionState == ConnectionState.waiting) {
                          return const Center(child: CircularProgressIndicator());
                        }
                        final items = snap.data ?? {};
                        if (items.isEmpty) {
                          return ListView(
                            physics: const AlwaysScrollableScrollPhysics(),
                            padding: const EdgeInsets.all(16),
                            children: const [SizedBox(height: 120), Center(child: Text('No state data yet.'))],
                          );
                        }
                        final keys = items.keys.toList()..sort();
                        return ListView(
                          physics: const AlwaysScrollableScrollPhysics(),
                          children: [
                            for (final st in keys) ...[
                              _sectionTitle(st),
                              ...((items[st] is List) ? (items[st] as List) : const []).whereType<Map>().map(
                                    (raw) => Card(child: _merchantTile(Map<String, dynamic>.from(raw))),
                                  ),
                            ]
                          ],
                        );
                      },
                    ),
                  ),
                  RefreshIndicator(
                    onRefresh: () async => _reload(),
                    child: FutureBuilder<Map<String, dynamic>>(
                      future: _cities,
                      builder: (context, snap) {
                        if (snap.connectionState == ConnectionState.waiting) {
                          return const Center(child: CircularProgressIndicator());
                        }
                        final items = snap.data ?? {};
                        if (items.isEmpty) {
                          return ListView(
                            physics: const AlwaysScrollableScrollPhysics(),
                            padding: const EdgeInsets.all(16),
                            children: const [SizedBox(height: 120), Center(child: Text('No city data yet.'))],
                          );
                        }
                        final keys = items.keys.toList()..sort();
                        return ListView(
                          physics: const AlwaysScrollableScrollPhysics(),
                          children: [
                            for (final key in keys) ...[
                              _sectionTitle(key.replaceAll('|', ' - ')),
                              ...((items[key] is List) ? (items[key] as List) : const []).whereType<Map>().map(
                                    (raw) => Card(child: _merchantTile(Map<String, dynamic>.from(raw))),
                                  ),
                            ]
                          ],
                        );
                      },
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

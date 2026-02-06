import 'package:flutter/material.dart';

import '../services/admin_role_service.dart';

class AdminRoleApprovalsScreen extends StatefulWidget {
  const AdminRoleApprovalsScreen({super.key});

  @override
  State<AdminRoleApprovalsScreen> createState() => _AdminRoleApprovalsScreenState();
}

class _AdminRoleApprovalsScreenState extends State<AdminRoleApprovalsScreen> {
  final _svc = AdminRoleService();
  late Future<List<dynamic>> _items;
  bool _busy = false;

  @override
  void initState() {
    super.initState();
    _items = _svc.pending();
  }

  void _reload() {
    setState(() => _items = _svc.pending());
  }

  Future<void> _approve(Map<String, dynamic> item) async {
    if (_busy) return;
    setState(() => _busy = true);
    final ok = await _svc.approve(userId: item['id'] as int?, email: item['email']?.toString());
    if (!mounted) return;
    setState(() => _busy = false);
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(ok ? 'Approved' : 'Approve failed')));
    if (ok) _reload();
  }

  Future<void> _reject(Map<String, dynamic> item) async {
    if (_busy) return;
    setState(() => _busy = true);
    final ok = await _svc.reject(userId: item['id'] as int?, email: item['email']?.toString());
    if (!mounted) return;
    setState(() => _busy = false);
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(ok ? 'Rejected' : 'Reject failed')));
    if (ok) _reload();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Role Approvals'),
        actions: [IconButton(onPressed: _busy ? null : _reload, icon: const Icon(Icons.refresh))],
      ),
      body: FutureBuilder<List<dynamic>>(
        future: _items,
        builder: (context, snap) {
          if (snap.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          final items = snap.data ?? const [];
          if (items.isEmpty) {
            return const Center(child: Text('No pending approvals.'));
          }
          return ListView.builder(
            itemCount: items.length,
            itemBuilder: (_, i) {
              final raw = items[i];
              if (raw is! Map) return const SizedBox.shrink();
              final item = Map<String, dynamic>.from(raw as Map);
              final email = (item['email'] ?? '').toString();
              final role = (item['role'] ?? '').toString();
              final roleStatus = (item['role_status'] ?? '').toString();

              return Card(
                margin: const EdgeInsets.fromLTRB(12, 10, 12, 0),
                child: ListTile(
                  title: Text(email.isEmpty ? 'User #${item['id']}' : email),
                  subtitle: Text('Role: $role  ?  Status: $roleStatus'),
                  trailing: Wrap(
                    spacing: 8,
                    children: [
                      OutlinedButton(
                        onPressed: _busy ? null : () => _reject(item),
                        child: const Text('Reject'),
                      ),
                      ElevatedButton(
                        onPressed: _busy ? null : () => _approve(item),
                        child: const Text('Approve'),
                      ),
                    ],
                  ),
                ),
              );
            },
          );
        },
      ),
    );
  }
}

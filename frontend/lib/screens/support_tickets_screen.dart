import 'package:flutter/material.dart';

import '../services/support_service.dart';

class SupportTicketsScreen extends StatefulWidget {
  const SupportTicketsScreen({super.key});

  @override
  State<SupportTicketsScreen> createState() => _SupportTicketsScreenState();
}

class _SupportTicketsScreenState extends State<SupportTicketsScreen> {
  final _svc = SupportService();

  late Future<List<dynamic>> _items;

  @override
  void initState() {
    super.initState();
    _items = _svc.listTickets();
  }

  void _reload() {
    setState(() => _items = _svc.listTickets());
  }

  Future<void> _newTicket() async {
    final subjectCtrl = TextEditingController();
    final msgCtrl = TextEditingController();

    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('New ticket'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: subjectCtrl,
                decoration: const InputDecoration(labelText: 'Subject', border: OutlineInputBorder()),
              ),
              const SizedBox(height: 10),
              TextField(
                controller: msgCtrl,
                minLines: 4,
                maxLines: 6,
                decoration: const InputDecoration(labelText: 'Message', border: OutlineInputBorder()),
              ),
            ],
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancel')),
          ElevatedButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Submit')),
        ],
      ),
    );

    if (ok != true) return;

    final subject = subjectCtrl.text.trim();
    final message = msgCtrl.text.trim();
    if (subject.isEmpty || message.isEmpty) return;

    await _svc.createTicket(subject: subject, message: message);
    if (!mounted) return;
    _reload();
    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Ticket created ✅')));
  }

  Widget _chip(String status) {
    final s = status.toLowerCase();
    IconData icon = Icons.flag_outlined;
    if (s == 'resolved') icon = Icons.check_circle_outline;
    if (s == 'in_progress') icon = Icons.autorenew;
    if (s == 'closed') icon = Icons.lock_outline;

    return Chip(
      avatar: Icon(icon, size: 16),
      label: Text(status),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Help & Disputes'),
        actions: [
          IconButton(onPressed: _reload, icon: const Icon(Icons.refresh)),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _newTicket,
        child: const Icon(Icons.add),
      ),
      body: FutureBuilder<List<dynamic>>(
        future: _items,
        builder: (context, snap) {
          if (snap.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          final items = snap.data ?? const [];
          if (items.isEmpty) {
            return const Center(child: Text('No tickets yet. Tap + to create one.'));
          }

          return ListView.builder(
            itemCount: items.length,
            itemBuilder: (_, i) {
              final raw = items[i];
              if (raw is! Map) return const SizedBox.shrink();
              final m = Map<String, dynamic>.from(raw as Map);

              return Card(
                margin: const EdgeInsets.fromLTRB(12, 10, 12, 0),
                child: ListTile(
                  title: Text((m['subject'] ?? '').toString(), style: const TextStyle(fontWeight: FontWeight.w900)),
                  subtitle: Text((m['message'] ?? '').toString(), maxLines: 2, overflow: TextOverflow.ellipsis),
                  trailing: _chip((m['status'] ?? 'open').toString()),
                  onTap: () {
                    showDialog(
                      context: context,
                      builder: (_) => AlertDialog(
                        title: Text((m['subject'] ?? '').toString()),
                        content: Text((m['message'] ?? '').toString()),
                        actions: [
                          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Close')),
                        ],
                      ),
                    );
                  },
                ),
              );
            },
          );
        },
      ),
    );
  }
}

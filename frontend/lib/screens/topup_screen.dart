import 'package:flutter/material.dart';

import '../services/topup_service.dart';

class TopupScreen extends StatefulWidget {
  const TopupScreen({super.key});

  @override
  State<TopupScreen> createState() => _TopupScreenState();
}

class _TopupScreenState extends State<TopupScreen> {
  final _svc = TopupService();
  final _amount = TextEditingController(text: "1000");
  bool _loading = false;
  String _ref = "";
  String _url = "";

  void _toast(String m) => ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(m)));

  Future<void> _init() async {
    setState(() => _loading = true);
    try {
      final amt = double.tryParse(_amount.text.trim()) ?? 0;
      if (amt <= 0) {
        _toast("Enter a valid amount");
        return;
      }
      final r = await _svc.initialize(amt);
      setState(() {
        _ref = (r['reference'] ?? '').toString();
        _url = (r['authorization_url'] ?? '').toString();
      });
      _toast("Initialized. Ref: $_ref");
    } catch (e) {
      _toast("Init error: $e");
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  void dispose() {
    _amount.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Top up Wallet")),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            TextField(
              controller: _amount,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(border: OutlineInputBorder(), labelText: "Amount (NGN)"),
            ),
            const SizedBox(height: 12),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: _loading ? null : _init,
                icon: _loading ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2)) : const Icon(Icons.payments_outlined),
                label: const Text("Initialize Payment"),
              ),
            ),
            const SizedBox(height: 16),
            if (_ref.isNotEmpty) Text("Reference: $_ref"),
            if (_url.isNotEmpty) Text("Pay URL: $_url"),
            const SizedBox(height: 10),
            const Text("Note: Wallet is credited on webhook confirmation (Paystack) or in demo mode."),
          ],
        ),
      ),
    );
  }
}

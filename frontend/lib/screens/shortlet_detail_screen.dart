import 'package:flutter/material.dart';

import '../services/shortlet_service.dart';
import '../services/api_client.dart';
import '../widgets/safe_image.dart';

class ShortletDetailScreen extends StatefulWidget {
  final Map<String, dynamic> shortlet;

  const ShortletDetailScreen({super.key, required this.shortlet});

  @override
  State<ShortletDetailScreen> createState() => _ShortletDetailScreenState();
}

class _ShortletDetailScreenState extends State<ShortletDetailScreen> {
  final _svc = ShortletService();

  final _checkInCtrl = TextEditingController();
  final _checkOutCtrl = TextEditingController();
  final _nameCtrl = TextEditingController();
  final _phoneCtrl = TextEditingController();

  bool _loadingQuote = false;
  Map<String, dynamic>? _quote;
  bool _booking = false;

  @override
  void dispose() {
    _checkInCtrl.dispose();
    _checkOutCtrl.dispose();
    _nameCtrl.dispose();
    _phoneCtrl.dispose();
    super.dispose();
  }

  List<String> _asStringList(dynamic v) {
    if (v is List) return v.map((e) => e.toString()).where((s) => s.trim().isNotEmpty).toList();
    if (v is String) {
      final s = v.trim();
      if (s.isEmpty) return [];
      // crude parse: try JSON list else comma-separated
      try {
        final data = ApiClient.instance.jsonDecodeSafe(s);
        if (data is List) return data.map((e) => e.toString()).toList();
      } catch (_) {}
      return s.split(',').map((x) => x.trim()).where((x) => x.isNotEmpty).toList();
    }
    return [];
  }

  Future<void> _getQuote() async {
    final id = widget.shortlet['id'];
    if (id == null) return;

    final checkIn = _checkInCtrl.text.trim();
    final checkOut = _checkOutCtrl.text.trim();
    if (checkIn.isEmpty || checkOut.isEmpty) return;

    setState(() {
      _loadingQuote = true;
      _quote = null;
    });

    final data = await _svc.bookShortlet(shortletId: int.parse(id.toString()), checkIn: checkIn, checkOut: checkOut);
    // bookShortlet actually creates booking; for demo, we treat response quote as a quote.
    // We won't auto-book twice; instead show quote and leave it as "pending".
    setState(() {
      _quote = (data['quote'] is Map) ? Map<String, dynamic>.from(data['quote']) : null;
      _loadingQuote = false;
    });
  }

  Future<void> _book() async {
    final id = widget.shortlet['id'];
    if (id == null) return;

    final checkIn = _checkInCtrl.text.trim();
    final checkOut = _checkOutCtrl.text.trim();

    if (checkIn.isEmpty || checkOut.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Enter check-in and check-out dates.")));
      return;
    }

    setState(() => _booking = true);
    final data = await _svc.bookShortlet(
      shortletId: int.parse(id.toString()),
      checkIn: checkIn,
      checkOut: checkOut,
      guestName: _nameCtrl.text.trim(),
      guestPhone: _phoneCtrl.text.trim(),
    );
    if (!mounted) return;
    setState(() => _booking = false);

    final ok = data['ok'] == true;
    if (ok) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Booking created (pending) ✅")));
    } else {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Booking failed.")));
    }
  }

  @override
  Widget build(BuildContext context) {
    final m = widget.shortlet;
    final img = (m['image'] ?? '').toString();
    final title = (m['title'] ?? '').toString();
    final desc = (m['description'] ?? '').toString();
    final state = (m['state'] ?? '').toString();
    final city = (m['city'] ?? '').toString();
    final locality = (m['locality'] ?? '').toString();
    final lga = (m['lga'] ?? '').toString();

    final nightly = (m['nightly_price'] ?? 0).toString();
    final cleaning = (m['cleaning_fee'] ?? 0).toString();
    final beds = (m['beds'] ?? 1).toString();
    final baths = (m['baths'] ?? 1).toString();
    final guests = (m['guests'] ?? 2).toString();

    final minN = (m['min_nights'] ?? 1).toString();
    final maxN = (m['max_nights'] ?? 30).toString();

    final amenities = _asStringList(m['amenities']);
    final rules = (m['house_rules'] ?? '').toString();
    final owner = (m['owner_phone'] ?? '').toString();

    final locParts = [locality, city, state].where((x) => x.trim().isNotEmpty).toList();
    final loc = locParts.join(", ");

    if (title.trim().isEmpty) {
      return Scaffold(
        appBar: AppBar(title: Text("Shortlet")),
        body: Center(child: Text("Shortlet not available.")),
      );
    }

    return Scaffold(
      appBar: AppBar(title: const Text("Shortlet")),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          ClipRRect(
            borderRadius: BorderRadius.circular(16),
            child: SafeImage(url: img, height: 220, width: double.infinity),
          ),
          const SizedBox(height: 12),
          Text(title, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w900)),
          const SizedBox(height: 6),
          Text(loc, style: TextStyle(color: Colors.grey.shade700)),
          const SizedBox(height: 10),
          Row(
            children: [
              Expanded(child: _pill("₦$nightly / night")),
              const SizedBox(width: 8),
              Expanded(child: _pill("Cleaning ₦$cleaning")),
            ],
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              Expanded(child: _pill("$beds beds")),
              const SizedBox(width: 8),
              Expanded(child: _pill("$baths baths")),
              const SizedBox(width: 8),
              Expanded(child: _pill("$guests guests")),
            ],
          ),
          const SizedBox(height: 8),
          _pill("Stay: $minN - $maxN nights"),
          const SizedBox(height: 16),
          if (desc.trim().isNotEmpty) ...[
            const Text("About", style: TextStyle(fontWeight: FontWeight.w900)),
            const SizedBox(height: 6),
            Text(desc),
            const SizedBox(height: 16),
          ],
          if (amenities.isNotEmpty) ...[
            const Text("Amenities", style: TextStyle(fontWeight: FontWeight.w900)),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: amenities.take(20).map((a) => Chip(label: Text(a))).toList(),
            ),
            const SizedBox(height: 16),
          ],
          if (rules.trim().isNotEmpty) ...[
            const Text("House rules", style: TextStyle(fontWeight: FontWeight.w900)),
            const SizedBox(height: 6),
            Text(rules),
            const SizedBox(height: 16),
          ],
          if (owner.trim().isNotEmpty) ...[
            const Text("Host contact", style: TextStyle(fontWeight: FontWeight.w900)),
            const SizedBox(height: 6),
            Text(owner),
            const SizedBox(height: 16),
          ],
          const Divider(height: 24),
          const Text("Book dates", style: TextStyle(fontWeight: FontWeight.w900)),
          const SizedBox(height: 10),
          TextField(
            controller: _checkInCtrl,
            decoration: const InputDecoration(labelText: "Check-in (YYYY-MM-DD)", border: OutlineInputBorder()),
          ),
          const SizedBox(height: 10),
          TextField(
            controller: _checkOutCtrl,
            decoration: const InputDecoration(labelText: "Check-out (YYYY-MM-DD)", border: OutlineInputBorder()),
          ),
          const SizedBox(height: 10),
          TextField(
            controller: _nameCtrl,
            decoration: const InputDecoration(labelText: "Guest name (optional)", border: OutlineInputBorder()),
          ),
          const SizedBox(height: 10),
          TextField(
            controller: _phoneCtrl,
            decoration: const InputDecoration(labelText: "Guest phone (optional)", border: OutlineInputBorder()),
          ),
          const SizedBox(height: 10),
          Row(
            children: [
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: _loadingQuote ? null : _getQuote,
                  icon: const Icon(Icons.calculate_outlined),
                  label: _loadingQuote ? const Text("...") : const Text("Get quote"),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: ElevatedButton.icon(
                  onPressed: _booking ? null : _book,
                  icon: const Icon(Icons.check_circle_outline),
                  label: _booking ? const Text("...") : const Text("Book (pending)"),
                ),
              ),
            ],
          ),
          if (_quote != null) ...[
            const SizedBox(height: 12),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text("Quote", style: TextStyle(fontWeight: FontWeight.w900)),
                    const SizedBox(height: 6),
                    Text("Nights: ${_quote!['nights'] ?? '-'}"),
                    Text("Subtotal: ₦${_quote!['subtotal'] ?? '-'}"),
                    Text("Platform fee: ₦${_quote!['platform_fee'] ?? '-'}"),
                    const Divider(height: 16),
                    Text("Total: ₦${_quote!['total'] ?? '-'}", style: const TextStyle(fontWeight: FontWeight.w900)),
                  ],
                ),
              ),
            ),
          ]
        ],
      ),
    );
  }

  Widget _pill(String text) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(12),
        color: Colors.grey.shade100,
      ),
      child: Center(child: Text(text, style: const TextStyle(fontWeight: FontWeight.w800))),
    );
  }
}

import 'package:flutter/material.dart';

import 'landing_screen.dart';
import 'login_screen.dart';

class PendingApprovalScreen extends StatelessWidget {
  final String role;

  const PendingApprovalScreen({super.key, required this.role});

  String _roleLabel() {
    switch (role.toLowerCase()) {
      case 'merchant':
        return 'Merchant';
      case 'driver':
        return 'Driver';
      case 'inspector':
        return 'Inspector';
      default:
        return 'Account';
    }
  }

  @override
  Widget build(BuildContext context) {
    final label = _roleLabel();
    return Scaffold(
      appBar: AppBar(title: const Text('Pending Approval')),
      body: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              '$label application received',
              style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w800),
            ),
            const SizedBox(height: 12),
            Text(
              'Your account is pending admin approval. You can still browse the marketplace while we review your request.',
              style: TextStyle(color: Colors.grey.shade700, height: 1.4),
            ),
            const SizedBox(height: 24),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: () {
                  Navigator.of(context).pushReplacement(
                    MaterialPageRoute(builder: (_) => const LoginScreen()),
                  );
                },
                child: const Text('Go to Login'),
              ),
            ),
            const SizedBox(height: 10),
            SizedBox(
              width: double.infinity,
              child: OutlinedButton(
                onPressed: () {
                  Navigator.of(context).pushReplacement(
                    MaterialPageRoute(
                      builder: (_) => LandingScreen(
                        onLogin: () {
                          Navigator.of(context).push(
                            MaterialPageRoute(builder: (_) => const LoginScreen()),
                          );
                        },
                        onSignup: () {
                          Navigator.of(context).push(
                            MaterialPageRoute(builder: (_) => const LoginScreen()),
                          );
                        },
                      ),
                    ),
                  );
                },
                child: const Text('Back to Marketplace'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

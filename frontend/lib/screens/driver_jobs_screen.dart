import 'package:flutter/material.dart';

import '../services/api_service.dart';
import '../services/token_storage.dart';
import 'landing_screen.dart';
import 'login_screen.dart';
import 'moneybox_dashboard_screen.dart';
import 'role_signup_screen.dart';

class DriverJobsScreen extends StatefulWidget {
  const DriverJobsScreen({super.key});

  @override
  State<DriverJobsScreen> createState() => _DriverJobsScreenState();
}

class _DriverJobsScreenState extends State<DriverJobsScreen> {
  bool _signingOut = false;

  Future<bool> _confirmSignOut() async {
    final res = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Sign out'),
        content: const Text('Are you sure you want to sign out?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: const Text('Sign out'),
          ),
        ],
      ),
    );
    return res ?? false;
  }

  void _goToLanding() {
    Navigator.of(context).pushAndRemoveUntil(
      MaterialPageRoute(
        builder: (_) => LandingScreen(
          onLogin: () {
            Navigator.of(context).push(
              MaterialPageRoute(builder: (_) => const LoginScreen()),
            );
          },
          onSignup: () {
            Navigator.of(context).push(
              MaterialPageRoute(builder: (_) => const RoleSignupScreen()),
            );
          },
        ),
      ),
      (_) => false,
    );
  }

  Future<void> _handleSignOut() async {
    if (_signingOut) return;
    final confirmed = await _confirmSignOut();
    if (!confirmed) return;
    setState(() => _signingOut = true);
    try {
      await TokenStorage().clear();
      ApiService.setToken(null);
      ApiService.lastMeStatusCode = null;
      ApiService.lastMeAt = null;
      ApiService.lastAuthError = null;
    } finally {
      if (mounted) {
        setState(() => _signingOut = false);
      }
    }
    if (!mounted) return;
    _goToLanding();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Driver Jobs'),
        actions: [
          TextButton(
            onPressed: _signingOut ? null : _handleSignOut,
            child: Text(
              _signingOut ? 'Signing out...' : 'Sign out',
              style: const TextStyle(fontWeight: FontWeight.w600),
            ),
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Card(
            child: ListTile(
              leading: const Icon(Icons.savings_outlined),
              title: const Text('MoneyBox'),
              subtitle: const Text('Save from commission earnings'),
              trailing: const Icon(Icons.chevron_right),
              onTap: () => Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const MoneyBoxDashboardScreen()),
              ),
            ),
          ),
          const SizedBox(height: 10),
          const Card(
            child: ListTile(
              leading: Icon(Icons.local_shipping_outlined),
              title: Text('Jobs'),
              subtitle: Text('Assignments will appear here once approved'),
            ),
          ),
        ],
      ),
    );
  }
}

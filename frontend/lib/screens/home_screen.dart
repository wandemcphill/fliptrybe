import 'package:flutter/material.dart';

import '../services/api_service.dart';
import '../services/token_storage.dart';
import 'landing_screen.dart';
import 'login_screen.dart';
import 'role_signup_screen.dart';

import 'marketplace_screen.dart';
import 'shortlet_screen.dart';
import 'profile_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _tab = 0;

  Future<void> _handleLogout() async {
    await TokenStorage().clear();
    ApiService.setToken(null);
    ApiService.lastMeStatusCode = null;
    ApiService.lastMeAt = null;
    ApiService.lastAuthError = null;

    if (!mounted) return;
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
      (route) => false,
    );
  }

  final _pages = const [
    MarketplaceScreen(),
    ShortletScreen(),
    ProfileScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('FlipTrybe', style: TextStyle(color: Colors.white)),
        backgroundColor: Colors.black,
        actions: [
          IconButton(
            icon: const Icon(Icons.logout, color: Colors.redAccent),
            onPressed: _handleLogout,
            tooltip: 'Sign out',
          ),
        ],
      ),
      body: IndexedStack(
        index: _tab,
        children: _pages,
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _tab,
        onDestinationSelected: (i) => setState(() => _tab = i),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.storefront_outlined), label: 'Marketplace'),
          NavigationDestination(icon: Icon(Icons.apartment_outlined), label: 'Short-let'),
          NavigationDestination(icon: Icon(Icons.person_outline), label: 'Profile'),
        ],
      ),
    );
  }
}

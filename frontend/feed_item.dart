import 'package:flutter/material.dart';

class FeedItem extends StatelessWidget {
  final Map<String, dynamic> listing;

  const FeedItem({super.key, required this.listing});

  @override
  Widget build(BuildContext context) {
    // Safety check for missing images
    final String imageUrl = listing['image'] ?? 'https://via.placeholder.com/400x300';
    final bool isSponsored = listing['sponsored'] == true;

    return Container(
      margin: const EdgeInsets.only(bottom: 20),
      decoration: BoxDecoration(
        color: const Color(0xFF1E1E1E), // Dark card background
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(color: Colors.black.withOpacity(0.5), blurRadius: 10, offset: const Offset(0, 5))
        ],
        border: isSponsored 
            ? Border.all(color: Colors.amber, width: 2) // Gold border for Ads
            : null,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 1. IMAGE HEADER
          Stack(
            children: [
              ClipRRect(
                borderRadius: const BorderRadius.vertical(top: Radius.circular(16)),
                child: Image.network(
                  imageUrl,
                  height: 200,
                  width: double.infinity,
                  fit: BoxFit.cover,
                  errorBuilder: (c, e, s) => Container(height: 200, color: Colors.grey[900]),
                ),
              ),
              // Trust Score Badge (Top Right)
              Positioned(
                top: 10,
                right: 10,
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                  decoration: BoxDecoration(
                    color: Colors.black.withOpacity(0.8),
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.verified_user, color: Color(0xFF00C853), size: 14),
                      const SizedBox(width: 5),
                      Text(
                        "${listing['trust_score'] ?? '98'}% Trust",
                        style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 12),
                      ),
                    ],
                  ),
                ),
              ),
              if (isSponsored)
                Positioned(
                  top: 10,
                  left: 10,
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    color: Colors.amber,
                    child: const Text("PROMOTED", style: TextStyle(color: Colors.black, fontSize: 10, fontWeight: FontWeight.bold)),
                  ),
                ),
            ],
          ),

          // 2. DETAILS
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  listing['title'] ?? "Unknown Item",
                  style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 5),
                Text(
                  "₦${listing['price']?.toString() ?? '0.00'}",
                  style: const TextStyle(color: Color(0xFF00C853), fontSize: 20, fontWeight: FontWeight.bold), // Green Price
                ),
                const SizedBox(height: 10),
                Row(
                  children: [
                    Icon(Icons.location_on, color: Colors.grey[500], size: 14),
                    const SizedBox(width: 4),
                    Text(
                      listing['location'] ?? "Lagos, NG",
                      style: TextStyle(color: Colors.grey[500], fontSize: 14),
                    ),
                    const Spacer(),
                    // Buy Button
                    ElevatedButton(
                      onPressed: () {
                        // TODO: Open Product Details
                      },
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.white,
                        foregroundColor: Colors.black,
                        shape: const StadiumBorder(),
                      ),
                      child: const Text("View"),
                    )
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
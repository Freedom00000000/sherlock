import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../models/check_result.dart';

class ResultTile extends StatelessWidget {
  final CheckResult result;
  const ResultTile({super.key, required this.result});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      child: Material(
        color: const Color(0xFF2A2A3E),
        borderRadius: BorderRadius.circular(14),
        child: InkWell(
          borderRadius: BorderRadius.circular(14),
          onTap: _open,
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 13),
            child: Row(
              children: [
                _icon(),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        result.siteName,
                        style: const TextStyle(
                          color: Colors.white,
                          fontWeight: FontWeight.w600,
                          fontSize: 15,
                        ),
                      ),
                      const SizedBox(height: 3),
                      Text(
                        result.url,
                        style: const TextStyle(
                          color: Color(0xFF7C3AED),
                          fontSize: 12,
                        ),
                        overflow: TextOverflow.ellipsis,
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 8),
                Icon(
                  Icons.open_in_new_rounded,
                  size: 16,
                  color: Colors.white.withOpacity(0.25),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _icon() {
    return Container(
      width: 38,
      height: 38,
      decoration: BoxDecoration(
        color: const Color(0xFF22C55E).withOpacity(0.15),
        borderRadius: BorderRadius.circular(10),
      ),
      child: const Icon(Icons.check_rounded, color: Color(0xFF22C55E), size: 20),
    );
  }

  Future<void> _open() async {
    final uri = Uri.tryParse(result.url);
    if (uri != null) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    }
  }
}

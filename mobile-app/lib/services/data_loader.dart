import 'dart:convert';
import 'package:flutter/services.dart';
import '../models/site_info.dart';

class DataLoader {
  static List<SiteInfo>? _cache;

  static Future<List<SiteInfo>> loadSites({bool includeNsfw = false}) async {
    if (_cache == null) {
      final raw = await rootBundle.loadString('assets/data.json');
      final map = json.decode(raw) as Map<String, dynamic>;
      map.remove('\$schema');

      _cache = map.entries
          .where((e) => e.value is Map<String, dynamic>)
          .map((e) =>
              SiteInfo.fromJson(e.key, e.value as Map<String, dynamic>))
          .toList();
    }

    return includeNsfw ? _cache! : _cache!.where((s) => !s.isNSFW).toList();
  }
}

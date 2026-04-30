import 'dart:async';
import 'package:flutter/material.dart';
import 'package:share_plus/share_plus.dart';
import '../models/check_result.dart';
import '../models/site_info.dart';
import '../services/data_loader.dart';
import '../services/search_service.dart';
import '../widgets/result_tile.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final _inputCtrl = TextEditingController();
  final _scrollCtrl = ScrollController();
  final _searchSvc = SearchService();

  List<SiteInfo> _sites = [];
  List<CheckResult> _results = [];
  StreamSubscription<CheckResult>? _sub;

  bool _loading = true;
  bool _searching = false;
  bool _includeNsfw = false;
  int _total = 0;
  int _checked = 0;

  @override
  void initState() {
    super.initState();
    _initSites();
  }

  Future<void> _initSites() async {
    _sites = await DataLoader.loadSites(includeNsfw: true);
    if (mounted) setState(() => _loading = false);
  }

  // ── Search ─────────────────────────────────────────────────────────────────

  Future<void> _startSearch() async {
    final username = _inputCtrl.text.trim();
    if (username.isEmpty || _searching) return;
    FocusScope.of(context).unfocus();

    final sites = _includeNsfw ? _sites : _sites.where((s) => !s.isNSFW).toList();

    setState(() {
      _searching = true;
      _results.clear();
      _total = sites.length;
      _checked = 0;
    });

    _sub = _searchSvc.search(username, sites).listen(
      (result) {
        if (!mounted) return;
        setState(() {
          _results.add(result);
          _checked++;
        });
        if (result.status == ResultStatus.found) {
          _scrollCtrl.animateTo(
            _scrollCtrl.position.maxScrollExtent,
            duration: const Duration(milliseconds: 300),
            curve: Curves.easeOut,
          );
        }
      },
      onDone: () {
        if (mounted) setState(() => _searching = false);
      },
    );
  }

  void _stopSearch() {
    _sub?.cancel();
    _searchSvc.stop();
    setState(() => _searching = false);
  }

  // ── Export / Share ─────────────────────────────────────────────────────────

  void _share() {
    final found = _results.where((r) => r.status == ResultStatus.found).toList();
    if (found.isEmpty) return;
    final username = _inputCtrl.text.trim();
    final buf = StringBuffer('Sherlock results for: $username\n\n');
    for (final r in found) {
      buf.writeln('[+] ${r.siteName}');
      buf.writeln('    ${r.url}');
      buf.writeln();
    }
    Share.share(buf.toString(), subject: 'Sherlock – $username');
  }

  // ── Settings bottom sheet ──────────────────────────────────────────────────

  void _showSettings() {
    showModalBottomSheet(
      context: context,
      backgroundColor: const Color(0xFF2A2A3E),
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (_) => StatefulBuilder(
        builder: (ctx, setSheet) => Padding(
          padding: const EdgeInsets.fromLTRB(24, 20, 24, 32),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Center(
                child: Container(
                  width: 40, height: 4,
                  decoration: BoxDecoration(
                    color: Colors.white24,
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              ),
              const SizedBox(height: 20),
              const Text(
                'Settings',
                style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 16),
              SwitchListTile(
                contentPadding: EdgeInsets.zero,
                title: const Text('Include NSFW sites', style: TextStyle(color: Colors.white)),
                subtitle: Text(
                  'Show results from adult platforms',
                  style: TextStyle(color: Colors.white.withOpacity(0.5), fontSize: 12),
                ),
                value: _includeNsfw,
                activeColor: const Color(0xFF7C3AED),
                onChanged: (v) {
                  setSheet(() {});
                  setState(() => _includeNsfw = v);
                },
              ),
              const Divider(color: Colors.white12),
              ListTile(
                contentPadding: EdgeInsets.zero,
                leading: const Icon(Icons.info_outline, color: Colors.white38),
                title: Text(
                  '${_sites.length} sites in database',
                  style: TextStyle(color: Colors.white.withOpacity(0.6), fontSize: 13),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  // ── Build ──────────────────────────────────────────────────────────────────

  @override
  void dispose() {
    _inputCtrl.dispose();
    _scrollCtrl.dispose();
    _sub?.cancel();
    _searchSvc.stop();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final found = _results.where((r) => r.status == ResultStatus.found).toList();
    return Scaffold(
      backgroundColor: const Color(0xFF1E1E2E),
      body: Column(
        children: [
          _Header(
            foundCount: found.length,
            onSettings: _showSettings,
            onShare: found.isNotEmpty ? _share : null,
          ),
          _SearchBar(
            controller: _inputCtrl,
            searching: _searching,
            onSearch: _startSearch,
            onStop: _stopSearch,
          ),
          if (_searching || _checked > 0)
            _ProgressRow(checked: _checked, total: _total),
          Expanded(child: _body(found)),
        ],
      ),
    );
  }

  Widget _body(List<CheckResult> found) {
    if (_loading) {
      return const Center(
        child: CircularProgressIndicator(color: Color(0xFF7C3AED)),
      );
    }
    if (found.isEmpty) {
      return _EmptyState(siteCount: _sites.length, searching: _searching);
    }
    return ListView.builder(
      controller: _scrollCtrl,
      padding: const EdgeInsets.only(top: 8, bottom: 24),
      itemCount: found.length,
      itemBuilder: (_, i) => ResultTile(result: found[i]),
    );
  }
}

// ── Sub-widgets ────────────────────────────────────────────────────────────────

class _Header extends StatelessWidget {
  final int foundCount;
  final VoidCallback onSettings;
  final VoidCallback? onShare;

  const _Header({
    required this.foundCount,
    required this.onSettings,
    required this.onShare,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      color: const Color(0xFF7C3AED),
      padding: EdgeInsets.only(
        top: MediaQuery.of(context).padding.top + 12,
        left: 20,
        right: 12,
        bottom: 12,
      ),
      child: Row(
        children: [
          const Text('🔍', style: TextStyle(fontSize: 22)),
          const SizedBox(width: 10),
          const Expanded(
            child: Text(
              'Sherlock',
              style: TextStyle(
                color: Colors.white,
                fontSize: 20,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
          if (foundCount > 0) ...[
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
              decoration: BoxDecoration(
                color: const Color(0xFF22C55E),
                borderRadius: BorderRadius.circular(20),
              ),
              child: Text(
                'Found: $foundCount',
                style: const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.bold,
                  fontSize: 13,
                ),
              ),
            ),
            const SizedBox(width: 4),
            if (onShare != null)
              IconButton(
                icon: const Icon(Icons.share_rounded, color: Colors.white70),
                onPressed: onShare,
                tooltip: 'Share results',
              ),
          ],
          IconButton(
            icon: const Icon(Icons.tune_rounded, color: Colors.white70),
            onPressed: onSettings,
            tooltip: 'Settings',
          ),
        ],
      ),
    );
  }
}

class _SearchBar extends StatelessWidget {
  final TextEditingController controller;
  final bool searching;
  final VoidCallback onSearch;
  final VoidCallback onStop;

  const _SearchBar({
    required this.controller,
    required this.searching,
    required this.onSearch,
    required this.onStop,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      color: const Color(0xFF2A2A3E),
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 12),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              controller: controller,
              enabled: !searching,
              style: const TextStyle(color: Colors.white, fontSize: 16),
              textInputAction: TextInputAction.search,
              onSubmitted: (_) => onSearch(),
              decoration: InputDecoration(
                hintText: 'Enter username…',
                hintStyle: TextStyle(color: Colors.white.withOpacity(0.35)),
                filled: true,
                fillColor: const Color(0xFF313149),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                  borderSide: BorderSide.none,
                ),
                contentPadding:
                    const EdgeInsets.symmetric(horizontal: 16, vertical: 13),
                prefixIcon: Icon(
                  Icons.person_search_rounded,
                  color: Colors.white.withOpacity(0.4),
                ),
              ),
            ),
          ),
          const SizedBox(width: 10),
          AnimatedSwitcher(
            duration: const Duration(milliseconds: 200),
            child: searching
                ? FilledButton(
                    key: const ValueKey('stop'),
                    onPressed: onStop,
                    style: FilledButton.styleFrom(
                      backgroundColor: Colors.red[700],
                      minimumSize: const Size(52, 50),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                    child: const Icon(Icons.stop_rounded, color: Colors.white),
                  )
                : FilledButton(
                    key: const ValueKey('search'),
                    onPressed: onSearch,
                    style: FilledButton.styleFrom(
                      backgroundColor: const Color(0xFF7C3AED),
                      minimumSize: const Size(52, 50),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                    child: const Icon(Icons.search_rounded, color: Colors.white),
                  ),
          ),
        ],
      ),
    );
  }
}

class _ProgressRow extends StatelessWidget {
  final int checked;
  final int total;

  const _ProgressRow({required this.checked, required this.total});

  @override
  Widget build(BuildContext context) {
    final pct = total > 0 ? checked / total : 0.0;
    return Container(
      color: const Color(0xFF2A2A3E),
      padding: const EdgeInsets.fromLTRB(16, 0, 16, 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: pct,
              minHeight: 5,
              backgroundColor: const Color(0xFF313149),
              valueColor:
                  const AlwaysStoppedAnimation<Color>(Color(0xFF7C3AED)),
            ),
          ),
          const SizedBox(height: 5),
          Text(
            '$checked / $total sites',
            style: TextStyle(
              color: Colors.white.withOpacity(0.45),
              fontSize: 11,
              fontFamily: 'monospace',
            ),
          ),
        ],
      ),
    );
  }
}

class _EmptyState extends StatelessWidget {
  final int siteCount;
  final bool searching;

  const _EmptyState({required this.siteCount, required this.searching});

  @override
  Widget build(BuildContext context) {
    if (searching) {
      return const Center(
        child: CircularProgressIndicator(color: Color(0xFF7C3AED)),
      );
    }
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.manage_search_rounded,
              size: 72, color: Colors.white.withOpacity(0.08)),
          const SizedBox(height: 16),
          Text(
            'Search for a username',
            style: TextStyle(
                color: Colors.white.withOpacity(0.3), fontSize: 17),
          ),
          const SizedBox(height: 6),
          Text(
            '$siteCount sites will be checked',
            style: TextStyle(
                color: Colors.white.withOpacity(0.18), fontSize: 13),
          ),
        ],
      ),
    );
  }
}

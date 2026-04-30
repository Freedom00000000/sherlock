import 'dart:async';
import '../models/check_result.dart';
import '../models/site_info.dart';
import 'site_checker.dart';

class SearchService {
  static const int _concurrency = 12;

  SiteChecker? _checker;
  bool _running = false;
  StreamController<CheckResult>? _ctrl;

  Stream<CheckResult> search(String username, List<SiteInfo> sites) {
    stop();
    _running = true;
    _checker = SiteChecker();
    _ctrl = StreamController<CheckResult>();
    _run(username, sites);
    return _ctrl!.stream;
  }

  Future<void> _run(String username, List<SiteInfo> sites) async {
    final checker = _checker!;
    try {
      for (var i = 0; i < sites.length && _running; i += _concurrency) {
        final batch = sites.sublist(
          i,
          (i + _concurrency).clamp(0, sites.length),
        );

        final futures = batch.map((s) => checker.check(s, username));
        final results = await Future.wait(futures, eagerError: false);

        for (final r in results) {
          if (!_running) break;
          _ctrl?.add(r);
        }
      }
    } catch (_) {
      // Silently finish on cancellation
    } finally {
      if (!(_ctrl?.isClosed ?? true)) {
        await _ctrl?.close();
      }
      _running = false;
    }
  }

  void stop() {
    _running = false;
    if (!(_ctrl?.isClosed ?? true)) {
      _ctrl?.close();
    }
    _ctrl = null;
    _checker?.dispose();
    _checker = null;
  }
}

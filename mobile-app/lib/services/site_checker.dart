import 'dart:async';
import 'package:http/http.dart' as http;
import '../models/site_info.dart';
import '../models/check_result.dart';

class SiteChecker {
  static const _ua =
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:129.0) Gecko/20100101 Firefox/129.0';
  static const _timeout = Duration(seconds: 15);

  final http.Client _client;

  SiteChecker() : _client = http.Client();

  Future<CheckResult> check(SiteInfo site, String username) async {
    if (site.regexCheck != null) {
      final ok = RegExp(site.regexCheck!).hasMatch(username);
      if (!ok) {
        return CheckResult(
          siteName: site.name,
          url: site.url.replaceAll('{}', username),
          status: ResultStatus.notFound,
          errorMessage: 'Username format invalid for this site',
        );
      }
    }

    final targetUrl = site.url.replaceAll('{}', username);
    final probeUrl =
        (site.urlProbe ?? site.url).replaceAll('{}', username);

    final headers = <String, String>{
      'User-Agent': _ua,
      if (site.headers != null) ...site.headers!,
    };

    try {
      switch (site.errorType) {
        case 'status_code':
          return await _byStatusCode(site, targetUrl, probeUrl, headers);
        case 'message':
          return await _byMessage(site, targetUrl, probeUrl, headers);
        case 'response_url':
          return await _byResponseUrl(site, targetUrl, probeUrl, headers);
        default:
          return CheckResult(
            siteName: site.name,
            url: targetUrl,
            status: ResultStatus.error,
            errorMessage: 'Unknown errorType: ${site.errorType}',
          );
      }
    } on TimeoutException {
      return CheckResult(
        siteName: site.name,
        url: targetUrl,
        status: ResultStatus.error,
        errorMessage: 'Timeout',
      );
    } catch (e) {
      return CheckResult(
        siteName: site.name,
        url: targetUrl,
        status: ResultStatus.error,
        errorMessage: e.toString(),
      );
    }
  }

  Future<CheckResult> _byStatusCode(
    SiteInfo site,
    String targetUrl,
    String probeUrl,
    Map<String, String> headers,
  ) async {
    final res = await _client
        .head(Uri.parse(probeUrl), headers: headers)
        .timeout(_timeout);
    return CheckResult(
      siteName: site.name,
      url: targetUrl,
      status: _statusOk(res.statusCode)
          ? ResultStatus.found
          : ResultStatus.notFound,
    );
  }

  Future<CheckResult> _byMessage(
    SiteInfo site,
    String targetUrl,
    String probeUrl,
    Map<String, String> headers,
  ) async {
    final res = await _client
        .get(Uri.parse(probeUrl), headers: headers)
        .timeout(_timeout);
    final body = res.body;

    bool hasErrorMsg = false;
    final msg = site.errorMsg;
    if (msg is String) {
      hasErrorMsg = body.contains(msg);
    } else if (msg is List) {
      hasErrorMsg = msg.any((m) => body.contains(m.toString()));
    }

    return CheckResult(
      siteName: site.name,
      url: targetUrl,
      status: hasErrorMsg ? ResultStatus.notFound : ResultStatus.found,
    );
  }

  Future<CheckResult> _byResponseUrl(
    SiteInfo site,
    String targetUrl,
    String probeUrl,
    Map<String, String> headers,
  ) async {
    final res = await _client
        .get(Uri.parse(probeUrl), headers: headers)
        .timeout(_timeout);
    return CheckResult(
      siteName: site.name,
      url: targetUrl,
      status: _statusOk(res.statusCode)
          ? ResultStatus.found
          : ResultStatus.notFound,
    );
  }

  bool _statusOk(int code) => code >= 200 && code < 300;

  void dispose() => _client.close();
}

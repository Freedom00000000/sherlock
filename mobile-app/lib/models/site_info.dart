class SiteInfo {
  final String name;
  final String url;
  final String urlMain;
  final String errorType;
  final dynamic errorMsg; // String | List<dynamic>
  final String? urlProbe;
  final String? regexCheck;
  final bool isNSFW;
  final Map<String, String>? headers;

  const SiteInfo({
    required this.name,
    required this.url,
    required this.urlMain,
    required this.errorType,
    this.errorMsg,
    this.urlProbe,
    this.regexCheck,
    this.isNSFW = false,
    this.headers,
  });

  factory SiteInfo.fromJson(String name, Map<String, dynamic> json) {
    return SiteInfo(
      name: name,
      url: json['url'] as String,
      urlMain: json['urlMain'] as String,
      errorType: json['errorType'] as String,
      errorMsg: json['errorMsg'],
      urlProbe: json['urlProbe'] as String?,
      regexCheck: json['regexCheck'] as String?,
      isNSFW: (json['isNSFW'] as bool?) ?? false,
      headers: (json['headers'] as Map<String, dynamic>?)
          ?.map((k, v) => MapEntry(k, v.toString())),
    );
  }
}

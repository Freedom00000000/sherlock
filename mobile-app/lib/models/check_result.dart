enum ResultStatus { found, notFound, error }

class CheckResult {
  final String siteName;
  final String url;
  final ResultStatus status;
  final String? errorMessage;

  const CheckResult({
    required this.siteName,
    required this.url,
    required this.status,
    this.errorMessage,
  });
}

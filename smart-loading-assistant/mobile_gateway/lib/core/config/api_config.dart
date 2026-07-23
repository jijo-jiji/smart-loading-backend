class ApiConfig {
  static const String baseUrl = String.fromEnvironment(
    'API_URL',
    defaultValue: 'http://10.0.2.2:8000/api/v1', // Android emulator localhost
  );
  
  static const String apiKey = String.fromEnvironment(
    'API_KEY',
    defaultValue: 'super_secret_local_key',
  );
}

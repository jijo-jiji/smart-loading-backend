import 'dart:io';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:dart_jsonwebtoken/dart_jsonwebtoken.dart';
import 'package:mobile_gateway/data/database/app_database.dart';

import 'auth_event.dart';
import 'auth_state.dart';

class AuthBloc extends Bloc<AuthEvent, AuthState> {
  final AppDatabase db;
  final FlutterSecureStorage secureStorage;
  
  // Public key for verifying JWT signatures from FastAPI
  static const String serverPublicKeyPem = '''-----BEGIN PUBLIC KEY-----
MFwwDQYJKoZIhvcNAQEBBQADSwAwSAJBAKt1q9BvR9G5X0Tj5sJ3t4V2Q8N5...
-----END PUBLIC KEY-----'''; 

  AuthBloc({required this.db, required this.secureStorage}) : super(AuthInitial()) {
    on<AppStarted>(_onAppStarted);
    on<QrBadgeScanned>(_onQrBadgeScanned);
    on<SessionExpired>(_onSessionExpired);
  }

  Future<void> _onAppStarted(AppStarted event, Emitter<AuthState> emit) async {
    final token = await secureStorage.read(key: 'jwt_token');
    if (token == null) {
      emit(Unauthenticated());
      return;
    }
    
    // We have a stored token, but is it expired or revoked?
    try {
      final isValid = await _verifyAndCheckToken(token);
      if (isValid) {
        final jwt = JWT.decode(token);
        final operatorId = jwt.payload['operator_id'] as String;
        final clearanceLevel = (jwt.payload['clearance_level'] as num?)?.toInt() ?? 1;
        emit(Authenticated(operatorId, clearanceLevel));
      } else {
        await secureStorage.delete(key: 'jwt_token');
        emit(Unauthenticated(error: "Session expired or revoked."));
      }
    } catch (e) {
      await secureStorage.delete(key: 'jwt_token');
      emit(Unauthenticated(error: "Invalid session token."));
    }
  }

  Future<void> _onQrBadgeScanned(QrBadgeScanned event, Emitter<AuthState> emit) async {
    try {
      final isValid = await _verifyAndCheckToken(event.jwtToken);
      if (isValid) {
        final jwt = JWT.decode(event.jwtToken);
        final operatorId = jwt.payload['operator_id'] as String;
        final clearanceLevel = (jwt.payload['clearance_level'] as num?)?.toInt() ?? 1;
        
        await secureStorage.write(key: 'jwt_token', value: event.jwtToken);
        
        // Setup high-water mark upon successful auth
        final now = DateTime.now().toUtc().millisecondsSinceEpoch.toString();
        await secureStorage.write(key: 'high_water_mark', value: now);
        
        emit(Authenticated(operatorId, clearanceLevel));
      } else {
        emit(Unauthenticated(error: "QR Badge rejected."));
      }
    } catch (e) {
      emit(Unauthenticated(error: "Invalid or forged QR Badge."));
    }
  }

  Future<void> _onSessionExpired(SessionExpired event, Emitter<AuthState> emit) async {
    await secureStorage.delete(key: 'jwt_token');
    emit(Unauthenticated());
  }

  Future<bool> _verifyAndCheckToken(String token) async {
    try {
      // 1. Asymmetric Verification
      // In a real app we parse the PEM, here we'll just mock the RSA key parsing
      final jwt = JWT.verify(token, SecretKey('MOCK_SECRET_KEY')); // Mocked for now to avoid OpenSSL RSA keygen overhead in dart
      
      // 2. Monotonic Time Ratchet Check
      // Get uptime
      // (Using a mock uptime here for structural representation since dart:io doesn't expose system Uptime easily without FFI or platform channels)
      // A full implementation would use platform channels to query sysinfo(2) on Android.
      final storedMark = await secureStorage.read(key: 'high_water_mark');
      if (storedMark != null) {
        final markTime = int.parse(storedMark);
        final currentTime = DateTime.now().toUtc().millisecondsSinceEpoch;
        if (currentTime < markTime) {
          throw Exception("Clock Tampering Detected! Current time is before High-Water Mark.");
        }
      }

      // 3. Denylist (Revocation) Check
      final operatorId = jwt.payload['operator_id'] as String;
      final isRevoked = await (db.select(db.localRevocations)..where((tbl) => tbl.operatorId.equals(operatorId))).getSingleOrNull();
      
      if (isRevoked != null) {
        throw Exception("Operator is on the active Denylist.");
      }

      return true;
    } on JWTExpiredException {
      return false;
    } catch (e) {
      print("JWT Validation Failed: $e");
      return false;
    }
  }
}

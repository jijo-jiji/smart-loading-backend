import 'dart:convert';
import 'dart:math';
import 'package:http/http.dart' as http;
import 'package:drift/drift.dart';
import '../database/app_database.dart';

class SyncRepository {
  final AppDatabase db;
  final String baseUrl = 'http://127.0.0.1:8005/api/v1';
  final String apiKey = 'test_api_key_123';
  
  final Random _random = Random();

  SyncRepository(this.db);

  /// Synchronizes all PENDING outbox items to the FastAPI backend.
  /// Uses a 4-tier exponential backoff (2s, 4s, 8s, 16s) with jitter to prevent
  /// the "Thundering Herd" DDoS on the single-instance backend.
  Future<void> syncPendingOutbox() async {
    final pendingItems = await (db.select(db.localOutbox)
      ..where((tbl) => tbl.syncStatus.equals('PENDING')))
      .get();
      
    if (pendingItems.isEmpty) return;
    
    // Group by planId
    final Map<String, List<LocalOutboxData>> groupedByPlan = {};
    for (var item in pendingItems) {
      if (!groupedByPlan.containsKey(item.planId)) {
        groupedByPlan[item.planId] = [];
      }
      groupedByPlan[item.planId]!.add(item);
    }

    for (var entry in groupedByPlan.entries) {
      final planId = entry.key;
      final batch = entry.value;
      
      final payload = batch.map((item) => {
        'cargo_id': item.cargoId,
        'scanned_at_utc': item.scannedAtUtc,
        'operator_id': item.operatorId,
        'verified_seal_number': item.verifiedSealNumber,
        'sequence_deviation_acknowledged': item.sequenceDeviationAcknowledged
      }).toList();
      
      await _syncBatchWithBackoff(planId, payload, batch);
    }
  }

  Future<void> _syncBatchWithBackoff(String planId, List<Map<String, dynamic>> payload, List<LocalOutboxData> batch) async {
    final maxRetries = 4;
    int attempt = 0;
    
    while (attempt <= maxRetries) {
      try {
        final response = await http.post(
          Uri.parse('$baseUrl/plans/$planId/sync'),
          headers: {
            'Content-Type': 'application/json',
            'X-API-Key': apiKey,
          },
          body: jsonEncode(payload),
        );

        if (response.statusCode == 200 || response.statusCode == 202) {
          // Idempotency check: if the app successfully posted but the battery died right here, 
          // the app will reboot and retry. The backend's INSERT OR IGNORE will return 200 again,
          // allowing the app to successfully update the local drift DB to SYNCED on the second pass.
          
          bool isCompromised = batch.any((item) => item.sequenceDeviationAcknowledged);
          
          await db.transaction(() async {
            for (var item in batch) {
              await (db.update(db.localOutbox)
                ..where((tbl) => tbl.id.equals(item.id)))
                .write(LocalOutboxCompanion(syncStatus: const Value('SYNCED')));
            }
            
            if (isCompromised) {
              await (db.update(db.localPlans)
                ..where((tbl) => tbl.planId.equals(planId)))
                .write(LocalPlansCompanion(status: const Value('COMPROMISED')));
            }
          });
          return;
        } else {
          throw Exception("Server returned ${response.statusCode}");
        }
      } catch (e) {
        attempt++;
        if (attempt > maxRetries) {
          print("Sync failed after $maxRetries attempts for plan $planId: $e");
          return; // Surrender this cycle. Rely on polling timer.
        }
        
        // Exponential backoff: 2^attempt * 1000 ms = 2s, 4s, 8s, 16s
        // Jitter: +/- up to 30% of the delay
        int baseDelayMs = pow(2, attempt).toInt() * 1000;
        int jitter = _random.nextInt((baseDelayMs * 0.3).toInt());
        bool addJitter = _random.nextBool();
        int finalDelayMs = addJitter ? baseDelayMs + jitter : baseDelayMs - jitter;
        
        await Future.delayed(Duration(milliseconds: finalDelayMs));
      }
    }
  }
}

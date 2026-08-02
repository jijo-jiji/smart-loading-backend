import 'package:drift/drift.dart';

class LocalAnomalies extends Table {
  IntColumn get id => integer().autoIncrement()();
  TextColumn get cargoId => text()();
  TextColumn get planId => text()();
  TextColumn get scannedAtUtc => text()();
  TextColumn get operatorId => text()();
  TextColumn get anomalyType => text().withDefault(const Constant('ALIEN_CARGO'))();
  
  // 'PENDING', 'SYNCED'
  TextColumn get syncStatus => text().withDefault(const Constant('PENDING'))(); 
}

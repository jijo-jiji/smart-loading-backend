import 'package:drift/drift.dart';

class LocalOutbox extends Table {
  IntColumn get id => integer().autoIncrement()();
  TextColumn get planId => text()();
  TextColumn get cargoId => text()();
  TextColumn get scannedAtUtc => text()();
  TextColumn get operatorId => text()();
  TextColumn get verifiedSealNumber => text().nullable()();
  BoolColumn get sequenceDeviationAcknowledged => boolean().withDefault(const Constant(false))();
  
  // 'LASER', 'MANUAL_RECOVERY'
  TextColumn get scanMethod => text().withDefault(const Constant('LASER'))();
  
  // 'PENDING', 'SYNCED', 'REVERTED'
  TextColumn get syncStatus => text().withDefault(const Constant('PENDING'))(); 
}

import 'package:drift/drift.dart';

class LocalSteps extends Table {
  TextColumn get cargoId => text()();
  TextColumn get planId => text()();
  IntColumn get stepSequence => integer()();
  
  // Physical properties
  RealColumn get weight => real()();
  BoolColumn get isHazardous => boolean()();
  TextColumn get expectedSealNumber => text().nullable()();
  
  // Routing
  IntColumn get dropStopNumber => integer()();
  
  // Placement (Pre-translated by backend)
  TextColumn get positioningTranslation => text()();
  TextColumn get orientationInstruction => text()();
  TextColumn get dunnageInstruction => text()();

  @override
  Set<Column> get primaryKey => {planId, cargoId};
}

import 'package:drift/drift.dart';

class LocalPlans extends Table {
  TextColumn get planId => text()();
  TextColumn get truckId => text()();
  IntColumn get totalItems => integer()();
  TextColumn get status => text().withDefault(const Constant('ACTIVE'))();
  TextColumn get operatorId => text().nullable()();
  IntColumn get requiredClearance => integer().withDefault(const Constant(1))();
  
  @override
  Set<Column> get primaryKey => {planId};
}

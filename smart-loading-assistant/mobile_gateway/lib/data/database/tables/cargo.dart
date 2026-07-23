import 'package:drift/drift.dart';

class Cargo extends Table {
  IntColumn get id => integer().autoIncrement()();
  TextColumn get trackingId => text().withLength(min: 40, max: 64)();
  RealColumn get weight => real().check(weight.isBiggerThan(const Constant(0.0)))();
  RealColumn get length => real()();
  RealColumn get width => real()();
  RealColumn get height => real()();
  BoolColumn get isSynced => boolean().withDefault(const Constant(false))();
}

import 'package:drift/drift.dart';

class LocalRevocations extends Table {
  TextColumn get operatorId => text()();

  @override
  Set<Column> get primaryKey => {operatorId};
}

import 'dart:async';

abstract class ScannerRepository {
  Stream<String> get trackingIds;
  Future<void> resume();
  Future<void> pause();
  Future<void> dispose();
}

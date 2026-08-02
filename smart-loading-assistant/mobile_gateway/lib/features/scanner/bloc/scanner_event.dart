import 'package:equatable/equatable.dart';

abstract class ScannerEvent extends Equatable {
  const ScannerEvent();

  @override
  List<Object?> get props => [];
}

class BarcodeDetected extends ScannerEvent {
  final String rawData;

  const BarcodeDetected(this.rawData);

  @override
  List<Object?> get props => [rawData];
}

class PalletPlaced extends ScannerEvent {
  final String trackingId;

  const PalletPlaced(this.trackingId);

  @override
  List<Object?> get props => [trackingId];
}

class AmberAlertAcknowledged extends ScannerEvent {
  final String trackingId;

  const AmberAlertAcknowledged(this.trackingId);

  @override
  List<Object?> get props => [trackingId];
}

class ServerCompromised extends ScannerEvent {}

import 'package:equatable/equatable.dart';

abstract class ScannerState extends Equatable {
  const ScannerState();
  
  @override
  List<Object?> get props => [];
}

class ScanningState extends ScannerState {}

class DebounceState extends ScannerState {}

class ResolutionState extends ScannerState {
  final String trackingId;
  final String instruction;
  final bool isHazardous;

  const ResolutionState({
    required this.trackingId,
    required this.instruction,
    required this.isHazardous,
  });

  @override
  List<Object?> get props => [trackingId, instruction, isHazardous];
}

class AmberAlertState extends ScannerState {
  final String trackingId;

  const AmberAlertState(this.trackingId);

  @override
  List<Object?> get props => [trackingId];
}

class QuarantineState extends ScannerState {}

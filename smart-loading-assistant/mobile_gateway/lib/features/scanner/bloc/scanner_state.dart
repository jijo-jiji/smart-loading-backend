import 'package:equatable/equatable.dart';

abstract class ScannerState extends Equatable {
  const ScannerState();
  
  @override
  List<Object?> get props => [];
}

class ScannerInitial extends ScannerState {}
class ScannerProcessing extends ScannerState {}
class ScannerSuccess extends ScannerState {}
class ScannerFailure extends ScannerState {
  final String reason;
  const ScannerFailure(this.reason);
  @override
  List<Object?> get props => [reason];
}

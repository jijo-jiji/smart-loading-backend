import 'package:equatable/equatable.dart';

abstract class ScannerEvent extends Equatable {
  const ScannerEvent();

  @override
  List<Object?> get props => [];
}

class ScanInitiated extends ScannerEvent {
  final String rawData;
  final double weight;
  final double length;
  final double width;
  final double height;

  const ScanInitiated({
    required this.rawData,
    required this.weight,
    required this.length,
    required this.width,
    required this.height,
  });

  @override
  List<Object?> get props => [rawData, weight, length, width, height];
}

class ScanProcessed extends ScannerEvent {}

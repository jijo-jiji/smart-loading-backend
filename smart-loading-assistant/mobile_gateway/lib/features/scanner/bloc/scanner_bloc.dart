import 'package:flutter_bloc/flutter_bloc.dart';
import 'dart:async';
import 'scanner_event.dart';
import 'scanner_state.dart';
import '../repository/scanner_repository.dart';

class ScannerBloc extends Bloc<ScannerEvent, ScannerState> {
  final ScannerRepository scannerRepository;
  late final StreamSubscription<String> _scannerSubscription;

  ScannerBloc({required this.scannerRepository}) : super(ScannerInitial()) {
    on<ScanInitiated>((event, emit) async {
      emit(ScannerProcessing());
      
      // Kinetic responsibility: physically impossible payloads
      if (event.weight <= 0) {
        emit(const ScannerFailure("Weight must be > 0."));
        return;
      }
      
      final volume = event.length * event.width * event.height;
      if (volume < 1) {
        emit(const ScannerFailure("Mass volume must be >= 1."));
        return;
      }

      // Cryptographic hash validation (40 to 64 chars)
      if (event.rawData.length < 40 || event.rawData.length > 64) {
        emit(const ScannerFailure("Invalid cryptographic tracking ID format."));
        return;
      }

      // Simulate success saving to local DB for the boilerplate
      emit(ScannerSuccess());
    });

    _scannerSubscription = scannerRepository.trackingIds.listen((trackingId) {
      // Hardware laser triggered a scan
      add(ScanInitiated(
        rawData: trackingId,
        weight: 10.0,
        length: 1.0,
        width: 1.0,
        height: 1.0,
      ));
    });
  }

  @override
  Future<void> close() {
    _scannerSubscription.cancel();
    scannerRepository.dispose();
    return super.close();
  }
}

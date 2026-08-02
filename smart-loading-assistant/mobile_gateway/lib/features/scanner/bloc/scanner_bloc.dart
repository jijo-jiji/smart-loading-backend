import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:drift/drift.dart';
import 'dart:async';
import 'scanner_event.dart';
import 'scanner_state.dart';
import '../../../data/database/app_database.dart';

class ScannerBloc extends Bloc<ScannerEvent, ScannerState> {
  final AppDatabase db;
  final String currentPlanId; 
  final String currentOperatorId;

  ScannerBloc({
    required this.db,
    required this.currentPlanId,
    required this.currentOperatorId,
  }) : super(ScanningState()) {
    
    on<BarcodeDetected>(_onBarcodeDetected);
    on<PalletPlaced>(_onPalletPlaced);
    on<AmberAlertAcknowledged>(_onAmberAlertAcknowledged);
    on<ServerCompromised>((event, emit) => emit(QuarantineState()));
  }

  Future<void> _onBarcodeDetected(BarcodeDetected event, Emitter<ScannerState> emit) async {
    // Only process if we are currently scanning. Ignore if we are already dealing with a scan.
    if (state is! ScanningState) return;

    // 1. Enter DebounceState to kill the 15x multi-scan hardware twitch
    emit(DebounceState());
    
    // 2. Query LocalSteps for the hash
    final step = await (db.select(db.localSteps)
          ..where((tbl) => tbl.planId.equals(currentPlanId))
          ..where((tbl) => tbl.cargoId.equals(event.rawData)))
        .getSingleOrNull();

    // 3. Mandatory 1.5s visual pause
    await Future.delayed(const Duration(milliseconds: 1500));

    if (step == null) {
      // Alien Cargo! Drop into Amber Alert.
      emit(AmberAlertState(event.rawData));
    } else {
      // Resolution successful. Show placement instructions.
      emit(ResolutionState(
        trackingId: event.rawData,
        instruction: step.positioningTranslation,
        isHazardous: step.isHazardous,
      ));
    }
  }

  Future<void> _onPalletPlaced(PalletPlaced event, Emitter<ScannerState> emit) async {
    // The operator completed the heavy swipe-to-confirm physical workflow.
    
    // Write event to LocalOutbox
    await db.into(db.localOutbox).insert(LocalOutboxCompanion.insert(
      planId: currentPlanId,
      cargoId: event.trackingId,
      scannedAtUtc: DateTime.now().toUtc().toIso8601String(),
      operatorId: currentOperatorId,
      // Sequence deviation logic would go here if implemented locally, but for now we trust backend.
    ));

    // Return to ScanningState
    emit(ScanningState());
  }

  Future<void> _onAmberAlertAcknowledged(AmberAlertAcknowledged event, Emitter<ScannerState> emit) async {
    // The operator manually dismissed the high-friction Amber Alert.
    
    // Log the anomaly directly to LocalAnomalies
    await db.into(db.localAnomalies).insert(LocalAnomaliesCompanion.insert(
      cargoId: event.trackingId,
      planId: currentPlanId,
      scannedAtUtc: DateTime.now().toUtc().toIso8601String(),
      operatorId: currentOperatorId,
      anomalyType: const Value('ALIEN_CARGO'),
    ));

    // Safely return to scanning. The physics plan remains ACTIVE.
    emit(ScanningState());
  }
}

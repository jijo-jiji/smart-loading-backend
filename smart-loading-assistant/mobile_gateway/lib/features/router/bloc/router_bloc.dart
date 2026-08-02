import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:drift/drift.dart' as drift;
import 'package:mobile_gateway/data/database/app_database.dart';

import 'router_event.dart';
import 'router_state.dart';
import '../../auth/bloc/auth_state.dart';

class RouterBloc extends Bloc<RouterEvent, RouterState> {
  final AppDatabase db;

  AuthState _currentAuthState = AuthInitial();

  RouterBloc({required this.db}) : super(SplashView()) {
    on<EvaluateRouting>(_onEvaluateRouting);
    on<TruckScanned>(_onTruckScanned);
    on<AssumeTruckCommand>(_onAssumeTruckCommand);
    on<ResumeScanning>(_onResumeScanning);
    on<CompleteActivePlan>(_onCompleteActivePlan);
  }

  Future<void> _onEvaluateRouting(EvaluateRouting event, Emitter<RouterState> emit) async {
    _currentAuthState = event.authState;
    
    if (event.authState is Unauthenticated || event.authState is AuthInitial) {
      emit(LoginView());
      return;
    }

    if (event.authState is Authenticated) {
      final authState = event.authState as Authenticated;
      
      // Emit WelcomeView first to greet the user
      emit(WelcomeView(authState.operatorId));
      
      // Artificial delay to show the greeting
      await Future.delayed(const Duration(seconds: 2));
      
      // Check Drift for an active plan
      final activePlan = await (db.select(db.localPlans)..where((tbl) => tbl.status.equals('ACTIVE'))).getSingleOrNull();
      
      if (activePlan != null) {
        final authState = event.authState as Authenticated;
        if (activePlan.operatorId != null && activePlan.operatorId != authState.operatorId) {
          emit(HandoverConfirmationView(activePlan.planId, activePlan.operatorId!));
        } else {
          emit(DashboardView(activePlan.planId));
        }
      } else {
        emit(TruckSelectionView());
      }
    }
  }

  Future<void> _onTruckScanned(TruckScanned event, Emitter<RouterState> emit) async {
    if (_currentAuthState is! Authenticated) return;
    final authState = _currentAuthState as Authenticated;
    
    // Simulate fetching the plan from the DB or backend.
    // In our mock, we assume the plan exists in DB or is being created.
    // Let's check if the scanned plan is already in LocalPlans
    final plan = await (db.select(db.localPlans)..where((tbl) => tbl.planId.equals(event.planId))).getSingleOrNull();
    
    if (plan != null) {
      // 1. Evaluate Clearance
      if (authState.clearanceLevel < plan.requiredClearance) {
        emit(UnauthorizedAccessView("Clearance Level ${authState.clearanceLevel} insufficient for Plan ${plan.requiredClearance}"));
        return;
      }
      
      // 2. Evaluate Handover
      if (plan.operatorId != null && plan.operatorId != authState.operatorId) {
        emit(HandoverConfirmationView(event.planId, plan.operatorId!));
        return;
      }
    } else {
      // Mock inserting a new plan if it doesn't exist (simulating backend sync)
      await db.into(db.localPlans).insert(LocalPlan(
        planId: event.planId,
        truckId: "102-ALPHA",
        totalItems: 20,
        status: 'ACTIVE',
        operatorId: authState.operatorId,
        requiredClearance: 3 // Mock: Requires clearance 3
      ));
    }
    
    emit(DashboardView(event.planId));
  }

  Future<void> _onAssumeTruckCommand(AssumeTruckCommand event, Emitter<RouterState> emit) async {
    if (_currentAuthState is! Authenticated) return;
    final authState = _currentAuthState as Authenticated;
    
    // Update LocalPlans to assume command
    await (db.update(db.localPlans)..where((tbl) => tbl.planId.equals(event.planId)))
        .write(LocalPlansCompanion(operatorId: drift.Value(authState.operatorId)));
        
    // Insert Handover Anomaly
    await db.into(db.localAnomalies).insert(LocalAnomaliesCompanion.insert(
      cargoId: "TRUCK_DOOR",
      planId: event.planId,
      scannedAtUtc: DateTime.now().toUtc().toIso8601String(),
      operatorId: authState.operatorId,
      anomalyType: const drift.Value('CHAIN_OF_CUSTODY_HANDOVER'),
    ));
    
    emit(DashboardView(event.planId));
  }

  Future<void> _onResumeScanning(ResumeScanning event, Emitter<RouterState> emit) async {
    if (_currentAuthState is! Authenticated) return;
    final authState = _currentAuthState as Authenticated;
    
    emit(ScannerView(event.planId, authState.operatorId));
  }

  Future<void> _onCompleteActivePlan(CompleteActivePlan event, Emitter<RouterState> emit) async {
    // Update LocalPlans status to COMPLETED
    await (db.update(db.localPlans)..where((tbl) => tbl.planId.equals(event.planId)))
        .write(LocalPlansCompanion(status: const drift.Value('COMPLETED')));
        
    emit(TruckSelectionView());
  }
}

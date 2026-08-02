import '../../auth/bloc/auth_state.dart';

abstract class RouterEvent {}

class EvaluateRouting extends RouterEvent {
  final AuthState authState;
  EvaluateRouting(this.authState);
}

class TruckScanned extends RouterEvent {
  final String planId;
  TruckScanned(this.planId);
}

class AssumeTruckCommand extends RouterEvent {
  final String planId;
  AssumeTruckCommand(this.planId);
}

class ResumeScanning extends RouterEvent {
  final String planId;
  ResumeScanning(this.planId);
}

class CompleteActivePlan extends RouterEvent {
  final String planId;
  CompleteActivePlan(this.planId);
}

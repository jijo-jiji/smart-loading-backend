abstract class RouterState {}

class SplashView extends RouterState {}
class LoginView extends RouterState {}
class TruckSelectionView extends RouterState {}
class HandoverConfirmationView extends RouterState {
  final String planId;
  final String previousOperatorId;
  HandoverConfirmationView(this.planId, this.previousOperatorId);
}
class UnauthorizedAccessView extends RouterState {
  final String message;
  UnauthorizedAccessView(this.message);
}
class DashboardView extends RouterState {
  final String planId;
  DashboardView(this.planId);
}
class ScannerView extends RouterState {
  final String planId;
  final String operatorId;
  ScannerView(this.planId, this.operatorId);
}

class WelcomeView extends RouterState {
  final String operatorId;
  WelcomeView(this.operatorId);
}

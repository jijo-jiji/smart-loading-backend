abstract class AuthEvent {}

class AppStarted extends AuthEvent {}

class QrBadgeScanned extends AuthEvent {
  final String jwtToken;
  QrBadgeScanned(this.jwtToken);
}

class SessionExpired extends AuthEvent {}

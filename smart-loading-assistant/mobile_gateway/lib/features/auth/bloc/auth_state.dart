abstract class AuthState {}

class AuthInitial extends AuthState {}

class Unauthenticated extends AuthState {
  final String? error;
  Unauthenticated({this.error});
}

class Authenticated extends AuthState {
  final String operatorId;
  final int clearanceLevel;
  Authenticated(this.operatorId, this.clearanceLevel);
}

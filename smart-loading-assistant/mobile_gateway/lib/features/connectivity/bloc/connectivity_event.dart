import 'package:equatable/equatable.dart';

abstract class ConnectivityEvent extends Equatable {
  const ConnectivityEvent();
  @override
  List<Object?> get props => [];
}

class ConnectivityStatusChanged extends ConnectivityEvent {
  final bool isOnline;
  const ConnectivityStatusChanged(this.isOnline);
  @override
  List<Object?> get props => [isOnline];
}

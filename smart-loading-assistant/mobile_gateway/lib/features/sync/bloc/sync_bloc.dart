import 'package:flutter_bloc/flutter_bloc.dart';
import 'dart:async';

import 'sync_event.dart';
import 'sync_state.dart';
import '../../connectivity/bloc/connectivity_bloc.dart';
import '../../connectivity/bloc/connectivity_state.dart';

class SyncBloc extends Bloc<SyncEvent, SyncState> {
  final ConnectivityBloc connectivityBloc;
  late final StreamSubscription connectivitySubscription;

  SyncBloc({required this.connectivityBloc}) : super(SyncInitial()) {
    on<SyncRequested>((event, emit) async {
      if (connectivityBloc.state is ConnectivityOnline) {
        emit(SyncInProgress());
        // Simulate an API network request batching local db
        await Future.delayed(const Duration(milliseconds: 500));
        emit(SyncSuccess());
      } else {
        // Outbox pattern: hold in failure/offline state until connectivity returns
        emit(SyncFailure());
      }
    });

    connectivitySubscription = connectivityBloc.stream.listen((state) {
      if (state is ConnectivityOnline) {
        add(SyncRequested());
      }
    });
  }

  @override
  Future<void> close() {
    connectivitySubscription.cancel();
    return super.close();
  }
}

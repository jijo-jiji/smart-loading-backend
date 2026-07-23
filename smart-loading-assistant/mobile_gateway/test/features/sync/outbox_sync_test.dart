import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:mobile_gateway/features/connectivity/bloc/connectivity_bloc.dart';
import 'package:mobile_gateway/features/connectivity/bloc/connectivity_state.dart';
import 'package:mobile_gateway/features/sync/bloc/sync_bloc.dart';
import 'package:mobile_gateway/features/sync/bloc/sync_event.dart';
import 'package:mobile_gateway/features/sync/bloc/sync_state.dart';
import 'dart:async';

class MockConnectivityBloc extends Mock implements ConnectivityBloc {}

void main() {
  group('SyncBloc - Outbox Pattern (Kinetic Failure Simulation)', () {
    late SyncBloc syncBloc;
    late MockConnectivityBloc mockConnectivityBloc;
    late StreamController<ConnectivityState> connectivityStreamController;

    setUp(() {
      mockConnectivityBloc = MockConnectivityBloc();
      connectivityStreamController = StreamController<ConnectivityState>();
      
      when(() => mockConnectivityBloc.stream)
          .thenAnswer((_) => connectivityStreamController.stream);
          
      when(() => mockConnectivityBloc.state)
          .thenReturn(ConnectivityOffline());
          
      syncBloc = SyncBloc(connectivityBloc: mockConnectivityBloc);
    });

    tearDown(() {
      connectivityStreamController.close();
      syncBloc.close();
    });

    test('emits [SyncFailure] when SyncRequested and connectivity is offline', () {
      expectLater(
        syncBloc.stream,
        emitsInOrder([
          isA<SyncFailure>(),
        ]),
      );

      syncBloc.add(SyncRequested());
    });

    test('emits [SyncInProgress, SyncSuccess] when SyncRequested and connectivity is online', () {
      when(() => mockConnectivityBloc.state)
          .thenReturn(ConnectivityOnline());

      expectLater(
        syncBloc.stream,
        emitsInOrder([
          isA<SyncInProgress>(),
          isA<SyncSuccess>(),
        ]),
      );

      syncBloc.add(SyncRequested());
    });
    
    test('triggers SyncRequested when connectivity changes to online', () async {
      when(() => mockConnectivityBloc.state).thenReturn(ConnectivityOnline());
      
      expectLater(
        syncBloc.stream,
        emitsInOrder([
          isA<SyncInProgress>(),
          isA<SyncSuccess>(),
        ]),
      );

      // Simulate hardware radio turning on
      connectivityStreamController.add(ConnectivityOnline());
    });
  });
}

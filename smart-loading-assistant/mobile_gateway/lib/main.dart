import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:mobile_gateway/data/database/app_database.dart';
import 'package:mobile_gateway/features/connectivity/bloc/connectivity_bloc.dart';
import 'package:mobile_gateway/features/scanner/bloc/scanner_bloc.dart';
import 'package:mobile_gateway/features/scanner/repository/hardware_scanner_repository.dart';
import 'package:mobile_gateway/features/sync/bloc/sync_bloc.dart';
import 'package:mobile_gateway/ui/screens/scanner_screen.dart';
import 'package:mobile_gateway/ui/screens/login_screen.dart';
import 'package:mobile_gateway/ui/screens/dashboard_screen.dart';
import 'package:mobile_gateway/ui/screens/truck_selection_screen.dart' as mobile_gateway_ui;
import 'package:mobile_gateway/ui/screens/handover_confirmation_screen.dart' as mobile_gateway_ui;
import 'package:mobile_gateway/ui/screens/unauthorized_access_screen.dart' as mobile_gateway_ui;
import 'package:mobile_gateway/features/auth/bloc/auth_bloc.dart';
import 'package:mobile_gateway/features/auth/bloc/auth_event.dart';
import 'package:mobile_gateway/features/auth/bloc/auth_state.dart';
import 'package:mobile_gateway/features/router/bloc/router_bloc.dart';
import 'package:mobile_gateway/features/router/bloc/router_state.dart';
import 'package:mobile_gateway/features/router/bloc/router_event.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:drift/drift.dart' as drift;

Future<void> _insertMockData(AppDatabase db) async {
  final count = await db.select(db.localSteps).get();
  if (count.isEmpty) {
    await db.into(db.localSteps).insert(LocalStepsCompanion.insert(
      planId: "DEV_PLAN_001",
      cargoId: "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2",
      stepSequence: 1,
      weight: 1500.0,
      dropStopNumber: 1,
      orientationInstruction: "Load Sideways",
      dunnageInstruction: "Corrugated Void Filler",
      isHazardous: false,
      positioningTranslation: "Base Layer on Center Deck, Front (Near Cab)",
    ));
    await db.into(db.localSteps).insert(LocalStepsCompanion.insert(
      planId: "DEV_PLAN_001",
      cargoId: "d4c3b2a1f0e9d8c7b6a5f4e3d2c1b0a9f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c",
      stepSequence: 2,
      weight: 800.0,
      dropStopNumber: 1,
      orientationInstruction: "Load Straight",
      dunnageInstruction: "None",
      isHazardous: true,
      positioningTranslation: "Base Layer on Left Wall, Middle",
    ));
  }
}

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Initialize Database
  final database = AppDatabase();
  await _insertMockData(database);
  
  // Initialize Repositories
  final scannerRepository = HardwareScannerRepository();
  const secureStorage = FlutterSecureStorage();

  runApp(MyApp(
    database: database,
    scannerRepository: scannerRepository,
    secureStorage: secureStorage,
  ));
}

class MyApp extends StatelessWidget {
  final AppDatabase database;
  final HardwareScannerRepository scannerRepository;
  final FlutterSecureStorage secureStorage;

  const MyApp({
    super.key,
    required this.database,
    required this.scannerRepository,
    required this.secureStorage,
  });

  @override
  Widget build(BuildContext context) {
    return MultiBlocProvider(
      providers: [
        BlocProvider<ConnectivityBloc>(
          create: (context) => ConnectivityBloc(),
        ),
        BlocProvider<AuthBloc>(
          create: (context) => AuthBloc(
            db: database,
            secureStorage: secureStorage,
          )..add(AppStarted()),
        ),
        BlocProvider<RouterBloc>(
          create: (context) {
            final authBloc = context.read<AuthBloc>();
            final routerBloc = RouterBloc(db: database);
            // Listen to auth changes and route accordingly
            authBloc.stream.listen((authState) {
              routerBloc.add(EvaluateRouting(authState));
            });
            // initial evaluation
            routerBloc.add(EvaluateRouting(authBloc.state));
            return routerBloc;
          },
        ),
        BlocProvider<SyncBloc>(
          create: (context) => SyncBloc(
            connectivityBloc: context.read<ConnectivityBloc>(),
          ),
        ),
      ],
      child: MaterialApp(
        title: 'Smart Loading Assistant',
        theme: ThemeData(
          colorScheme: ColorScheme.fromSeed(
            seedColor: Colors.green,
            brightness: Brightness.dark,
          ),
          useMaterial3: true,
        ),
        home: BlocBuilder<RouterBloc, RouterState>(
          builder: (context, state) {
            if (state is SplashView) {
              return const Scaffold(body: Center(child: CircularProgressIndicator()));
            } else if (state is LoginView) {
              return const LoginScreen();
            } else if (state is TruckSelectionView) {
              return const mobile_gateway_ui.TruckSelectionScreen();
            } else if (state is HandoverConfirmationView) {
              return mobile_gateway_ui.HandoverConfirmationScreen(
                planId: state.planId, 
                previousOperatorId: state.previousOperatorId
              );
            } else if (state is UnauthorizedAccessView) {
              return mobile_gateway_ui.UnauthorizedAccessScreen(message: state.message);
            } else if (state is DashboardView) {
              return DashboardScreen(planId: state.planId);
            } else if (state is WelcomeView) {
              return Scaffold(
                backgroundColor: Colors.black,
                body: Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(Icons.check_circle_outline, color: Colors.green, size: 80),
                      const SizedBox(height: 24),
                      Text(
                        'Hi, ${state.operatorId}',
                        style: const TextStyle(color: Colors.white, fontSize: 32, fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 16),
                      const CircularProgressIndicator(color: Colors.green),
                    ],
                  ),
                ),
              );
            } else if (state is ScannerView) {
              return BlocProvider<ScannerBloc>(
                create: (context) => ScannerBloc(
                  db: database,
                  currentPlanId: state.planId,
                  currentOperatorId: state.operatorId,
                ),
                child: const ScannerScreen(),
              );
            }
            return const LoginScreen();
          }
        ),
      ),
    );
  }
}

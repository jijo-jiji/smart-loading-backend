import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import '../widgets/swipe_to_confirm.dart';
import '../../features/scanner/bloc/scanner_bloc.dart';
import '../../features/scanner/bloc/scanner_state.dart';
import '../../features/scanner/bloc/scanner_event.dart';

class ScannerScreen extends StatefulWidget {
  const ScannerScreen({Key? key}) : super(key: key);

  @override
  State<ScannerScreen> createState() => _ScannerScreenState();
}

class _ScannerScreenState extends State<ScannerScreen> {
  final MobileScannerController _cameraController = MobileScannerController(
    detectionSpeed: DetectionSpeed.normal,
    facing: CameraFacing.back,
    torchEnabled: false,
  );

  @override
  void initState() {
    super.initState();
    _cameraController.start();
  }

  @override
  void dispose() {
    _cameraController.dispose();
    super.dispose();
  }

  void _onDetect(BarcodeCapture capture) {
    if (capture.barcodes.isEmpty) return;
    final String? code = capture.barcodes.first.rawValue;
    if (code != null) {
      // Fire the event. The Bloc handles debouncing.
      context.read<ScannerBloc>().add(BarcodeDetected(code));
    }
  }

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<ScannerBloc, ScannerState>(
      builder: (context, state) {
        // Quarantine State: Full Red Lock
        if (state is QuarantineState) {
          return _buildQuarantineView();
        }
        
        // Amber Alert State: Full Amber Lock for Alien Cargo
        if (state is AmberAlertState) {
          return _buildAmberAlertView(context, state.trackingId);
        }
        
        // Normal Flow (Scanning, Debounce, Resolution)
        return Scaffold(
          backgroundColor: Colors.black,
          body: Stack(
            fit: StackFit.expand,
            children: [
              // Camera Feed (Hide or Blur if not actively scanning)
              if (state is ScanningState || state is DebounceState)
                MobileScanner(
                  controller: _cameraController,
                  onDetect: _onDetect,
                  errorBuilder: (BuildContext context, MobileScannerException error) {
                    return const Center(child: Text('Camera not available on this device', style: TextStyle(color: Colors.white54)));
                  },
                ),
                
              if (state is DebounceState)
                Container(color: Colors.black54), // Dim the feed to indicate pausing
                
              // Overlay UI
              SafeArea(
                child: Column(
                  children: [
                    _buildTopStatusBar(state),
                    const Spacer(),
                    
                    // Center Instruction Card
                    if (state is ResolutionState)
                      _buildInstructionCard(state),
                      
                    // Target Reticle
                    if (state is ScanningState || state is DebounceState)
                      _buildTargetReticle(state),
                      
                    const Spacer(),
                    
                    // Bottom Control Panel
                    _buildBottomControlPanel(context, state),
                  ],
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildTopStatusBar(ScannerState state) {
    String title = 'SCANNER ACTIVE';
    Color color = Colors.greenAccent;
    
    if (state is DebounceState) {
      title = 'PROCESSING HASH...';
      color = Colors.blueAccent;
    } else if (state is ResolutionState) {
      title = 'READY TO LOAD';
      color = Colors.white;
    }

    return Padding(
      padding: const EdgeInsets.all(16.0),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            title,
            style: TextStyle(
              color: color,
              fontWeight: FontWeight.bold,
              fontSize: 18,
            ),
          ),
          IconButton(
            icon: ValueListenableBuilder(
              valueListenable: _cameraController,
              builder: (context, controllerState, child) {
                return Icon(
                  controllerState.torchState == TorchState.on ? Icons.flash_on : Icons.flash_off,
                  color: controllerState.torchState == TorchState.on ? Colors.yellow : Colors.white,
                );
              },
            ),
            onPressed: () => _cameraController.toggleTorch(),
          ),
        ],
      ),
    );
  }

  Widget _buildTargetReticle(ScannerState state) {
    return Container(
      width: 250,
      height: 250,
      decoration: BoxDecoration(
        border: Border.all(
          color: state is DebounceState ? Colors.blue : Colors.white54,
          width: state is DebounceState ? 4 : 2,
        ),
        borderRadius: BorderRadius.circular(12),
      ),
    );
  }

  Widget _buildInstructionCard(ResolutionState state) {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 24),
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: state.isHazardous ? Colors.red[900] : Colors.blueGrey[900],
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: state.isHazardous ? Colors.redAccent : Colors.lightBlueAccent,
          width: 3,
        )
      ),
      child: Column(
        children: [
          if (state.isHazardous)
            const Text(
              '⚠️ HAZARDOUS CARGO',
              style: TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold),
            ),
          const SizedBox(height: 12),
          Text(
            state.instruction.toUpperCase(),
            textAlign: TextAlign.center,
            style: const TextStyle(color: Colors.white, fontSize: 32, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 12),
          Text(
            'ID: ${state.trackingId.substring(0, 8)}...',
            style: const TextStyle(color: Colors.white70, fontSize: 16),
          ),
        ],
      ),
    );
  }

  Widget _buildBottomControlPanel(BuildContext context, ScannerState state) {
    return Container(
      padding: const EdgeInsets.all(24.0),
      decoration: const BoxDecoration(
        color: Colors.black87,
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (state is ResolutionState)
            SwipeToConfirmWidget(
              onConfirm: () async {
                context.read<ScannerBloc>().add(PalletPlaced(state.trackingId));
              },
              text: 'SWIPE WHEN LOADED --->',
              height: 100,
            )
          else
            Column(
              children: [
                const Text("Awaiting Hash...", style: TextStyle(color: Colors.white54)),
                const SizedBox(height: 16),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                  children: [
                    ElevatedButton(
                      style: ElevatedButton.styleFrom(backgroundColor: Colors.green),
                      onPressed: () {
                        context.read<ScannerBloc>().add(BarcodeDetected("a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2"));
                      },
                      child: const Text('MOCK VALID', style: TextStyle(color: Colors.white)),
                    ),
                    ElevatedButton(
                      style: ElevatedButton.styleFrom(backgroundColor: Colors.orange),
                      onPressed: () {
                        context.read<ScannerBloc>().add(BarcodeDetected("ALIEN_CARGO_HASH_999"));
                      },
                      child: const Text('MOCK ALIEN', style: TextStyle(color: Colors.white)),
                    ),
                  ],
                ),
              ],
            ),
        ],
      ),
    );
  }

  Widget _buildAmberAlertView(BuildContext context, String trackingId) {
    return Scaffold(
      backgroundColor: Colors.amber[800],
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(32.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.warning_amber_rounded, size: 120, color: Colors.black),
              const SizedBox(height: 32),
              const Text(
                'WRONG TRUCK',
                style: TextStyle(fontSize: 40, fontWeight: FontWeight.bold, color: Colors.black),
              ),
              const Text(
                'ALIEN CARGO DETECTED',
                style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Colors.black87),
              ),
              const SizedBox(height: 64),
              ElevatedButton(
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.black,
                  padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 24),
                ),
                onPressed: () {
                  context.read<ScannerBloc>().add(AmberAlertAcknowledged(trackingId));
                },
                child: const Text(
                  'ACKNOWLEDGE & REMOVE PALLET',
                  style: TextStyle(fontSize: 18, color: Colors.white),
                ),
              )
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildQuarantineView() {
    return Scaffold(
      backgroundColor: Colors.red[900],
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(32.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.lock_person, size: 120, color: Colors.white),
              const SizedBox(height: 32),
              const Text(
                'STOP LOADING',
                style: TextStyle(fontSize: 40, fontWeight: FontWeight.bold, color: Colors.white),
              ),
              const Text(
                'PLAN COMPROMISED\nAWAITING MANAGER REVIEW',
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 20, color: Colors.white70),
              ),
              const SizedBox(height: 64),
              OutlinedButton(
                style: OutlinedButton.styleFrom(
                  foregroundColor: Colors.white, side: const BorderSide(color: Colors.white, width: 2),
                  padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 24),
                ),
                onPressed: () {
                  // Revert locally if pending
                },
                child: const Text('[ REVERT LAST SCAN ]', style: TextStyle(fontSize: 18)),
              ),
              const SizedBox(height: 24),
              ElevatedButton(
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.black,
                  padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 24),
                ),
                onPressed: () {
                  // Open Manager QR Scanner
                },
                child: const Text('[ MANAGER OVERRIDE ]', style: TextStyle(fontSize: 18, color: Colors.white)),
              )
            ],
          ),
        ),
      ),
    );
  }
}

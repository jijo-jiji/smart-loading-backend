import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import '../../features/router/bloc/router_bloc.dart';
import '../../features/router/bloc/router_event.dart';

class TruckSelectionScreen extends StatefulWidget {
  const TruckSelectionScreen({super.key});

  @override
  State<TruckSelectionScreen> createState() => _TruckSelectionScreenState();
}

class _TruckSelectionScreenState extends State<TruckSelectionScreen> {
  final MobileScannerController _cameraController = MobileScannerController(
    detectionSpeed: DetectionSpeed.normal,
    facing: CameraFacing.back,
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
    if (code != null && code.startsWith('DEV_PLAN')) {
      context.read<RouterBloc>().add(TruckScanned(code));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(
        fit: StackFit.expand,
        children: [
          MobileScanner(
            controller: _cameraController,
            onDetect: _onDetect,
            errorBuilder: (BuildContext context, MobileScannerException error) {
              return const Center(child: Text('Camera not available on this device', style: TextStyle(color: Colors.white54)));
            },
          ),
          SafeArea(
            child: Column(
              children: [
                const Spacer(),
                Container(
                  padding: const EdgeInsets.all(32),
                  color: Colors.black87,
                  width: double.infinity,
                  child: Column(
                    children: [
                      const Icon(Icons.local_shipping, size: 64, color: Colors.blueAccent),
                      const SizedBox(height: 16),
                      const Text(
                        'AWAITING TRUCK ASSIGNMENT',
                        textAlign: TextAlign.center,
                        style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Colors.white),
                      ),
                      const SizedBox(height: 8),
                      const Text(
                        'Scan the QR code on the Truck Container door.',
                        textAlign: TextAlign.center,
                        style: TextStyle(color: Colors.white70, fontSize: 14),
                      ),
                      const SizedBox(height: 32),
                      ElevatedButton(
                        onPressed: () {
                          context.read<RouterBloc>().add(TruckScanned("DEV_PLAN_001"));
                        },
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.blueAccent,
                          padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
                        ),
                        child: const Text('MOCK SCAN TRUCK 102-ALPHA', style: TextStyle(color: Colors.white, fontSize: 14)),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

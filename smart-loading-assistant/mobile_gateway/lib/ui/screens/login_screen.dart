import 'package:flutter/material.dart';
import 'package:dart_jsonwebtoken/dart_jsonwebtoken.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import '../../features/auth/bloc/auth_event.dart';
import '../../features/auth/bloc/auth_bloc.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
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
    if (code != null && code.startsWith('eyJ')) {
      // It's a JWT
      context.read<AuthBloc>().add(QrBadgeScanned(code));
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
                  padding: const EdgeInsets.all(24),
                  color: Colors.black87,
                  width: double.infinity,
                  child: Column(
                    children: [
                      const Icon(Icons.qr_code_scanner, size: 64, color: Colors.white),
                      const SizedBox(height: 16),
                      const Text(
                        "SCAN OPERATOR BADGE",
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                          letterSpacing: 2,
                        ),
                      ),
                      const SizedBox(height: 32),
                      ElevatedButton(
                        onPressed: () {
                          final jwt = JWT({
                            'operator_id': 'DEV_OPERATOR_001',
                            'clearance_level': 5,
                            'exp': (DateTime.now().add(const Duration(hours: 12)).millisecondsSinceEpoch ~/ 1000)
                          });
                          final token = jwt.sign(SecretKey('MOCK_SECRET_KEY'));
                          context.read<AuthBloc>().add(QrBadgeScanned(token));
                        },
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.blueAccent,
                          padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
                        ),
                        child: const Text("MOCK SCAN BADGE", style: TextStyle(color: Colors.white)),
                      ),
                    ],
                  ),
                )
              ],
            ),
          ),
        ],
      ),
    );
  }
}

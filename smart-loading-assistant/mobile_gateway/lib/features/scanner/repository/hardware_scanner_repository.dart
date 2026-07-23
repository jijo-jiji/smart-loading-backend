import 'dart:async';
import 'package:flutter/services.dart';
import 'scanner_repository.dart';

class HardwareScannerRepository implements ScannerRepository {
  final _trackingIdController = StreamController<String>.broadcast();
  bool _isOpticalFeedActive = false;

  HardwareScannerRepository() {
    // Intercept physical volume buttons
    HardwareKeyboard.instance.addHandler(_handleKey);
  }

  bool _handleKey(KeyEvent event) {
    if (event is KeyDownEvent) {
      if (event.logicalKey == LogicalKeyboardKey.audioVolumeUp ||
          event.logicalKey == LogicalKeyboardKey.audioVolumeDown) {
        resume();
        return true; // Consume event
      }
    } else if (event is KeyUpEvent) {
      if (event.logicalKey == LogicalKeyboardKey.audioVolumeUp ||
          event.logicalKey == LogicalKeyboardKey.audioVolumeDown) {
        pause();
        return true; // Consume event
      }
    }
    return false;
  }

  @override
  Stream<String> get trackingIds => _trackingIdController.stream;

  @override
  Future<void> resume() async {
    if (!_isOpticalFeedActive) {
      _isOpticalFeedActive = true;
      // Initialize or resume mobile_scanner camera feed here
      // e.g. cameraController.start();
    }
  }

  @override
  Future<void> pause() async {
    if (_isOpticalFeedActive) {
      _isOpticalFeedActive = false;
      // Pause mobile_scanner camera feed to save battery and thermal load
      // e.g. cameraController.stop();
    }
  }

  @override
  Future<void> dispose() async {
    HardwareKeyboard.instance.removeHandler(_handleKey);
    await _trackingIdController.close();
    // cameraController.dispose();
  }
}

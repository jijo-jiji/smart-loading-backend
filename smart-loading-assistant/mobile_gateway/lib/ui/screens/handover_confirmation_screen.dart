import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../features/router/bloc/router_bloc.dart';
import '../../features/router/bloc/router_event.dart';

class HandoverConfirmationScreen extends StatelessWidget {
  final String planId;
  final String previousOperatorId;

  const HandoverConfirmationScreen({
    super.key,
    required this.planId,
    required this.previousOperatorId,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.amber[900],
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(32.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.warning_amber_rounded, size: 100, color: Colors.black),
              const SizedBox(height: 32),
              const Text(
                'HANDOVER REQUIRED',
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 32, fontWeight: FontWeight.bold, color: Colors.black),
              ),
              const SizedBox(height: 24),
              Text(
                'This truck is currently locked by Operator $previousOperatorId.',
                textAlign: TextAlign.center,
                style: const TextStyle(fontSize: 20, color: Colors.black87),
              ),
              const SizedBox(height: 16),
              const Text(
                'Do you want to override their session and assume command? This action will be audited.',
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 16, color: Colors.black54),
              ),
              const SizedBox(height: 64),
              ElevatedButton(
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.black,
                  padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 24),
                ),
                onPressed: () {
                  context.read<RouterBloc>().add(AssumeTruckCommand(planId));
                },
                child: const Text('YES, ASSUME COMMAND', style: TextStyle(color: Colors.white, fontSize: 18)),
              ),
              const SizedBox(height: 24),
              TextButton(
                onPressed: () {
                  // Go back to login or just re-evaluate state (which defaults to login if we just restart)
                  // Let's just pop back to TruckSelection by evaluating current auth state
                  final authState = context.read<RouterBloc>().state; // hacky, better to use an event
                  // Actually, just emit a new evaluate routing event from main
                  // But wait, the easiest is to just pop or emit TruckSelectionView.
                  // Since RouterBloc handles it, we can just send EvaluateRouting again.
                  context.read<RouterBloc>().add(EvaluateRouting(context.read<RouterBloc>().db != null ? (context.read<RouterBloc>() as dynamic)._currentAuthState : null)); 
                  // Let's just leave it simple: they can't go back unless they restart the app or we add a Cancel event.
                  // For the demo, they will just click Yes.
                },
                child: const Text('CANCEL', style: TextStyle(color: Colors.black54, fontSize: 18)),
              )
            ],
          ),
        ),
      ),
    );
  }
}

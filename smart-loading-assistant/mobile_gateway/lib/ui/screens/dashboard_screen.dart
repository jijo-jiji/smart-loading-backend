import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../features/auth/bloc/auth_state.dart';
import '../../features/auth/bloc/auth_bloc.dart';
import '../../features/auth/bloc/auth_event.dart';
import '../../features/router/bloc/router_event.dart';
import '../../features/router/bloc/router_bloc.dart';
import 'scanner_screen.dart';

class DashboardScreen extends StatelessWidget {
  final String planId;
  const DashboardScreen({super.key, required this.planId});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF1E1E1E),
      appBar: AppBar(
        backgroundColor: Colors.black,
        title: const Text("SHIFT DASHBOARD"),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout, color: Colors.redAccent),
            onPressed: () {
              context.read<AuthBloc>().add(SessionExpired());
            },
          )
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            BlocBuilder<AuthBloc, AuthState>(
              builder: (context, state) {
                String opId = "UNKNOWN";
                if (state is Authenticated) {
                  opId = state.operatorId;
                }
                return Text(
                  "OPERATOR: $opId",
                  style: const TextStyle(color: Colors.white54, fontSize: 16, letterSpacing: 1.5),
                );
              },
            ),
            const SizedBox(height: 16),
            Text(
              planId,
              style: const TextStyle(color: Colors.white, fontSize: 36, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 32),
            // Progress Bar Mock
            const Text("PLAN PROGRESS", style: TextStyle(color: Colors.white54)),
            const SizedBox(height: 8),
            LinearProgressIndicator(
              value: 14 / 20,
              minHeight: 20,
              backgroundColor: Colors.grey[800],
              color: Colors.greenAccent,
            ),
            const SizedBox(height: 8),
            const Text("14 of 20 Pallets Loaded", style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
            
            const Spacer(),
            
            // Resume Scanning Button
            ElevatedButton(
              onPressed: () {
                context.read<RouterBloc>().add(ResumeScanning(planId));
              },
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.green,
                padding: const EdgeInsets.symmetric(vertical: 24),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
              ),
              child: const Text(
                "RESUME SCANNING",
                style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Colors.white),
              ),
            ),
            const SizedBox(height: 16),
            // Complete Truck Button
            OutlinedButton(
              onPressed: () {
                context.read<RouterBloc>().add(CompleteActivePlan(planId));
              },
              style: OutlinedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 16),
                side: const BorderSide(color: Colors.green),
              ),
              child: const Text("COMPLETE TRUCK", style: TextStyle(color: Colors.green, fontSize: 18, fontWeight: FontWeight.bold)),
            ),
          ],
        ),
      ),
    );
  }
}

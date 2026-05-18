import 'package:flutter/material.dart';
import '../../shared/widgets/ichebo_app_bar.dart';
import '../../shared/widgets/empty_state.dart';

class ActivityScreen extends StatelessWidget {
  const ActivityScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: const IcheboAppBar(title: 'Activity', watermarkText: 'ACTIVITY'),
      body: const EmptyState(
        icon: Icons.check_circle_outline,
        message: 'Your tasks, habits, and goals will appear here.',
      ),
    );
  }
}

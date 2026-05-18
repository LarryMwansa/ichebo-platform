import 'package:flutter/material.dart';
import '../../shared/widgets/ichebo_app_bar.dart';
import '../../shared/widgets/empty_state.dart';

class LearnScreen extends StatelessWidget {
  const LearnScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: const IcheboAppBar(title: 'Learn', watermarkText: 'FORMATION'),
      body: const EmptyState(
        icon: Icons.school_outlined,
        message: 'Your programmes and enrolments will appear here.',
      ),
    );
  }
}

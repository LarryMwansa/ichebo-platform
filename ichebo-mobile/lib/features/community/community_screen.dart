import 'package:flutter/material.dart';
import '../../shared/widgets/ichebo_app_bar.dart';
import '../../shared/widgets/empty_state.dart';

class CommunityScreen extends StatelessWidget {
  const CommunityScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: const IcheboAppBar(title: 'Community', watermarkText: 'COMMUNITY'),
      body: const EmptyState(
        icon: Icons.people_outline,
        message: 'Members, announcements, and gatherings will appear here.',
      ),
    );
  }
}

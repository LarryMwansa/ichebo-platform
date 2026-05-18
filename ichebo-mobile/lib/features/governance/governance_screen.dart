import 'package:flutter/material.dart';
import '../../shared/widgets/ichebo_app_bar.dart';
import '../../shared/widgets/empty_state.dart';

class GovernanceScreen extends StatelessWidget {
  const GovernanceScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: const IcheboAppBar(title: 'Governance', watermarkText: 'GOVERNANCE'),
      body: const EmptyState(
        icon: Icons.account_balance_outlined,
        message: 'Reference Library, Mandate, and Keys will appear here.',
      ),
    );
  }
}

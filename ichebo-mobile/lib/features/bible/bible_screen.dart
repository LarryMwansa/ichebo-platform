import 'package:flutter/material.dart';
import '../../shared/widgets/ichebo_app_bar.dart';
import '../../shared/widgets/empty_state.dart';

class BibleScreen extends StatelessWidget {
  const BibleScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: const IcheboAppBar(title: 'Bible', watermarkText: 'SCRIPTURE'),
      body: const EmptyState(
        icon: Icons.menu_book_outlined,
        message: 'Bible reader coming soon.\nSelect a translation to begin.',
      ),
    );
  }
}

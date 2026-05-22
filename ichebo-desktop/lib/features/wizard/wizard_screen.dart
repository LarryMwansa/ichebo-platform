import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../core/theme/tokens.dart';
import 'step_activation.dart';
import 'step_account.dart';
import 'step_initial_sync.dart';
import 'wizard_state.dart';

class WizardScreen extends ConsumerWidget {
  const WizardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final wizard = ref.watch(wizardProvider);

    // When wizard completes, navigate to the shell.
    ref.listen(wizardProvider, (_, next) {
      if (next.step == WizardStep.done) {
        context.go('/community');
      }
    });

    return Scaffold(
      backgroundColor: IcsColors.inkBg,
      body: Center(
        child: SingleChildScrollView(
          child: Container(
            width: 480,
            padding: const EdgeInsets.all(IcsSpacing.xl),
            decoration: BoxDecoration(
              color: IcsColors.ink2,
              borderRadius: BorderRadius.all(IcsRadius.m),
              border: Border.all(color: IcsColors.borderDark),
            ),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                _StepIndicator(step: wizard.step),
                const SizedBox(height: IcsSpacing.xl),
                AnimatedSwitcher(
                  duration: const Duration(milliseconds: 250),
                  child: switch (wizard.step) {
                    WizardStep.activation => const StepActivation(),
                    WizardStep.account   => const StepAccount(),
                    WizardStep.sync      => const StepInitialSync(),
                    WizardStep.done      => const SizedBox.shrink(),
                  },
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _StepIndicator extends StatelessWidget {
  const _StepIndicator({required this.step});
  final WizardStep step;

  @override
  Widget build(BuildContext context) {
    final steps = [WizardStep.activation, WizardStep.account, WizardStep.sync];
    final labels = ['Activation', 'Account', 'Sync'];
    final current = steps.indexOf(step);

    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: List.generate(steps.length * 2 - 1, (i) {
        if (i.isOdd) {
          // Connector line
          final leftIndex = i ~/ 2;
          final passed = leftIndex < current;
          return Container(
            width: 40,
            height: 1,
            color: passed ? IcsColors.accentRed : IcsColors.borderDark,
          );
        }
        final index = i ~/ 2;
        final isActive = index == current;
        final isPassed = index < current;
        return Column(
          children: [
            Container(
              width: 28,
              height: 28,
              decoration: BoxDecoration(
                color: isActive
                    ? IcsColors.accentRed
                    : isPassed
                        ? IcsColors.accentRed.withValues(alpha: 0.3)
                        : const Color(0xFF2A2A2A),
                shape: BoxShape.circle,
                border: Border.all(
                  color: isActive || isPassed ? IcsColors.accentRed : IcsColors.borderDark,
                ),
              ),
              child: Center(
                child: isPassed
                    ? const Icon(Icons.check, size: 14, color: Colors.white)
                    : Text(
                        '${index + 1}',
                        style: TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w700,
                          color: isActive ? Colors.white : IcsColors.textMutedDark,
                        ),
                      ),
              ),
            ),
            const SizedBox(height: 4),
            Text(
              labels[index],
              style: TextStyle(
                fontSize: 10,
                color: isActive ? Colors.white : IcsColors.textMutedDark,
                fontWeight: isActive ? FontWeight.w600 : FontWeight.w400,
              ),
            ),
          ],
        );
      }),
    );
  }
}

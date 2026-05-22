import 'package:flutter/material.dart';
import '../tokens/tokens.dart';

enum IcheboButtonVariant { primary, secondary, danger, ghost }

class IcheboButton extends StatelessWidget {
  const IcheboButton({
    super.key,
    required this.label,
    required this.onPressed,
    this.variant = IcheboButtonVariant.primary,
    this.loading = false,
    this.icon,
    this.expand = true,
  });

  final String label;
  final VoidCallback? onPressed;
  final IcheboButtonVariant variant;
  final bool loading;
  final IconData? icon;

  /// When true (default) the button fills available width.
  final bool expand;

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    Widget child = loading
        ? SizedBox(
            width: 20,
            height: 20,
            child: CircularProgressIndicator(
              strokeWidth: 2,
              color: _fgColor(isDark),
            ),
          )
        : Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              if (icon != null) ...[
                Icon(icon, size: 18),
                const SizedBox(width: IcheboSpacing.xs3),
              ],
              Text(label),
            ],
          );

    final minSize = expand
        ? const Size(double.infinity, kMinTouchTarget)
        : const Size(0, kMinTouchTarget);

    switch (variant) {
      case IcheboButtonVariant.primary:
        return ElevatedButton(
          onPressed: loading ? null : onPressed,
          style: ElevatedButton.styleFrom(
            backgroundColor: IcheboColors.primary,
            foregroundColor: Colors.white,
            minimumSize: minSize,
            shape: const RoundedRectangleBorder(borderRadius: IcheboRadius.m),
            textStyle: IcheboTextStyles.labelLarge,
          ),
          child: child,
        );

      case IcheboButtonVariant.secondary:
        return OutlinedButton(
          onPressed: loading ? null : onPressed,
          style: OutlinedButton.styleFrom(
            foregroundColor: IcheboColors.primary,
            side: const BorderSide(color: IcheboColors.primary),
            minimumSize: minSize,
            shape: const RoundedRectangleBorder(borderRadius: IcheboRadius.m),
            textStyle: IcheboTextStyles.labelLarge,
          ),
          child: child,
        );

      case IcheboButtonVariant.danger:
        return ElevatedButton(
          onPressed: loading ? null : onPressed,
          style: ElevatedButton.styleFrom(
            backgroundColor: isDark ? IcheboColors.errorDark : IcheboColors.error,
            foregroundColor: Colors.white,
            minimumSize: minSize,
            shape: const RoundedRectangleBorder(borderRadius: IcheboRadius.m),
            textStyle: IcheboTextStyles.labelLarge,
          ),
          child: child,
        );

      case IcheboButtonVariant.ghost:
        return TextButton(
          onPressed: loading ? null : onPressed,
          style: TextButton.styleFrom(
            foregroundColor: IcheboColors.primary,
            minimumSize: minSize,
            shape: const RoundedRectangleBorder(borderRadius: IcheboRadius.m),
            textStyle: IcheboTextStyles.labelLarge,
          ),
          child: child,
        );
    }
  }

  Color _fgColor(bool isDark) {
    switch (variant) {
      case IcheboButtonVariant.primary:
      case IcheboButtonVariant.danger:
        return Colors.white;
      case IcheboButtonVariant.secondary:
      case IcheboButtonVariant.ghost:
        return IcheboColors.primary;
    }
  }
}

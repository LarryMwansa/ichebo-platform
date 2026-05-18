import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../tokens/tokens.dart';

/// Dark-ink app bar matching the web page-hero pattern.
/// Always ink background, always light foreground — does not invert in light mode.
class IcheboAppBar extends StatelessWidget implements PreferredSizeWidget {
  const IcheboAppBar({
    super.key,
    required this.title,
    this.subtitle,
    this.actions,
    this.leading,
    this.showBack = false,
    this.watermarkText,
  });

  final String title;
  final String? subtitle;
  final List<Widget>? actions;
  final Widget? leading;
  final bool showBack;

  /// Optional ghost watermark text (The Ghost Watermark pattern from DESIGN.md).
  final String? watermarkText;

  @override
  Size get preferredSize => const Size.fromHeight(56);

  @override
  Widget build(BuildContext context) {
    return AnnotatedRegion<SystemUiOverlayStyle>(
      value: SystemUiOverlayStyle.light,
      child: Container(
        height: preferredSize.height,
        color: IcheboColors.ink,
        child: Stack(
          children: [
            // Ghost watermark
            if (watermarkText != null)
              Positioned(
                right: -8,
                top: -4,
                child: Text(
                  watermarkText!,
                  style: IcheboTextStyles.displayLarge.copyWith(
                    color: IcheboColors.stone.withValues(alpha: 0.05),
                    fontSize: 56,
                  ),
                ),
              ),
            SafeArea(
              bottom: false,
              child: Row(
                children: [
                  if (showBack)
                    IconButton(
                      icon: const Icon(Icons.arrow_back, color: IcheboColors.stone),
                      onPressed: () => Navigator.of(context).maybePop(),
                      tooltip: 'Back',
                    )
                  else if (leading != null)
                    leading!
                  else
                    const SizedBox(width: IcheboSpacing.s),
                  Expanded(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          title,
                          style: IcheboTextStyles.titleLarge.copyWith(
                            color: IcheboColors.stone,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                        if (subtitle != null)
                          Text(
                            subtitle!,
                            style: IcheboTextStyles.bodySmall.copyWith(
                              color: IcheboColors.stone.withValues(alpha: 0.55),
                            ),
                          ),
                      ],
                    ),
                  ),
                  if (actions != null) ...actions!,
                  const SizedBox(width: IcheboSpacing.xs3),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

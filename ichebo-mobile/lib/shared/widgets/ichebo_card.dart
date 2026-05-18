import 'package:flutter/material.dart';
import '../tokens/tokens.dart';

/// Standard 12dp-radius card. Optionally shows the Left Red Rule accent.
class IcheboCard extends StatelessWidget {
  const IcheboCard({
    super.key,
    required this.child,
    this.accent = false,
    this.padding,
    this.onTap,
    this.color,
  });

  final Widget child;

  /// When true, renders the Left Red Rule (3px left border in primary red).
  final bool accent;

  final EdgeInsetsGeometry? padding;
  final VoidCallback? onTap;
  final Color? color;

  @override
  Widget build(BuildContext context) {
    final surface = color ?? Theme.of(context).colorScheme.surface;
    final content = Padding(
      padding: padding ?? const EdgeInsets.all(IcheboSpacing.s),
      child: child,
    );

    Widget card = Container(
      decoration: BoxDecoration(
        color: surface,
        borderRadius: IcheboRadius.l,
        border: accent
            ? const Border(
                left: BorderSide(color: IcheboColors.primary, width: 3),
              )
            : null,
      ),
      clipBehavior: accent ? Clip.none : Clip.antiAlias,
      child: content,
    );

    if (onTap != null) {
      card = InkWell(
        onTap: onTap,
        borderRadius: IcheboRadius.l,
        child: card,
      );
    }

    return card;
  }
}

/// Dark ink card — used for heroes and highlighted sections.
class IcheboCardDark extends StatelessWidget {
  const IcheboCardDark({
    super.key,
    required this.child,
    this.padding,
    this.onTap,
  });

  final Widget child;
  final EdgeInsetsGeometry? padding;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return IcheboCard(
      color: IcheboColors.ink2,
      padding: padding,
      onTap: onTap,
      child: child,
    );
  }
}

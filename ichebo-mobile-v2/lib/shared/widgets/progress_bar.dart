import 'package:flutter/material.dart';
import '../tokens/tokens.dart';

class IcheboProgressBar extends StatelessWidget {
  const IcheboProgressBar({
    super.key,
    required this.value,
    this.height = 6.0,
    this.color,
    this.label,
  });

  /// 0.0 to 1.0
  final double value;
  final double height;
  final Color? color;
  final String? label;

  @override
  Widget build(BuildContext context) {
    final fill = color ?? IcheboColors.primary;
    final track = Theme.of(context).brightness == Brightness.dark
        ? IcheboColors.inkLight
        : IcheboColors.stone2;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        if (label != null) ...[
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                label!,
                style: IcheboTextStyles.bodySmall.copyWith(
                  color: IcheboColors.muted,
                ),
              ),
              Text(
                '${(value * 100).round()}%',
                style: IcheboTextStyles.labelCaps.copyWith(
                  color: fill,
                  fontSize: 10,
                ),
              ),
            ],
          ),
          const SizedBox(height: IcheboSpacing.xs3),
        ],
        ClipRRect(
          borderRadius: IcheboRadius.pill,
          child: LinearProgressIndicator(
            value: value.clamp(0.0, 1.0),
            minHeight: height,
            backgroundColor: track,
            color: fill,
          ),
        ),
      ],
    );
  }
}

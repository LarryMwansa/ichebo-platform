import 'package:flutter/material.dart';
import '../core/theme/tokens.dart';

// ── Toast model ───────────────────────────────────────────────────────────────

enum ToastLevel { success, error, warning, info }

class ToastMessage {
  ToastMessage({
    required this.message,
    this.level = ToastLevel.success,
  }) : id = UniqueKey();

  final Key id;
  final String message;
  final ToastLevel level;
}

// ── Global notifier (simple ValueNotifier — no Riverpod needed) ───────────────

final toastNotifier = _ToastNotifier();

class _ToastNotifier extends ChangeNotifier {
  final List<ToastMessage> _toasts = [];
  List<ToastMessage> get toasts => List.unmodifiable(_toasts);

  void show(String message, {ToastLevel level = ToastLevel.success}) {
    final toast = ToastMessage(message: message, level: level);
    _toasts.add(toast);
    notifyListeners();
    Future.delayed(IcsDuration.toast, () => dismiss(toast.id));
  }

  void dismiss(Key id) {
    _toasts.removeWhere((t) => t.id == id);
    notifyListeners();
  }
}

// ── Toast container overlay (rendered at root above all other content) ────────

class ToastContainer extends StatefulWidget {
  const ToastContainer({super.key});

  @override
  State<ToastContainer> createState() => _ToastContainerState();
}

class _ToastContainerState extends State<ToastContainer> {
  @override
  void initState() {
    super.initState();
    toastNotifier.addListener(_onUpdate);
  }

  @override
  void dispose() {
    toastNotifier.removeListener(_onUpdate);
    super.dispose();
  }

  void _onUpdate() => setState(() {});

  @override
  Widget build(BuildContext context) {
    if (toastNotifier.toasts.isEmpty) return const SizedBox.shrink();

    return Positioned(
      bottom: IcsSpacing.xl,
      right: IcsSpacing.xl,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.end,
        children: toastNotifier.toasts
            .map((t) => _ToastItem(
                  key: t.id,
                  toast: t,
                  onDismiss: () => toastNotifier.dismiss(t.id),
                ))
            .toList(),
      ),
    );
  }
}

// ── Individual toast ──────────────────────────────────────────────────────────

class _ToastItem extends StatefulWidget {
  const _ToastItem({
    super.key,
    required this.toast,
    required this.onDismiss,
  });
  final ToastMessage toast;
  final VoidCallback onDismiss;

  @override
  State<_ToastItem> createState() => _ToastItemState();
}

class _ToastItemState extends State<_ToastItem>
    with SingleTickerProviderStateMixin {
  late final AnimationController _ctrl;
  late final Animation<Offset> _slide;
  late final Animation<double> _fade;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 200),
    );
    _slide = Tween<Offset>(
      begin: const Offset(0, 0.3),
      end: Offset.zero,
    ).animate(CurvedAnimation(parent: _ctrl, curve: Curves.easeOut));
    _fade = CurvedAnimation(parent: _ctrl, curve: Curves.easeOut);
    _ctrl.forward();
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(top: IcsSpacing.s),
      child: FadeTransition(
        opacity: _fade,
        child: SlideTransition(
          position: _slide,
          child: _ToastCard(toast: widget.toast, onDismiss: widget.onDismiss),
        ),
      ),
    );
  }
}

class _ToastCard extends StatelessWidget {
  const _ToastCard({required this.toast, required this.onDismiss});
  final ToastMessage toast;
  final VoidCallback onDismiss;

  static const _icons = {
    ToastLevel.success: Icons.check_circle_outline,
    ToastLevel.error: Icons.error_outline,
    ToastLevel.warning: Icons.warning_amber_outlined,
    ToastLevel.info: Icons.info_outline,
  };

  static const _colors = {
    ToastLevel.success: IcsColors.success,
    ToastLevel.error: IcsColors.error,
    ToastLevel.warning: IcsColors.warning,
    ToastLevel.info: IcsColors.info,
  };

  @override
  Widget build(BuildContext context) {
    final color = _colors[toast.level]!;
    final icon = _icons[toast.level]!;

    return Container(
      constraints: const BoxConstraints(minWidth: 280, maxWidth: 400),
      padding: const EdgeInsets.symmetric(
        horizontal: IcsSpacing.l,
        vertical: IcsSpacing.m,
      ),
      decoration: BoxDecoration(
        color: const Color(0xFF1E1E1E),
        borderRadius: BorderRadius.all(IcsRadius.m),
        border: Border.all(color: Colors.white.withValues(alpha: 0.08)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.3),
            blurRadius: 20,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Row(
        children: [
          Icon(icon, color: color, size: 18),
          const SizedBox(width: IcsSpacing.m),
          Expanded(
            child: Text(
              toast.message,
              style: const TextStyle(
                color: Colors.white,
                fontSize: 13,
                height: 1.4,
              ),
            ),
          ),
          const SizedBox(width: IcsSpacing.s),
          GestureDetector(
            onTap: onDismiss,
            child: Icon(
              Icons.close,
              size: 16,
              color: Colors.white.withValues(alpha: 0.4),
            ),
          ),
        ],
      ),
    );
  }
}

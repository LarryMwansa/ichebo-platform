import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/api/providers.dart';
import '../../shared/tokens/tokens.dart';
import '../../shared/widgets/badges.dart';
import '../../shared/widgets/empty_state.dart';
import '../../shared/widgets/ichebo_app_bar.dart';

// Local state providers for current book/chapter/translation selection.
final _selectedTranslationProvider = StateProvider.autoDispose<String?>((ref) => null);
final _selectedBookProvider = StateProvider.autoDispose<BibleBook?>((ref) => null);
final _selectedChapterProvider = StateProvider.autoDispose<int?>((ref) => null);

class BibleScreen extends ConsumerWidget {
  const BibleScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final selectedBook = ref.watch(_selectedBookProvider);
    final selectedChapter = ref.watch(_selectedChapterProvider);

    return Scaffold(
      appBar: IcheboAppBar(
        title: selectedBook != null
            ? '${selectedBook.name} ${selectedChapter ?? ''}'
            : 'Bible',
        watermarkText: 'SCRIPTURE',
        actions: [
          IconButton(
            icon: const Icon(Icons.search, color: IcheboColors.stone),
            onPressed: () {}, // search deferred
            tooltip: 'Search',
          ),
          _TranslationChip(),
        ],
      ),
      body: selectedBook == null
          ? const _BookList()
          : selectedChapter == null
              ? _ChapterList(book: selectedBook)
              : _VerseList(book: selectedBook, chapter: selectedChapter),
    );
  }
}

// ── Translation picker chip ───────────────────────────────────────────────────

class _TranslationChip extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final translationsAsync = ref.watch(bibleTranslationsProvider);
    final selected = ref.watch(_selectedTranslationProvider);

    return translationsAsync.maybeWhen(
      data: (translations) {
        final current = translations.firstWhere(
          (t) => t.code == selected,
          orElse: () => translations.firstWhere(
            (t) => t.isDefault,
            orElse: () => translations.first,
          ),
        );
        return Padding(
          padding: const EdgeInsets.only(right: IcheboSpacing.xs),
          child: GestureDetector(
            onTap: () => _showTranslationSheet(context, ref, translations, current.code),
            child: Container(
              padding: const EdgeInsets.symmetric(
                horizontal: IcheboSpacing.xs,
                vertical: IcheboSpacing.xs3,
              ),
              decoration: BoxDecoration(
                border: Border.all(color: IcheboColors.primary),
                borderRadius: IcheboRadius.pill,
              ),
              child: Text(
                current.code,
                style: IcheboTextStyles.labelCaps.copyWith(
                  color: IcheboColors.primary,
                  fontSize: 10,
                ),
              ),
            ),
          ),
        );
      },
      orElse: () => const SizedBox.shrink(),
    );
  }

  void _showTranslationSheet(BuildContext context, WidgetRef ref,
      List<BibleTranslation> translations, String currentCode) {
    showModalBottomSheet(
      context: context,
      shape: const RoundedRectangleBorder(borderRadius: IcheboRadius.xl2),
      builder: (_) => Padding(
        padding: const EdgeInsets.all(IcheboSpacing.s),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const LabelTag(label: 'Translation'),
            const SizedBox(height: IcheboSpacing.s),
            ...translations.map(
              (t) => ListTile(
                title: Text(t.name),
                trailing: t.code == currentCode
                    ? const Icon(Icons.check, color: IcheboColors.primary)
                    : null,
                onTap: () {
                  ref.read(_selectedTranslationProvider.notifier).state = t.code;
                  Navigator.pop(context);
                },
              ),
            ),
            const SizedBox(height: IcheboSpacing.s),
          ],
        ),
      ),
    );
  }
}

// ── Book list ─────────────────────────────────────────────────────────────────

class _BookList extends ConsumerWidget {
  const _BookList();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final booksAsync = ref.watch(bibleBooksProvider);

    return booksAsync.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (e, _) => EmptyState(message: e.toString()),
      data: (books) {
        final ot = books.where((b) => b.testament == 'OT').toList();
        final nt = books.where((b) => b.testament == 'NT').toList();

        return ListView(
          children: [
            _TestamentHeader(label: 'Old Testament'),
            ..._bookTiles(context, ref, ot),
            _TestamentHeader(label: 'New Testament'),
            ..._bookTiles(context, ref, nt),
          ],
        );
      },
    );
  }

  List<Widget> _bookTiles(BuildContext context, WidgetRef ref, List<BibleBook> books) {
    return books.map((book) => ListTile(
          title: Text(book.name),
          trailing: const Icon(Icons.chevron_right, size: 18),
          onTap: () {
            ref.read(_selectedBookProvider.notifier).state = book;
            ref.read(_selectedChapterProvider.notifier).state = null;
          },
        )).toList();
  }
}

class _TestamentHeader extends StatelessWidget {
  const _TestamentHeader({required this.label});
  final String label;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(
          IcheboSpacing.s, IcheboSpacing.m, IcheboSpacing.s, IcheboSpacing.xs3),
      child: LabelTag(label: label),
    );
  }
}

// ── Chapter list ──────────────────────────────────────────────────────────────

class _ChapterList extends ConsumerWidget {
  const _ChapterList({required this.book});
  final BibleBook book;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final chaptersAsync = ref.watch(bibleChaptersProvider(book.code));

    return chaptersAsync.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (e, _) => EmptyState(message: e.toString()),
      data: (chapters) => GridView.builder(
        padding: const EdgeInsets.all(IcheboSpacing.s),
        gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
          crossAxisCount: 6,
          crossAxisSpacing: IcheboSpacing.xs3,
          mainAxisSpacing: IcheboSpacing.xs3,
          childAspectRatio: 1,
        ),
        itemCount: chapters.length,
        itemBuilder: (context, i) {
          final ch = chapters[i];
          return InkWell(
            borderRadius: IcheboRadius.m,
            onTap: () => ref.read(_selectedChapterProvider.notifier).state = ch,
            child: Container(
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.surface,
                borderRadius: IcheboRadius.m,
              ),
              alignment: Alignment.center,
              child: Text(
                '$ch',
                style: Theme.of(context).textTheme.titleMedium,
              ),
            ),
          );
        },
      ),
    );
  }
}

// ── Verse list ────────────────────────────────────────────────────────────────

class _VerseList extends ConsumerWidget {
  const _VerseList({required this.book, required this.chapter});
  final BibleBook book;
  final int chapter;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final translationCode = ref.watch(_selectedTranslationProvider);
    final params = <String, String>{
      'book_code': book.code,
      'chapter': '$chapter',
      if (translationCode != null) 'translation_code': translationCode,
    };
    final versesAsync = ref.watch(bibleVersesProvider(params));

    return versesAsync.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (e, _) => EmptyState(message: e.toString()),
      data: (verses) => ListView.builder(
        padding: const EdgeInsets.symmetric(
          horizontal: IcheboSpacing.s,
          vertical: IcheboSpacing.xs,
        ),
        itemCount: verses.length,
        itemBuilder: (context, i) {
          final v = verses[i];
          return Padding(
            padding: const EdgeInsets.symmetric(vertical: IcheboSpacing.xs3),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                SizedBox(
                  width: 28,
                  child: Text(
                    '${v.verse}',
                    style: IcheboTextStyles.labelCaps.copyWith(
                      color: IcheboColors.primary,
                      fontSize: 10,
                    ),
                  ),
                ),
                Expanded(
                  child: Text(
                    v.text,
                    style: Theme.of(context)
                        .textTheme
                        .bodyLarge
                        ?.copyWith(height: 1.7),
                  ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}

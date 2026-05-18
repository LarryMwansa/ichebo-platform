import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/api/api_client.dart';
import '../../core/api/providers.dart';
import '../../shared/tokens/tokens.dart';
import '../../shared/widgets/badges.dart';
import '../../shared/widgets/empty_state.dart';
import '../../shared/widgets/ichebo_app_bar.dart';
import '../../shared/widgets/ichebo_button.dart';

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
        itemBuilder: (context, i) => _VerseTile(
          verse: verses[i],
          bookCode: book.code,
        ),
      ),
    );
  }
}

// ── Verse tile with note icon ─────────────────────────────────────────────────

class _VerseTile extends StatelessWidget {
  const _VerseTile({required this.verse, required this.bookCode});
  final BibleVerse verse;
  final String bookCode;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: IcheboSpacing.xs3),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 28,
            child: Text(
              '${verse.verse}',
              style: IcheboTextStyles.labelCaps.copyWith(
                color: IcheboColors.primary,
                fontSize: 10,
              ),
            ),
          ),
          Expanded(
            child: Text(
              verse.text,
              style: Theme.of(context).textTheme.bodyLarge?.copyWith(height: 1.7),
            ),
          ),
          GestureDetector(
            onTap: () => _openNotes(context),
            child: const Padding(
              padding: EdgeInsets.only(left: IcheboSpacing.xs3, top: 4),
              child: Icon(Icons.edit_note_outlined,
                  size: 18, color: IcheboColors.mutedLight),
            ),
          ),
        ],
      ),
    );
  }

  void _openNotes(BuildContext context) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(borderRadius: IcheboRadius.xl2),
      builder: (_) => _VerseNoteSheet(
        bookCode: bookCode,
        chapter: verse.chapter,
        verseNum: verse.verse,
        bookName: verse.bookName,
      ),
    );
  }
}

// ── Verse note bottom sheet ───────────────────────────────────────────────────

class _VerseNoteSheet extends ConsumerStatefulWidget {
  const _VerseNoteSheet({
    required this.bookCode,
    required this.chapter,
    required this.verseNum,
    required this.bookName,
  });
  final String bookCode;
  final int chapter;
  final int verseNum;
  final String bookName;

  @override
  ConsumerState<_VerseNoteSheet> createState() => _VerseNoteSheetState();
}

class _VerseNoteSheetState extends ConsumerState<_VerseNoteSheet> {
  final _noteCtrl = TextEditingController();
  bool _saving = false;
  bool _showCreate = false;

  String get _verseRef =>
      '${widget.bookCode} ${widget.chapter}:${widget.verseNum}';

  Map<String, String> get _params => {
        'book_code': widget.bookCode,
        'chapter': '${widget.chapter}',
        'verse': '${widget.verseNum}',
      };

  @override
  void dispose() {
    _noteCtrl.dispose();
    super.dispose();
  }

  Future<void> _saveNote() async {
    final text = _noteCtrl.text.trim();
    if (text.isEmpty) return;
    setState(() => _saving = true);
    try {
      await ref.read(apiClientProvider).post<void>(
        'records/',
        data: {
          'record_family': 'bible',
          'record_type': 'bible_note',
          'record_class': 'personal',
          'title': _verseRef,
          'summary': text,
          'verse_ref': _verseRef,
        },
      );
      ref.invalidate(bibleNotesProvider(_params));
      _noteCtrl.clear();
      if (mounted) setState(() => _showCreate = false);
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Could not save note. Please try again.')),
        );
      }
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final notesAsync = ref.watch(bibleNotesProvider(_params));

    return Padding(
      padding: EdgeInsets.only(
        left: IcheboSpacing.s,
        right: IcheboSpacing.s,
        top: IcheboSpacing.s,
        bottom: MediaQuery.of(context).viewInsets.bottom + IcheboSpacing.m,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // ── Header ────────────────────────────────────────────────────
          Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Notes', style: IcheboTextStyles.titleLarge),
                    Text(
                      '${widget.bookName} ${widget.chapter}:${widget.verseNum}',
                      style: IcheboTextStyles.bodySmall
                          .copyWith(color: IcheboColors.muted),
                    ),
                  ],
                ),
              ),
              IconButton(
                icon: const Icon(Icons.close),
                onPressed: () => Navigator.pop(context),
              ),
            ],
          ),
          const SizedBox(height: IcheboSpacing.xs),

          // ── Existing notes ────────────────────────────────────────────
          notesAsync.when(
            loading: () => const Padding(
              padding: EdgeInsets.symmetric(vertical: IcheboSpacing.s),
              child: Center(child: CircularProgressIndicator()),
            ),
            error: (e, s) => const SizedBox.shrink(),
            data: (notes) => notes.isEmpty
                ? Padding(
                    padding: const EdgeInsets.symmetric(
                        vertical: IcheboSpacing.xs),
                    child: Text(
                      'No notes yet for this verse.',
                      style: IcheboTextStyles.bodySmall
                          .copyWith(color: IcheboColors.mutedLight),
                    ),
                  )
                : Column(
                    children: notes
                        .map((n) => _NoteItem(
                            note: n, params: _params, ref: ref))
                        .toList(),
                  ),
          ),

          // ── Create note ───────────────────────────────────────────────
          if (_showCreate) ...[
            const SizedBox(height: IcheboSpacing.xs),
            TextField(
              controller: _noteCtrl,
              maxLines: 3,
              autofocus: true,
              decoration: const InputDecoration(
                hintText: 'Write your note…',
                border: OutlineInputBorder(borderRadius: IcheboRadius.m),
              ),
            ),
            const SizedBox(height: IcheboSpacing.xs),
            Row(
              children: [
                Expanded(
                  child: IcheboButton(
                    label: 'Save note',
                    onPressed: _saveNote,
                    loading: _saving,
                  ),
                ),
                const SizedBox(width: IcheboSpacing.xs),
                IcheboButton(
                  label: 'Cancel',
                  onPressed: () => setState(() {
                    _showCreate = false;
                    _noteCtrl.clear();
                  }),
                  variant: IcheboButtonVariant.ghost,
                  expand: false,
                ),
              ],
            ),
          ] else ...[
            const SizedBox(height: IcheboSpacing.xs),
            IcheboButton(
              label: 'Add note',
              icon: Icons.add,
              onPressed: () => setState(() => _showCreate = true),
              variant: IcheboButtonVariant.secondary,
            ),
          ],
        ],
      ),
    );
  }
}

// ── Note item (with soft-delete) ──────────────────────────────────────────────

class _NoteItem extends StatelessWidget {
  const _NoteItem({
    required this.note,
    required this.params,
    required this.ref,
  });
  final BibleNote note;
  final Map<String, String> params;
  final WidgetRef ref;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: IcheboSpacing.xs3),
      child: Container(
        padding: const EdgeInsets.all(IcheboSpacing.xs),
        decoration: BoxDecoration(
          color: Theme.of(context).colorScheme.surfaceContainerHighest,
          borderRadius: IcheboRadius.m,
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Expanded(
              child: Text(note.summary,
                  style: Theme.of(context).textTheme.bodyMedium),
            ),
            const SizedBox(width: IcheboSpacing.xs3),
            GestureDetector(
              onTap: () => _delete(context),
              child: const Icon(Icons.delete_outline,
                  size: 16, color: IcheboColors.mutedLight),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _delete(BuildContext context) async {
    try {
      await ref.read(apiClientProvider).patch<void>(
        'records/${note.id}/',
        data: {'deleted_at': DateTime.now().toUtc().toIso8601String()},
      );
      ref.invalidate(bibleNotesProvider(params));
    } catch (_) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Could not delete note.')),
        );
      }
    }
  }
}

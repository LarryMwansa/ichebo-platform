import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/theme/tokens.dart';
import 'bible_providers.dart';

class BibleScreen extends ConsumerWidget {
  const BibleScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final location = ref.watch(bibleLocationProvider);
    if (location != null) return _ReadingView(location: location);
    return const _BookListView();
  }
}

// ── Book list ─────────────────────────────────────────────────────────────────

class _BookListView extends ConsumerWidget {
  const _BookListView();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final books = ref.watch(bibleBooksProvider);

    return Scaffold(
      backgroundColor: IcsColors.inkBg,
      appBar: AppBar(
        backgroundColor: IcsColors.stone1,
        title: const Text('Bible'),
        actions: [
          IconButton(
            icon: const Icon(Icons.search),
            onPressed: () => _showSearchBar(context, ref),
          ),
        ],
      ),
      body: books.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, st) => _ErrorView(message: e.toString()),
        data: (list) {
          final ot = list.where((b) => b.testament == 'OT').toList();
          final nt = list.where((b) => b.testament == 'NT').toList();

          return ListView(
            padding: const EdgeInsets.all(IcsSpacing.m),
            children: [
              _TestamentSection(label: 'Old Testament', books: ot, ref: ref),
              const SizedBox(height: IcsSpacing.l),
              _TestamentSection(label: 'New Testament', books: nt, ref: ref),
              const SizedBox(height: IcsSpacing.xl),
            ],
          );
        },
      ),
    );
  }

  void _showSearchBar(BuildContext context, WidgetRef ref) {
    showSearch(
      context: context,
      delegate: _BibleSearchDelegate(ref),
    );
  }
}

class _TestamentSection extends StatelessWidget {
  const _TestamentSection({
    required this.label,
    required this.books,
    required this.ref,
  });
  final String         label;
  final List<BibleBook> books;
  final WidgetRef      ref;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.only(bottom: IcsSpacing.s),
          child: Text(
            label.toUpperCase(),
            style: const TextStyle(
              color: IcsColors.textMuted,
              fontSize: 11,
              letterSpacing: 1.2,
              fontWeight: FontWeight.w600,
            ),
          ),
        ),
        Wrap(
          spacing: IcsSpacing.s,
          runSpacing: IcsSpacing.s,
          children: books.map((b) => _BookChip(book: b, ref: ref)).toList(),
        ),
      ],
    );
  }
}

class _BookChip extends StatelessWidget {
  const _BookChip({required this.book, required this.ref});
  final BibleBook book;
  final WidgetRef ref;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: () => ref.read(bibleLocationProvider.notifier).state =
          BibleLocation(
            bookCode: book.code,
            bookName: book.name,
            chapter:  1,
          ),
      borderRadius: BorderRadius.circular(6),
      child: Container(
        padding: const EdgeInsets.symmetric(
            horizontal: IcsSpacing.m, vertical: IcsSpacing.s),
        decoration: BoxDecoration(
          color: IcsColors.stone1,
          borderRadius: BorderRadius.circular(6),
          border: Border.all(color: IcsColors.borderDark),
        ),
        child: Text(
          book.name,
          style: const TextStyle(color: Colors.white, fontSize: 13),
        ),
      ),
    );
  }
}

// ── Chapter picker + reading view ─────────────────────────────────────────────

class _ReadingView extends ConsumerWidget {
  const _ReadingView({required this.location});
  final BibleLocation location;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final chaptersAsync = ref.watch(bibleChaptersProvider(location.bookCode));
    final versesAsync   = ref.watch(bibleVersesProvider(location));

    return Scaffold(
      backgroundColor: IcsColors.inkBg,
      appBar: AppBar(
        backgroundColor: IcsColors.stone1,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () =>
              ref.read(bibleLocationProvider.notifier).state = null,
        ),
        title: Text('${location.bookName} ${location.chapter}'),
        actions: [
          IconButton(
            icon: const Icon(Icons.search),
            onPressed: () => _showSearchBar(context, ref),
          ),
        ],
      ),
      body: Column(
        children: [
          // Chapter selector
          chaptersAsync.when(
            loading: () => const SizedBox(height: 40),
            error:   (_, st) => const SizedBox(height: 40),
            data: (chapters) => _ChapterBar(
              chapters: chapters,
              current:  location.chapter,
              onSelect: (ch) => ref
                  .read(bibleLocationProvider.notifier)
                  .state = location.copyWith(chapter: ch),
            ),
          ),
          const Divider(height: 1, color: IcsColors.borderDark),
          // Verse content
          Expanded(
            child: versesAsync.when(
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (e, st) => _ErrorView(message: e.toString()),
              data: (verses) {
                if (verses.isEmpty) {
                  return const Center(
                    child: Text('No verses found',
                        style: TextStyle(color: IcsColors.textMuted)),
                  );
                }
                return ListView.builder(
                  padding: const EdgeInsets.all(IcsSpacing.m),
                  itemCount: verses.length,
                  itemBuilder: (_, i) => _VerseRow(verse: verses[i]),
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  void _showSearchBar(BuildContext context, WidgetRef ref) {
    showSearch(
      context: context,
      delegate: _BibleSearchDelegate(ref),
    );
  }
}

class _ChapterBar extends StatelessWidget {
  const _ChapterBar({
    required this.chapters,
    required this.current,
    required this.onSelect,
  });
  final List<int>          chapters;
  final int                current;
  final ValueChanged<int>  onSelect;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 44,
      child: ListView.builder(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(
            horizontal: IcsSpacing.m, vertical: IcsSpacing.xs),
        itemCount: chapters.length,
        itemBuilder: (_, i) {
          final ch       = chapters[i];
          final selected = ch == current;
          return Padding(
            padding: const EdgeInsets.only(right: IcsSpacing.xs),
            child: GestureDetector(
              onTap: () => onSelect(ch),
              child: Container(
                width: 36,
                alignment: Alignment.center,
                decoration: BoxDecoration(
                  color: selected
                      ? IcsColors.accentBlue
                      : IcsColors.stone1,
                  borderRadius: BorderRadius.circular(4),
                  border: Border.all(
                    color: selected
                        ? IcsColors.accentBlue
                        : IcsColors.borderDark,
                  ),
                ),
                child: Text(
                  '$ch',
                  style: TextStyle(
                    color: selected ? Colors.white : IcsColors.textMuted,
                    fontSize: 12,
                  ),
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}

class _VerseRow extends StatelessWidget {
  const _VerseRow({required this.verse});
  final BibleVerse verse;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: IcsSpacing.m),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 28,
            child: Text(
              '${verse.verse}',
              style: const TextStyle(
                  color: IcsColors.accentBlue,
                  fontSize: 11,
                  fontWeight: FontWeight.w600),
            ),
          ),
          Expanded(
            child: Text(
              verse.text,
              style: const TextStyle(
                  color: Colors.white, fontSize: 16, height: 1.6),
            ),
          ),
        ],
      ),
    );
  }
}

// ── Search ────────────────────────────────────────────────────────────────────

class _BibleSearchDelegate extends SearchDelegate<void> {
  _BibleSearchDelegate(this.ref);
  final WidgetRef ref;

  @override
  ThemeData appBarTheme(BuildContext context) => Theme.of(context).copyWith(
    appBarTheme: const AppBarTheme(backgroundColor: IcsColors.stone1),
    inputDecorationTheme: const InputDecorationTheme(
      hintStyle: TextStyle(color: IcsColors.textMuted),
    ),
  );

  @override
  List<Widget> buildActions(BuildContext context) => [
    if (query.isNotEmpty)
      IconButton(
        icon: const Icon(Icons.clear),
        onPressed: () => query = '',
      ),
  ];

  @override
  Widget buildLeading(BuildContext context) => IconButton(
    icon: const Icon(Icons.arrow_back),
    onPressed: () => close(context, null),
  );

  @override
  Widget buildResults(BuildContext context) => _SearchResultsView(
    query: query,
    ref: ref,
    onSelect: (result) {
      close(context, null);
      ref.read(bibleLocationProvider.notifier).state = BibleLocation(
        bookCode: result.bookCode,
        bookName: result.bookName,
        chapter:  result.chapter,
      );
    },
  );

  @override
  Widget buildSuggestions(BuildContext context) {
    if (query.length < 2) {
      return const Center(
        child: Text('Type at least 2 characters',
            style: TextStyle(color: IcsColors.textMuted)),
      );
    }
    return buildResults(context);
  }
}

class _SearchResultsView extends ConsumerWidget {
  const _SearchResultsView({
    required this.query,
    required this.ref,
    required this.onSelect,
  });
  final String                    query;
  final WidgetRef                 ref;
  final ValueChanged<SearchResult> onSelect;

  @override
  Widget build(BuildContext context, WidgetRef watchRef) {
    final results = watchRef.watch(bibleSearchProvider(query));
    return ColoredBox(
      color: IcsColors.inkBg,
      child: results.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error:   (e, st) => _ErrorView(message: e.toString()),
        data: (list) {
          if (list.isEmpty) {
            return Center(
              child: Text('No results for "$query"',
                  style: const TextStyle(color: IcsColors.textMuted)),
            );
          }
          return ListView.separated(
            padding: const EdgeInsets.all(IcsSpacing.m),
            itemCount: list.length,
            separatorBuilder: (_, i) =>
                const Divider(height: 1, color: IcsColors.borderDark),
            itemBuilder: (_, i) => _SearchResultTile(
              result: list[i],
              onTap:  () => onSelect(list[i]),
            ),
          );
        },
      ),
    );
  }
}

class _SearchResultTile extends StatelessWidget {
  const _SearchResultTile({required this.result, required this.onTap});
  final SearchResult result;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return ListTile(
      onTap: onTap,
      contentPadding:
          const EdgeInsets.symmetric(vertical: IcsSpacing.s),
      title: Text(
        result.reference,
        style: const TextStyle(
            color: IcsColors.accentBlue,
            fontSize: 13,
            fontWeight: FontWeight.w500),
      ),
      subtitle: Text(
        result.text,
        maxLines: 2,
        overflow: TextOverflow.ellipsis,
        style: const TextStyle(color: Colors.white, fontSize: 14),
      ),
    );
  }
}

// ── Shared helpers ────────────────────────────────────────────────────────────

class _ErrorView extends StatelessWidget {
  const _ErrorView({required this.message});
  final String message;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(IcsSpacing.l),
        child: Text(
          message,
          style: const TextStyle(color: IcsColors.accentRed),
          textAlign: TextAlign.center,
        ),
      ),
    );
  }
}

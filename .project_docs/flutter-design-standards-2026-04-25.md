# Ichebo Platform — Flutter Mobile App: Design & Standards

**Version:** v1.0 — 2026-04-25
**Status:** Approved — Definitive Reference
**Scope:** Flutter Android-first mobile application
**Platform:** Android (primary); iOS deferred to Version 3
**API contract:** Ichebo Data Contract v10

This document is the single authoritative reference for all design and development standards on the Ichebo Flutter mobile app. Read this before writing the first screen. Every decision here is grounded in the web design system (Web UI Design & Standards v1.0) with Flutter-specific adaptations.

The Flutter app consumes the DRF API. It does not use HTMX. It does not render server-side HTML. It is a native Android app that talks to the same backend as the web application.

---

## Part 1 — Architecture Overview

### 1.1 Web vs Mobile — Side by Side

| Concern | Web (Django + HTMX) | Mobile (Flutter) |
|---------|--------------------|--------------------|
| Rendering | Server renders HTML; HTMX swaps fragments | Flutter renders native widgets client-side |
| Authentication | Django session cookies | DRF token stored in `shared_preferences` |
| Navigation | Django URLs + `@login_required` | `go_router` with level-based guards |
| State management | Django view context (server-side) | Riverpod providers (client-side) |
| Offline support | Not available in Version 2 | `sqflite` local SQLite cache + delta sync |
| Push notifications | Not available in Version 2 | Firebase Cloud Messaging (FCM) |

### 1.2 Project Structure

```
ichebo_mobile/
  lib/
    main.dart                   ← App entry point
    app.dart                    ← MaterialApp + GoRouter setup
    core/
      api/
        api_client.dart         ← Dio HTTP client (base URL, auth header)
        endpoints.dart          ← All API URL constants
      auth/
        auth_provider.dart      ← Riverpod: user state + token
      storage/
        local_db.dart           ← sqflite setup
        sync_service.dart       ← Delta sync logic
      theme/
        app_theme.dart          ← ThemeData: light + dark
        tokens.dart             ← All design tokens as Dart constants
      utils/
        video_utils.dart        ← getEmbedUrl() — mirrors web video.py
    features/
      auth/                     ← Login, register, forgot password
      home/                     ← Dashboard (Paraclete digest)
      bible/                    ← Scripture reader, annotations
      learn/                    ← Catalogue, enrolment, lesson viewer
      activity/                 ← My Activities, Ministry
      community/                ← Member directory, announcements, gatherings
      governance/               ← Reference Library, Mandate, Keys (Level 3+)
      profile/                  ← Formation journey, settings
      notifications/            ← Notification list
    widgets/                    ← Shared reusable widgets
      ichebo_card.dart
      level_badge.dart
      status_badge.dart
      progress_bar.dart
      empty_state.dart
      ichebo_button.dart
      list_item_tile.dart
  android/
    app/
      google-services.json      ← Firebase config (never commit to public repo)
  pubspec.yaml
```

---

## Part 2 — Design Tokens

All values from the web design system have a Flutter equivalent. Never use hardcoded colour values or sizes — always use the token constants defined in `tokens.dart`.

### 2.1 Colour Tokens

| Name | Web Token | Hex | Dart Constant |
|------|-----------|-----|---------------|
| Primary Red | `--primary` | `#AF3236` | `AppColors.primary` |
| Secondary Blue | `--secondary-light` | `#185ABC` | `AppColors.secondary` |
| Near Black | `--text` | `#1A1A1A` | `AppColors.textPrimary` |
| White | `--bg` | `#FFFFFF` | `AppColors.background` |
| Surface | `--card` | `#F8F9FA` | `AppColors.surface` |
| Border | `--border` | `#E9ECEF` | `AppColors.border` |
| Muted | `--muted` | `#6C757D` | `AppColors.textSecondary` |
| Hover/Pressed | `--hover` | `#F1F3F5` | `AppColors.pressed` |
| Success | `--success` | `#16A34A` | `AppColors.success` |
| Error | `--error` | `#DC2626` | `AppColors.error` |
| Warning | `--warning` | `#CA8A04` | `AppColors.warning` |
| Info | `--info` | `#0C5C9E` | `AppColors.info` |

### 2.2 Dark Mode Colour Tokens

| Dart Constant | Light Mode | Dark Mode |
|---------------|-----------|-----------|
| `AppColors.background` | `#FFFFFF` | `#121212` |
| `AppColors.surface` | `#F8F9FA` | `#1E1E1E` |
| `AppColors.textPrimary` | `#1A1A1A` | `#F5F5F5` |
| `AppColors.textSecondary` | `#6C757D` | `#AAAAAA` |
| `AppColors.border` | `#E9ECEF` | `rgba(255,255,255,0.08)` |
| `AppColors.pressed` | `#F1F3F5` | `#2A2A2A` |

In Flutter: define these in `ThemeData` using `ColorScheme`. Use `Theme.of(context).colorScheme` to access them in widgets — never hardcode `Color(0xFFAF3236)`.

### 2.3 Level Colours

| Level | KGS Name | Dart Constant | Hex |
|-------|----------|---------------|-----|
| 0 | Seeker | `AppColors.level0` | `#6C757D` |
| 1 | Foundational Disciple | `AppColors.level1` | `#16A34A` |
| 2 | Active Contributor | `AppColors.level2` | `#185ABC` |
| 3 | Functional Minister | `AppColors.level3` | `#7E22CE` |
| 4 | Leader | `AppColors.level4` | `#EA580C` |
| 5 | Apostolic Steward | `AppColors.level5` | `#AF3236` |

### 2.4 Typography Tokens

Typeface: Roboto. Add via the `google_fonts` package. Body: `16sp` (sp = scale-independent pixels — equivalent to `rem` on web). Never use `pt` or `px` in Flutter text styles.

| Dart Constant | Size (sp) | Weight | Web Equivalent | Usage |
|---------------|-----------|--------|----------------|-------|
| `AppText.caption` | 11sp | 700 | `--fz--3` | Badge labels, uppercase caps |
| `AppText.bodySmall` | 12sp | 400 | `--fz--2` | Caption, meta info, timestamps |
| `AppText.bodyMedium` | 14sp | 400 | `--fz--1` | Body small, card descriptions |
| `AppText.bodyLarge` | 16sp | 400 | `--fz-0` | Body base, standard content |
| `AppText.titleSmall` | 16sp | 500 | `--fz-0 medium` | List item titles |
| `AppText.titleMedium` | 18sp | 600 | `--fz-1` | Card headings, subtitle |
| `AppText.titleLarge` | 20sp | 700 | `--fz-2` | Page title, section header |
| `AppText.displaySmall` | 24sp | 700 | `--fz-3` | Dashboard stats, level number |
| `AppText.displayLarge` | 32sp | 800 | `--fz-4` | Display numbers (stat cards) |

### 2.5 Spacing Tokens

| Dart Constant | Value | Web Equivalent | Usage |
|---------------|-------|----------------|-------|
| `AppSpacing.xxs` | 4.0 | `--space-3xs` | Tight internal spacing |
| `AppSpacing.xs` | 8.0 | `--space-2xs` | Icon-text gap, small gaps |
| `AppSpacing.sm` | 12.0 | `--space-xs` | Card internal gap |
| `AppSpacing.md` | 16.0 | `--space-s` | Standard padding (page edges) |
| `AppSpacing.lg` | 24.0 | `--space-m` | Section gap, card margin |
| `AppSpacing.xl` | 32.0 | `--space-l` | Page section gap |
| `AppSpacing.xxl` | 48.0 | `--space-xl` | Major section spacing |

---

## Part 3 — Navigation Architecture

### 3.1 Role-Adaptive Shell

The navigation shell adapts to `user.competence_level` from the auth token. GoRouter reads the level from `AuthProvider` and applies redirects. The DRF API enforces all permissions — the Flutter shell only controls what screens are visible.

| Level | Role | Bottom Nav Items | Additional Screens |
|-------|------|-----------------|-------------------|
| 0 | Seeker/Inductee | Home, Bible, Learn, Profile | Induction progress card on Home |
| 1 | Member | Home, Bible, Learn, Activity, Community, Profile | |
| 2 | Disciple | + Governance (read), Certifications tab in Learn | |
| 3 | Steward | + Community management, Cert queue, Induction review | |
| 4 | Senior Steward | + Governance write, Programme oversight | |
| 5 | Architect | Full operator access | |

### 3.2 Bottom Navigation

Maximum 5 items in the bottom nav. For Level 1+ users with more than 5 access points, use a "More" tab that opens a drawer list.

- **Level 0:** 4 items (Home, Bible, Learn, Profile) — fits without overflow
- **Level 1–2:** 5 items (Home, Bible, Learn, Activity/Community, Profile) + More drawer
- **Level 3+:** Same 5-item structure; coordinator screens via the More drawer

Active state: filled icon variant + primary colour label. Inactive: outlined icon + muted colour. This mirrors the web active state (FILL 1 for Material Symbols).

### 3.3 Navigation Patterns

| Pattern | Implementation | Notes |
|---------|---------------|-------|
| Tab-based app navigation | GoRouter with `ShellRoute` + bottom `NavigationBar` | Maintains scroll position per tab |
| Surface switching (My Learning / Catalogue) | `TabBar` + `TabBarView` within a screen | Mirrors web tab row |
| Detail view push | GoRouter push — slides from right (Android default) | |
| Bottom sheet | `showModalBottomSheet()` with 20dp top radius | Mirrors web `.sheet` component |
| Back navigation | AppBar leading back button or Android system back gesture | Always handle both |

---

## Part 4 — Component Library

### 4.1 `IcheboCard`

The primary content container. Mirrors web `.card-base`.

```dart
class IcheboCard extends StatelessWidget {
  final Widget child;
  final VoidCallback? onTap;
  final bool elevated;

  // Material with color: Theme.of(context).colorScheme.surface
  // Border: Border.all(color: AppColors.border)
  // BorderRadius: BorderRadius.circular(12)
  // If onTap != null: wrap in InkWell with splashColor: primary.withOpacity(0.08)
}
```

### 4.2 `IcheboButton`

All buttons use `IcheboButton`. Minimum height: **48dp** (strict touch target — matches web 48px rule).

```dart
enum IcheboButtonVariant { primary, secondary, danger, ghost }

class IcheboButton extends StatelessWidget {
  final String label;
  final VoidCallback? onPressed;  // null = disabled state
  final IcheboButtonVariant variant;
  final Widget? leadingIcon;
  final bool isLoading;
}
```

**Button variants:**

| Variant | Background | Foreground | Notes |
|---------|-----------|------------|-------|
| `primary` | `AppColors.primary` | white | Main action |
| `secondary` | `AppColors.surface` | `AppColors.textPrimary` | With border |
| `danger` | `AppColors.error` | white | Destructive |
| `ghost` | transparent | `AppColors.primary` | No border |

- **Disabled (all variants):** `opacity: 0.5`, `onPressed: null`
- **Loading (all variants):** show `CircularProgressIndicator(strokeWidth: 2)` inside button, disable `onPressed`

### 4.3 `LevelBadge`

```dart
class LevelBadge extends StatelessWidget {
  final int level;
  // Coloured circle: AppColors.levelN where N = level (0-5)
  // Size: 28dp circle, 12sp bold white text inside
}
```

### 4.4 `StatusBadge`

Pill-shaped status indicator. Mirrors web `.status-badge`.

```dart
enum StatusBadgeVariant { active, danger, warning, info, muted }

class StatusBadge extends StatelessWidget {
  final String label;
  final StatusBadgeVariant variant;
  // 10sp text, 700 weight, uppercase, letter spacing 0.05
  // Padding: 2dp vertical, 8dp horizontal
  // BorderRadius: 999
}
```

### 4.5 `IcheboProgressBar`

```dart
class IcheboProgressBar extends StatelessWidget {
  final double progress;  // 0.0 to 1.0
  // height: 8dp
  // background: AppColors.pressed
  // fill: AppColors.primary
  // BorderRadius: 4
  // Animated with AnimatedFractionallySizedBox
}
```

### 4.6 `ListItemTile`

Dense list item. Mirrors web `.list-item`.

```dart
class ListItemTile extends StatelessWidget {
  final Widget? leading;    // 40dp icon container
  final String title;
  final String? subtitle;
  final Widget? trailing;   // chevron or action
  final VoidCallback? onTap;
}
```

### 4.7 `EmptyState`

Required on every list screen that can be empty. Never show a blank screen.

```dart
class EmptyState extends StatelessWidget {
  final IconData icon;
  final String title;
  final String message;
  final Widget? action;   // optional IcheboButton
}
```

### 4.8 `IcheboAppBar`

```dart
class IcheboAppBar extends StatelessWidget implements PreferredSizeWidget {
  final String title;
  final List<Widget>? actions;
  final bool showBack;
  // backgroundColor: Theme.of(context).colorScheme.surface
  // elevation: 0
  // titleTextStyle: AppText.titleMedium
}
```

---

## Part 5 — Screen Patterns

### 5.1 List Screen Pattern

Every list screen (Bible books, programme catalogue, member directory, activity list) follows this structure:

1. `IcheboAppBar` at top
2. Optional `TabBar` below app bar if surface switching is needed
3. Optional search input (if search is supported)
4. `ListView.builder` or `GridView.builder` for content
5. `EmptyState` widget when list is empty
6. `FloatingActionButton` for primary create action (if applicable)
7. Pull-to-refresh with `RefreshIndicator` (triggers delta sync)

### 5.2 Detail Screen Pattern

1. `IcheboAppBar` with back button
2. Scrollable body with `SingleChildScrollView` or `CustomScrollView`
3. Hero section at top (title, meta, status badge)
4. Content sections separated by `AppSpacing.lg` gaps
5. Sticky bottom action bar for the primary action (Enrol, Mark Complete, Confirm, etc.)

### 5.3 Form Screen Pattern

1. `IcheboAppBar` with title and optional Save action in trailing
2. `SingleChildScrollView` to handle keyboard overlap
3. Form fields grouped logically with `label-caps` style labels above each
4. Primary action `IcheboButton` at the bottom (above system nav)
5. Error messages inline below each field (never toast for field errors)
6. Success: pop screen and show snackbar, OR navigate to the created item

### 5.4 Dashboard Screen

1. Greeting header: "Good morning, [first name]" with `LevelBadge`
2. Formation card (if Level 0–2): current level, active programme, progress bar, next requirement
3. Today's focus card: discipline prompt from `ParacleteDigest`
4. Pending activities section: due today and overdue (compact list)
5. Active enrolment card: current programme + progress bar + "Resume Lesson" button
6. Notification bell in `IcheboAppBar` trailing — taps to Notifications screen

---

## Part 6 — Offline & Connectivity

### 6.1 Offline-First Principle

The app must work for reading with no internet connection. This is critical for users in areas with poor connectivity — rural areas, load-shedding, church buildings with poor signal.

### 6.2 What is Cached Locally (sqflite)

| Data | When Cached | Update Strategy |
|------|------------|-----------------|
| Bible verses (all 3 translations) | First launch after login | Static — never changes. Cached permanently. |
| Records (user's tenant scope) | On each sync | Delta sync on app open + pull-to-refresh |
| Activities (user's activities) | On each sync | Delta sync |
| Learn content (programmes, courses, lessons) | When user opens Learn app | Delta sync; lesson text cached for offline reading |
| Notifications (recent 50) | On each sync | Delta sync |
| User profile (`auth/me` response) | On each login | On app open if online |

### 6.3 Write Queue Pattern

When the user performs a write action while offline:

1. Save the action to a `write_queue` table in sqflite
2. Show the result immediately in the UI (optimistic update)
3. When connectivity is restored, `workmanager` background task flushes the write queue
4. If a queued write fails on the server (conflict, validation), show a notification
5. Never block the user from using the app while offline

### 6.4 Connectivity Indicator

Show a subtle offline banner below the app bar when offline. Not a blocking dialog — just an informational strip. Remove automatically when connectivity is restored.

```dart
Container(
  color: AppColors.warning.withOpacity(0.12),
  padding: EdgeInsets.symmetric(horizontal: 16, vertical: 6),
  child: Row(children: [
    Icon(Icons.cloud_off, size: 14, color: AppColors.warning),
    SizedBox(width: 6),
    Text("You're offline — viewing cached content",
         style: AppText.bodySmall.copyWith(color: AppColors.warning)),
  ]),
)
```

---

## Part 7 — API Integration

### 7.1 Dio HTTP Client

Configure once in `api_client.dart`. All screens use the same configured instance via Riverpod.

```dart
class ApiClient {
  static Dio create(String? token) {
    final dio = Dio(BaseOptions(
      baseUrl: AppConfig.apiBaseUrl,
      connectTimeout: Duration(seconds: 10),
      receiveTimeout: Duration(seconds: 30),
    ));

    if (token != null) {
      dio.options.headers['Authorization'] = 'Token $token';
    }

    // Add retry interceptor for network errors
    // Add logging interceptor in debug mode
    return dio;
  }
}
```

### 7.2 Authentication Flow

```
1. User enters email + password
2. POST /api/auth/login/ → {"token": "abc123"}
3. Store token in shared_preferences
4. GET /api/auth/me/ → full user object
5. Store user in AuthProvider (Riverpod)
6. PATCH /api/auth/me/ with {"fcm_token": fcmToken}
7. GoRouter reads user.competence_level → routes to correct shell
```

### 7.3 Error Handling

| HTTP Status | Meaning | Flutter Action |
|------------|---------|----------------|
| 200/201 | Success | Parse response, update state |
| 400 | Validation error | Show field-level error messages inline |
| 401 | Unauthorized | Clear token, redirect to login screen |
| 403 | Forbidden (level gate) | Show "Access requires Level X" message |
| 404 | Not found | Show "Item not found" and pop screen |
| 500 | Server error | Show generic error snackbar; log to console |
| Network error | No connectivity | Use cached data; show offline banner |

---

## Part 8 — Push Notifications (FCM)

### 8.1 Setup

- Create Firebase project at `console.firebase.google.com`
- Add Android app to Firebase project (package name must match `pubspec.yaml`)
- Download `google-services.json` → place in `android/app/` (never commit to public repo)
- Add `firebase_messaging` to `pubspec.yaml`
- Send FCM token to backend on each login: `PATCH /api/auth/me/ {"fcm_token": token}`

### 8.2 Notification Types & Deep Links

| Notification Type | Deep Link Destination |
|------------------|-----------------------|
| `certification_confirmed` | Profile → Formation history |
| `induction_completed` | Home dashboard |
| `task_assigned` | Activity detail screen |
| `announcement` | Community → Announcements |

### 8.3 Notification Handling States

- **App in foreground:** show in-app notification banner (`SnackBar` or custom overlay). Do not show system notification.
- **App in background:** system notification shown by FCM. On tap, app opens and navigates to deep link.
- **App terminated:** system notification shown. On tap, app launches and navigates to deep link.

---

## Part 9 — Video Player

### 9.1 URL-Based Video Only

The app plays videos from URLs only — YouTube, Vimeo, and direct `.mp4` links. No self-hosted video.

```dart
// core/utils/video_utils.dart
class VideoUtils {
  static String? getEmbedUrl(String? url) {
    if (url == null) return null;
    if (url.contains('youtube.com/watch?v=')) {
      final id = Uri.parse(url).queryParameters['v'];
      return 'https://www.youtube.com/embed/$id';
    }
    if (url.contains('youtu.be/')) {
      final id = url.split('youtu.be/').last.split('?').first;
      return 'https://www.youtube.com/embed/$id';
    }
    if (url.contains('vimeo.com/')) {
      final id = url.split('vimeo.com/').last;
      return 'https://player.vimeo.com/video/$id';
    }
    return url;  // direct .mp4 — play natively
  }

  static bool isDirectVideo(String url) =>
    url.endsWith('.mp4') || url.endsWith('.webm');
}
```

### 9.2 Player Packages

- **YouTube URLs:** `youtube_player_flutter` package — renders native YouTube player
- **Direct `.mp4` URLs:** `video_player` + `chewie` packages — chewie provides controls UI
- **Vimeo URLs:** `webview_flutter` (fallback — no native Vimeo Flutter package)

Detect URL type using `VideoUtils.isDirectVideo()` and choose the correct player widget.

---

## Part 10 — Accessibility

### 10.1 Touch Targets

Minimum touch target: **48×48dp**. Flutter's Material widgets (`ElevatedButton`, `ListTile`, `IconButton`) already meet this by default. Custom widgets must add padding or `SizedBox` to reach 48dp.

### 10.2 Semantic Labels

- All images: `Semantics(label: '...')` or `Image(semanticLabel: '...')`
- Icon-only buttons: `Tooltip(message: 'Action description')` + `Semantics(label: '...')`
- Progress bars: `Semantics(value: '${(progress*100).round()}% complete')`
- Level badge: `Semantics(label: 'Formation level $level')`

### 10.3 Text Scaling

Respect system text size settings. Do not clamp `textScaleFactor` below 1.0. Design layouts to handle text at 1.3× scale without truncation or overflow. Test with device Accessibility settings set to "Large" text.

### 10.4 Colour Independence

Never convey information through colour alone. Status badges always include the text label in addition to colour. Error states show an icon + text, not just a red colour.

---

## Part 11 — What Not to Do

| Never Do This | Do This Instead |
|---------------|----------------|
| `Color(0xFFAF3236)` | `AppColors.primary` |
| `TextStyle(fontSize: 16)` | `AppText.bodyLarge` |
| `SizedBox(height: 13)` | `SizedBox(height: AppSpacing.sm)` = 12, or find nearest token |
| `Scaffold(backgroundColor: Colors.white)` | `Scaffold(backgroundColor: Theme.of(context).colorScheme.background)` |
| Show blank screen while loading | Show shimmer placeholder or loading spinner within the card structure |
| Show blank screen when list is empty | Use `EmptyState` widget |
| Block the UI when offline | Show cached data + offline banner; never block reads |
| Interactive elements smaller than 48dp | Add minimum padding to reach 48dp |
| Put API URLs as strings in widget files | Use constants from `core/api/endpoints.dart` |
| Manage state with `setState` for cross-screen data | Use Riverpod providers |
| Navigate without checking level | Use GoRouter guards that check `AuthProvider.level` |
| Ignore network errors silently | Always handle `DioException`; show appropriate error state |
| Add a 5th navigation library or state manager | Use `go_router` (navigation) and `riverpod` (state) — locked decisions |

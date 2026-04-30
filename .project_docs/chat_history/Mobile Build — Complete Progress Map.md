## Mobile Build — Complete Progress Map

### Done

|Layer|What|Status|
|---|---|---|
|Foundation|`AppColors`, `AppTextStyles`, `AppTheme`, `AppRouter`, `main.dart`|Complete|
|Auth|`LoginScreen`, `AuthNotifier`, `AuthRepository`, `AuthModels`, session restore, token storage|Complete|
|Tier 1 widgets|`IcheboAppBar`, `PageHeroHeader` (+ `LabelTag`), `BottomNavShell`|Complete|
|Tier 2 widgets|`IcheboCard`, `LevelBadge` (+ `LevelBadgeFull`), `StatusBadge`, `IcheboButton`|Complete|
|Tier 3 widgets|`ListItemTile` (+ `TileAvatar`, `TileIconBox`), `EmptyState` (+ `EmptyStateInline`), `IcheboProgressBar` (+ `FormationProgressCard`)|Complete|
|Barrel export|`shared/widgets/widgets.dart`|Complete|

---

### What Remains — Feature Screens

All five tab screens are currently empty placeholders. This is the full build queue:

**1. Home / Dashboard** — next Composition of stat cards (`IcheboCard`), formation progress (`FormationProgressCard`), recent activity (`ListItemTile` rows), quick-action buttons. Needs a `/api/home/` or `/api/auth/me/` endpoint to pull user data.

**2. Profile** User avatar, `LevelBadgeFull`, `FormationProgressCard`, account details, logout. High-value because it uses almost every shared widget and confirms the design system reads as a whole.

**3. Community** Member list using `ListItemTile` + `LevelBadge` + `TileAvatar`. Needs `/api/community/members/` endpoint.

**4. Learn** Programme/lesson cards using `IcheboCard`, `StatusBadge` (enrolled/completed), `IcheboProgressBar`. Needs `/api/learn/` endpoints.

**5. Bible** Its own distinct UI — topbar, chapter picker, synchronized scroll. You have a `bible_ui_vision.md` in memory that defines this in detail. Most complex screen — build last.

**6. Video** Live stream viewer + scheduled events list. Backend for this is already built (`video_live` app). Needs connecting to the mobile API.

---

### Also Remaining — Not Yet Started

- **Profile screen** (no feature folder yet — needs creating)
- **Notifications** (backend signals exist, mobile UI not started)
- **API endpoints** for home stats, community, learn, video — some may exist on the backend already, some may need adding

---

### Recommended Order from Here

```
Home/Dashboard → Profile → Community → Learn → Video → Bible
```

Home first because it's the landing screen every user sees. Profile second because it validates the full design system end-to-end. The rest follow by complexity.

Ready to build the Home/Dashboard screen?
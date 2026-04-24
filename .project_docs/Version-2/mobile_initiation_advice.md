# Strategic Advice: ICS Mobile App Initiation (Flutter)

Based on the review of `VERSION_2_PLANNING.md` and the `Production Infrastructure Plan`, here is the strategic recommendation for the mobile app phase.

## 1. Should Building Begin Now?
**Yes, with prerequisites.**

The core "Record" architecture and the `competence_level` permission system are stable (MVP complete). The Flutter app's "Role-Adaptive UI" strategy is a perfect fit for this architecture. However, to ensure a smooth developer experience and a robust offline-first app, you should prioritize **Phase 8 (Record Linking)** and **Phase 11 (Delta Sync API)** of the Production Plan immediately.

### Immediate Backend Prerequisites (Tasks for Week 1):
- [ ] **Fix Loose Coupling**: Add the `linked_record` FK to the `Activity` model. Mobile apps struggle with loose metadata strings; typed FKs make local SQLite relationships easier to manage.
- [ ] **Implement Delta Sync API**: Build the `GET /api/sync/changes/` endpoint. Offline capability is a non-negotiable for mobile; this endpoint is the foundation for the `sqflite` sync logic.
- [ ] **Expose Related Records**: Implement the aggregated `related` action on `RecordViewSet`. This reduces the number of network calls the mobile app needs to make when rendering a detail page.

## 2. Should it be in this Repo?
**Recommendation: Yes (Monorepo Approach).**

I recommend creating a `/mobile` directory in the project root. This "Digital Twin" project benefits significantly from a monorepo for the following reasons:

### Strategic Benefits:
1. **Synchronized Logic**: Since the mobile app handles Levels 0-5 and all operator workflows, it is essentially a second "head" for the same body. Keeping them together ensures that changes to `required_level` or `record_type` logic are reflected in both places simultaneously.
2. **Atomic Commits**: You can update a Django model/serializer and the corresponding Dart model/API client in a single git commit. This prevents "version mismatch" bugs during development.
3. **Shared Source of Truth**: Your `.project_docs` and `.env.example` already encompass the full ecosystem. A monorepo keeps this context unified.
4. **DevOps Integration**: As you move toward Docker Compose for the VPS (Phase 5), having the mobile assets in the same repo allows for easier CI/CD integration and potentially using the same repo for PWA asset generation.

## 3. Recommended Structure
```text
/home/mantis/projects/ics/
├── accounts/ (Django app)
├── mobile/ (Flutter/Dart project)
│   ├── lib/
│   ├── pubspec.yaml
│   └── ...
├── ics_project/ (Settings/Config)
├── .project_docs/
└── ...
```

## 4. Immediate Next Steps
1.  **Initialize Flutter**: Run `flutter create mobile` in the project root.
2.  **Implementation Alignment**: While starting the Flutter UI, simultaneously implement the **Delta Sync API** and **Activity FKs** on the backend.
3.  **Environment Sync**: Update `.env.example` to include any mobile-specific variables (e.g., `BASE_API_URL`, `FCM_SERVER_KEY`).

# Production Readiness Review: Bwanji Digital Ecosystem

This document outlines the current state of the project and the steps required to transition from the current "structural scaffold" to a production-ready deployment.

## 1. Environment Variables Audit

### 🟢 Status: Partially Met (Action Required)

While the `.env.example` templates exist, several critical gaps must be filled before production deployment.

| App / Package | Missing / Placeholder Vars | Required Action |
| :--- | :--- | :--- |
| **Main Site** | `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY`, `STRIPE_SECRET_KEY`, `ANTHROPIC_API_KEY` | Replace `pk_test_...` with real live keys (or at least valid test keys). |
| **Main Site** | `NEXT_PUBLIC_BLUEPRINT_URL` | **MISSING.** Add the URL for the Blueprint portal so links work. |
| **Client Portal** | `NEXT_PUBLIC_BLUEPRINT_URL` | **MISSING.** Required for sidebar navigation. |
| **Blueprint** | `.env.local` | **MISSING.** This app currently lacks its own environment file. It needs Stripe keys and Webhook secrets. |
| **Tools Portal** | `.env.local` | **MISSING.** Lacks its own environment file. |

### ⚠️ Security Warning
Current `.env.local` files in `apps/main-site` and `apps/client-portal` contain placeholder Stripe keys and secrets. **Never deploy with these values.**

---

## 2. Infrastructure & Database

### 🟢 Status: Scaffolded (Content Needed)

*   **Database Schema**: The Prisma schema is robust and covers Users, Organizations, Projects, Invoices, and the Learning Portal.
*   **Database Content**: The database is currently empty (as noted in `docs/to-d-stuff.md`). 
    *   **Recommendation**: Implement a `seed.ts` script to populate the `Course`, `CourseModule`, and `ContentCategory` tables to ensure the UI isn't just displaying "Coming Soon."
*   **Connection Pooling**: `DATABASE_URL` uses Supabase PGBouncer (port 6543), which is correct for serverless environments (Next.js).

---

## 3. Feature Completion — "The Payment Loop"

### 🔴 Status: Blocked (Testing Required)

The Stripe webhook logic is implemented in `apps/blueprint/src/app/api/webhooks/stripe/route.ts`, but it has not been verified.

*   **Webhook Secrets**: The Blueprint app needs a unique `BLUEPRINT_STRIPE_WEBHOOK_SECRET` from the Stripe Dashboard to prevent it from ignoring valid signals.
*   **CLI Testing**: You must run the `stripe listen` command to verify that successful payments correctly update the `BlueprintSubscription` model.

---

## 4. Production Hardening Checklist

| Task | Status | Priority |
| :--- | :--- | :--- |
| **Env Validation** | Missing | High |
| **Error Handling** | Basic | Medium |
| **SEO Optimization** | Pending | Medium |
| **Build Optimization** | Pending | Low |

### Recommendations for "Hardening":
1.  **Environment Validation**: Use a library like `t3-env` or a custom Zod schema to ensure the app **crashes on startup** if an environment variable is missing, rather than failing silently at runtime.
2.  **Stripe Live Mode**: Ensure you have a process for switching from `pk_test` to `pk_live` and updating the Webhook secrets in your production environment (Vercel, Railway, etc.).
3.  **Deployment Config**: Currently, no `vercel.json` or `Dockerfile` exists. If you are deploying to Vercel, you will need to configure the **Root Directory** for each app within the monorepo.

---

## Next Steps
1.  **Sync App URLs**: Update all `.env.local` files to include `NEXT_PUBLIC_BLUEPRINT_URL`.
2.  **Verify Stripe**: Use the Stripe CLI to trigger a test payment and confirm the database updates.
3.  **Populate Content**: Run a seed script so the production environment has a base level of "stock."

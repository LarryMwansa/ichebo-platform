# After MVP

  As for what's next — you mentioned a few things need settling.
  Here are the common post-MVP priorities given your codebase:

  1. User onboarding flow — How do new users register and
  progress from level 0 (Seeker) to level 1+? Is there a
  formation pipeline they go through, or do admins manually
  promote them?
  2. Formation/certification flow — Your learn/ app has a
  confirm_certification() view that writes competence_level. Is
  that pipeline working end-to-end?
  3. Tenant setup — Users need a UserPermission linking them to a
   tenant for community/governance features to work properly.
  Have you set that up for your account?
  4. App drawer gating — Currently the _app_drawer.html shows all
   apps regardless of level. Do you want to hide apps the user
  can't access yet?
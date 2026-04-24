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


  ---

  UI Refactor: ICS Platform Shell (Base Shell)

As is i@contextScopeItemMention 

<div class="nav-right-item">
      
      <button id="profileBtn" class="profile-avatar-btn" aria-label="Profile menu" aria-expanded="false">
        
          <div class="avatar-placeholder">A</div>
        
      </button>

      <div id="profileMenu" class="profile-menu" role="menu">
        <div class="profile-header">
          <div class="profile-avatar-large">
            A
          </div>
          <div class="profile-identity">
            <strong>Architect</strong>
            <small>architect@ics.test</small>
          </div>
        </div>
        <div class="profile-menu-items">
          <a href="/" role="menuitem">
            <span class="material-symbols-outlined">dashboard</span> My Dashboard
          </a>
          <a href="/accounts/profile/" role="menuitem">
            <span class="material-symbols-outlined">person</span> My Profile
          </a>
          <a href="/accounts/settings/" role="menuitem">
            <span class="material-symbols-outlined">settings</span> Settings
          </a>
          <form method="post" action="/accounts/logout/" class="logout-form">
            <input type="hidden" name="csrfmiddlewaretoken" value="F4PQgfzA5EdoJsAlj0psn6CeIWINSIyHMRDyni9HxNoCkSc88wrEVO2bVMe4sFbP">
            <button type="submit" role="menuitem" class="logout-btn">
              <span class="material-symbols-outlined">logout</span> Logout
            </button>
          </form>
        </div>
      </div>
      
    </div>
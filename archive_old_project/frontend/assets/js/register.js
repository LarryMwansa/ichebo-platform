// /assets/js/register.js

// FIX: Wrapped in DOMContentLoaded to guarantee the DOM is ready before
// querying elements, regardless of where this script tag is placed.
document.addEventListener("DOMContentLoaded", function () {
  const registerForm = document.getElementById("registerForm");

  if (registerForm) {
    registerForm.addEventListener("submit", function (e) {
      e.preventDefault();

      const name = document.getElementById("name").value;
      const email = document.getElementById("email").value;
      const password = document.getElementById("password").value;

      const result = ICSAuth.registerUser({ name, email, password });

      if (!result.success) {
        alert(result.message);
        return;
      }

      alert("Account created successfully!");

      // FIX: registerUser() auto-logs the user in (sets session).
      // Redirecting to login.html caused the router guard to immediately
      // bounce an authenticated user to dashboard anyway — confusing UX.
      // Go directly to dashboard instead.
      ICSRouter.Navigation.go("dashboard.html");
    });
  }
});

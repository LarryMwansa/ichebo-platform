// /assets/js/login.js

// FIX: Wrapped in DOMContentLoaded to guarantee the DOM is ready before
// querying elements, regardless of where this script tag is placed.
document.addEventListener("DOMContentLoaded", function () {
  const loginForm = document.getElementById("loginForm");

  if (loginForm) {
    loginForm.addEventListener("submit", function (e) {
      e.preventDefault();

      const email = document.getElementById("email").value;
      const password = document.getElementById("password").value;

      const result = ICSAuth.loginUser({ email, password });

      if (!result.success) {
        alert(result.message);
        return;
      }

      // Redirect to dashboard after successful login
      ICSRouter.Navigation.go("dashboard.html");
    });
  }
});

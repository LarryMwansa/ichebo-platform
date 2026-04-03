// /assets/js/auth.js

// NOTE: This file uses the global ICSStorage object from /utils/storage.js

// =========================
// LOGIN
// =========================
function loginUser(credentials) {
  const { email, password } = credentials;
  // MOCK validation (later replaced by API)
  if (email && password) {
    // In a real app, you'd fetch the user from an API.
    // Here, we'll just mock a found user.
    const user = {
      id: "user_mock_123", // Mock user needs a stable ID for session consistency
      name: "John Doe",
      email: email,
    };

    ICSStorage.Session.set(user);
    return { success: true };
  } else {
    return { success: false, message: "Invalid email or password." };
  }
}

// =========================
// REGISTER
// =========================
function registerUser(details) {
  const { name, email, password } = details;
  if (name && email && password) {
    // In a real app, you'd POST this to an API.
    // Here, we create a new user and add them to our mock storage.
    const user = {
      id: ICSStorage.AppStorage.generateId(), // Generate a new ID for the user
      name,
      email,
      // IMPORTANT: Never store passwords in localStorage in a real application.
    };

    // We can add the user to the 'users' app storage for mock persistence
    ICSStorage.AppStorage.add("users", user);

    // For this flow, we'll automatically log them in.
    ICSStorage.Session.set(user);
    return { success: true };
  } else {
    return { success: false, message: "Please fill all fields." };
  }
}

// =========================
// LOGOUT
// =========================
function logoutUser() {
  // This is also handled by ICSRouter.Navigation.logout() which is preferred
  ICSStorage.Session.clear();
  window.location.href = "/pages/login.html";
}

// =========================
// LOAD USER INTO UI
// =========================
function loadUserUI() {
  const user = ICSStorage.Session.user();

  if (!user) return;

  const nameEl = document.getElementById("username");
  const emailEl = document.getElementById("useremail");

  if (nameEl) nameEl.textContent = user.name;
  if (emailEl) emailEl.textContent = user.email;
}

// =========================
// EXPORT (GLOBAL ACCESS)
// =========================
// This makes the auth functions available to other scripts like login.js and register.js
window.ICSAuth = {
  loginUser,
  registerUser,
  logoutUser,
  loadUserUI,
};
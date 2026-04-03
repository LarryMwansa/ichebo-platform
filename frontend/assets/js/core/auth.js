// /assets/js/core/auth.js
// Calls DRF endpoints for authentication

// =========================
// LOGIN
// =========================
async function loginUser(credentials) {
  const { email, password } = credentials;
  
  if (!email || !password) {
    return { success: false, message: "Invalid email or password." };
  }

  try {
    const res = await fetch('/api/auth/login/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });

    if (!res.ok) {
      const data = await res.json();
      return { success: false, message: data.non_field_errors?.[0] || 'Login failed' };
    }

    const data = await res.json();
    localStorage.setItem('ics_token', data.token);
    localStorage.setItem('ics_user', JSON.stringify(data.user));
    return { success: true, user: data.user };
  } catch (error) {
    console.error('Login error:', error);
    return { success: false, message: 'Network error occurred. Please try again.' };
  }
}

// =========================
// REGISTER
// =========================
async function registerUser(details) {
  const { display_name, email, password } = details;
  
  if (!display_name || !email || !password) {
    return { success: false, message: "Please fill all fields." };
  }

  try {
    const res = await fetch('/api/auth/register/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ display_name, email, password })
    });

    if (!res.ok) {
      const data = await res.json();
      const errors = Object.values(data).flat();
      return { success: false, message: errors[0] || 'Registration failed' };
    }

    const data = await res.json();
    localStorage.setItem('ics_token', data.token);
    localStorage.setItem('ics_user', JSON.stringify(data.user));
    return { success: true, user: data.user };
  } catch (error) {
    console.error('Register error:', error);
    return { success: false, message: 'Network error occurred. Please try again.' };
  }
}

// =========================
// LOGOUT
// =========================
async function logoutUser() {
  try {
    const token = localStorage.getItem('ics_token');
    if (token) {
      await fetch('/api/auth/logout/', {
        method: 'POST',
        headers: { 'Authorization': `Token ${token}` }
      });
    }
  } catch (error) {
    console.error('Logout error:', error);
  } finally {
    localStorage.removeItem('ics_token');
    localStorage.removeItem('ics_user');
    window.location.href = '/pages/login.html';
  }
}

// =========================
// GET CURRENT USER
// =========================
function getCurrentUser() {
  const userJson = localStorage.getItem('ics_user');
  return userJson ? JSON.parse(userJson) : null;
}

// =========================
// LOAD USER INTO UI
// =========================
function loadUserUI() {
  const user = getCurrentUser();

  if (!user) return;

  const nameEl = document.getElementById('username');
  const emailEl = document.getElementById('useremail');

  if (nameEl) nameEl.textContent = user.display_name || user.email;
  if (emailEl) emailEl.textContent = user.email;
}

// =========================
// EXPORT (GLOBAL ACCESS)
// =========================
window.ICSAuth = {
  loginUser,
  registerUser,
  logoutUser,
  getCurrentUser,
  loadUserUI,
};
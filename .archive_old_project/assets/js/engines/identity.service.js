const ICSIdentity = (() => {
  function authHeaders() {
    const token = localStorage.getItem('ics_token')
    return { 'Authorization': `Token ${token}`, 'Content-Type': 'application/json' }
  }

  async function getCurrentUser() {
    if (!localStorage.getItem('ics_token')) return null

    const res = await fetch('/api/auth/me/', { headers: authHeaders() })
    if (!res.ok) return null
    return res.json()
  }

  async function getPermissions() {
    if (!localStorage.getItem('ics_token')) return []

    const preferred = await fetch('/api/auth/me/permissions/', { headers: authHeaders() })
    if (preferred.ok) {
      const data = await preferred.json()
      return Array.isArray(data) ? data : (data?.results ?? [])
    }

    if (preferred.status === 404) {
      const fallback = await fetch('/api/permissions/', { headers: authHeaders() })
      if (!fallback.ok) return []
      const data = await fallback.json()
      return Array.isArray(data) ? data : (data?.results ?? [])
    }

    return []
  }

  function isAuthenticated() {
    return !!localStorage.getItem('ics_token')
  }

  function getToken() {
    return localStorage.getItem('ics_token')
  }

  return { getCurrentUser, getPermissions, isAuthenticated, getToken }
})()

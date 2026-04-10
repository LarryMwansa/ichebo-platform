const ICSTenant = (() => {
  const BASE = '/api/tenants/'

  function authHeaders() {
    const token = localStorage.getItem('ics_token')
    return {
      'Content-Type': 'application/json',
      'Authorization': `Token ${token}`
    }
  }

  function normalizePath(path) {
    if (!path) return '/'
    let next = String(path).trim()
    if (!next.startsWith('/')) next = `/${next}`
    if (!next.endsWith('/')) next = `${next}/`
    next = next.replace(/\/{2,}/g, '/')
    return next
  }

  function buildChildPath(parentPath, childSlug) {
    const parent = normalizePath(parentPath)
    const slug = String(childSlug || '').trim().replace(/^\/+|\/+$/g, '')
    if (!slug) return parent
    return normalizePath(`${parent}${slug}`)
  }

  async function list(filters = {}) {
    const params = new URLSearchParams(filters)
    const url = params.toString() ? `${BASE}?${params}` : BASE
    const res = await fetch(url, { headers: authHeaders() })
    if (!res.ok) throw new Error(`Tenant list failed: ${res.status}`)
    return res.json()
  }

  async function get(id) {
    const res = await fetch(`${BASE}${id}/`, { headers: authHeaders() })
    if (!res.ok) throw new Error(`Tenant get failed: ${res.status}`)
    return res.json()
  }

  async function create(data) {
    const res = await fetch(BASE, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify(data)
    })
    if (!res.ok) throw new Error(`Tenant create failed: ${res.status}`)
    return res.json()
  }

  async function update(id, data) {
    const res = await fetch(`${BASE}${id}/`, {
      method: 'PATCH',
      headers: authHeaders(),
      body: JSON.stringify(data)
    })
    if (!res.ok) throw new Error(`Tenant update failed: ${res.status}`)
    return res.json()
  }

  async function remove(id) {
    const res = await fetch(`${BASE}${id}/`, {
      method: 'DELETE',
      headers: authHeaders()
    })
    if (!res.ok) throw new Error(`Tenant delete failed: ${res.status}`)
    return true
  }

  async function getMyPermissions() {
    if (window.ICSIdentity?.getPermissions) return window.ICSIdentity.getPermissions()

    const res = await fetch('/api/permissions/', { headers: authHeaders() })
    if (!res.ok) return []
    const data = await res.json()
    return Array.isArray(data) ? data : (data?.results ?? [])
  }

  async function getMyTenants() {
    const permissions = await getMyPermissions()
    const tenantIds = [...new Set(permissions.map((p) => p.tenant).filter(Boolean))]
    const tenants = await Promise.all(tenantIds.map((id) => get(id)))
    return tenants
  }

  return {
    list,
    get,
    create,
    update,
    remove,
    getMyPermissions,
    getMyTenants,
    normalizePath,
    buildChildPath
  }
})()

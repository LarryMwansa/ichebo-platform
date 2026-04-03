// activity.service.js — IIFE module, calls DRF endpoints for Activity objects
const ICSActivity = (() => {
  const BASE = '/api/activities/'

  function authHeaders() {
    const token = localStorage.getItem('ics_token')
    return {
      'Content-Type': 'application/json',
      'Authorization': `Token ${token}`
    }
  }

  async function list(filters = {}) {
    const params = new URLSearchParams(filters)
    const res = await fetch(`${BASE}?${params}`, { headers: authHeaders() })
    if (!res.ok) throw new Error(`Activity list failed: ${res.status}`)
    return res.json()
  }

  async function get(id) {
    const res = await fetch(`${BASE}${id}/`, { headers: authHeaders() })
    if (!res.ok) throw new Error(`Activity get failed: ${res.status}`)
    return res.json()
  }

  async function create(data) {
    const res = await fetch(BASE, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify(data)
    })
    if (!res.ok) throw new Error(`Activity create failed: ${res.status}`)
    return res.json()
  }

  async function update(id, data) {
    const res = await fetch(`${BASE}${id}/`, {
      method: 'PATCH',
      headers: authHeaders(),
      body: JSON.stringify(data)
    })
    if (!res.ok) throw new Error(`Activity update failed: ${res.status}`)
    return res.json()
  }

  async function remove(id) {
    const res = await fetch(`${BASE}${id}/`, {
      method: 'DELETE',
      headers: authHeaders()
    })
    if (!res.ok) throw new Error(`Activity delete failed: ${res.status}`)
    return true
  }

  async function getLogs(id) {
    const res = await fetch(`${BASE}${id}/log/`, { headers: authHeaders() })
    if (!res.ok) throw new Error(`Activity logs fetch failed: ${res.status}`)
    return res.json()
  }

  return { list, get, create, update, remove, getLogs }
})()

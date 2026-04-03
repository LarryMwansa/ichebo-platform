// records.service.js — IIFE module, calls DRF endpoints
const ICSRecords = (() => {
  const BASE = '/api/records/'

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
    if (!res.ok) throw new Error(`Records list failed: ${res.status}`)
    return res.json()
  }

  async function get(id) {
    const res = await fetch(`${BASE}${id}/`, { headers: authHeaders() })
    if (!res.ok) throw new Error(`Record get failed: ${res.status}`)
    return res.json()
  }

  async function create(data) {
    const res = await fetch(BASE, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify(data)
    })
    if (!res.ok) throw new Error(`Record create failed: ${res.status}`)
    return res.json()
  }

  async function update(id, data) {
    const res = await fetch(`${BASE}${id}/`, {
      method: 'PATCH',
      headers: authHeaders(),
      body: JSON.stringify(data)
    })
    if (!res.ok) throw new Error(`Record update failed: ${res.status}`)
    return res.json()
  }

  async function remove(id) {
    const res = await fetch(`${BASE}${id}/`, {
      method: 'DELETE',
      headers: authHeaders()
    })
    if (!res.ok) throw new Error(`Record delete failed: ${res.status}`)
    return true
  }

  return { list, get, create, update, remove }
})()

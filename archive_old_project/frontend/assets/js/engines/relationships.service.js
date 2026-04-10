// relationships.service.js — IIFE module for relationship CRUD
const ICSRelationships = (() => {
  const BASE = '/api/relationships/'

  function authHeaders() {
    const token = localStorage.getItem('ics_token')
    return {
      'Content-Type': 'application/json',
      'Authorization': `Token ${token}`
    }
  }

  async function create(data) {
    const res = await fetch(BASE, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify(data)
    })
    if (!res.ok) throw new Error(`Relationship create failed: ${res.status}`)
    return res.json()
  }

  async function remove(id) {
    const res = await fetch(`${BASE}${id}/`, {
      method: 'DELETE',
      headers: authHeaders()
    })
    if (!res.ok) throw new Error(`Relationship delete failed: ${res.status}`)
    return true
  }

  async function getForRecord(recordId) {
    const res = await fetch(`/api/records/${recordId}/relationships/`, {
      headers: authHeaders()
    })
    if (!res.ok) throw new Error(`Get relationships failed: ${res.status}`)
    return res.json()
  }

  return { create, remove, getForRecord }
})()

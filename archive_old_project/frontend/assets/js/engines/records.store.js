// records.store.js — State management for records (cached in memory, synced with service)
const ICSRecordsStore = (() => {
  let records = []
  let currentRecord = null
  let filters = {}
  let currentPage = 1
  let pageSize = 20
  let totalCount = 0

  async function fetchList(newFilters = {}) {
    try {
      filters = newFilters
      currentPage = 1
      const params = {
        ...filters,
        page: currentPage
      }
      const response = await ICSRecords.list(params)
      records = response.results || []
      totalCount = response.count || 0
      return { records, count: totalCount, page: currentPage }
    } catch (error) {
      console.error('Failed to fetch records:', error)
      throw error
    }
  }

  async function fetchNext() {
    try {
      currentPage += 1
      const params = {
        ...filters,
        page: currentPage
      }
      const response = await ICSRecords.list(params)
      if (response.results) {
        records = [...records, ...response.results]
      }
      return { records, count: response.count || totalCount, page: currentPage }
    } catch (error) {
      console.error('Failed to fetch next page:', error)
      throw error
    }
  }

  async function getRecord(id) {
    try {
      currentRecord = await ICSRecords.get(id)
      return currentRecord
    } catch (error) {
      console.error('Failed to get record:', error)
      throw error
    }
  }

  async function createRecord(data) {
    try {
      const newRecord = await ICSRecords.create(data)
      records.push(newRecord)
      totalCount += 1
      return newRecord
    } catch (error) {
      console.error('Failed to create record:', error)
      throw error
    }
  }

  async function updateRecord(id, data) {
    try {
      const updated = await ICSRecords.update(id, data)
      const index = records.findIndex(r => r.id === id)
      if (index !== -1) {
        records[index] = updated
      }
      if (currentRecord && currentRecord.id === id) {
        currentRecord = updated
      }
      return updated
    } catch (error) {
      console.error('Failed to update record:', error)
      throw error
    }
  }

  async function deleteRecord(id) {
    try {
      await ICSRecords.remove(id)
      records = records.filter(r => r.id !== id)
      totalCount = Math.max(0, totalCount - 1)
      if (currentRecord && currentRecord.id === id) {
        currentRecord = null
      }
      return true
    } catch (error) {
      console.error('Failed to delete record:', error)
      throw error
    }
  }

  function getAll() {
    return [...records]
  }

  function getCurrent() {
    return currentRecord
  }

  function getState() {
    return {
      records: [...records],
      currentRecord,
      filters,
      currentPage,
      pageSize,
      totalCount
    }
  }

  function clearCurrent() {
    currentRecord = null
  }

  return {
    fetchList,
    fetchNext,
    getRecord,
    createRecord,
    updateRecord,
    deleteRecord,
    getAll,
    getCurrent,
    getState,
    clearCurrent
  }
})()

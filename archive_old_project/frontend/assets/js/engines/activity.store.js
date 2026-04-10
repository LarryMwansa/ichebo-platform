// activity.store.js — State management for activities (cached in memory, synced with service)
const ICSActivityStore = (() => {
  let activities = []
  let currentActivity = null
  let filters = {}
  let currentPage = 1
  let pageSize = 20
  let totalCount = 0
  let activityLogs = []

  async function fetchList(newFilters = {}) {
    try {
      filters = newFilters
      currentPage = 1
      const params = {
        ...filters,
        page: currentPage
      }
      const response = await ICSActivity.list(params)
      activities = response.results || []
      totalCount = response.count || 0
      return { activities, count: totalCount, page: currentPage }
    } catch (error) {
      console.error('Failed to fetch activities:', error)
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
      const response = await ICSActivity.list(params)
      if (response.results) {
        activities = [...activities, ...response.results]
      }
      totalCount = response.count || totalCount
      return { activities, count: totalCount, page: currentPage }
    } catch (error) {
      console.error('Failed to fetch next activity page:', error)
      throw error
    }
  }

  async function getActivity(id) {
    try {
      currentActivity = await ICSActivity.get(id)
      return currentActivity
    } catch (error) {
      console.error('Failed to get activity:', error)
      throw error
    }
  }

  async function createActivity(data) {
    try {
      const newActivity = await ICSActivity.create(data)
      activities.push(newActivity)
      totalCount += 1
      return newActivity
    } catch (error) {
      console.error('Failed to create activity:', error)
      throw error
    }
  }

  async function updateActivity(id, data) {
    try {
      const updated = await ICSActivity.update(id, data)
      const index = activities.findIndex(a => a.id === id)
      if (index !== -1) {
        activities[index] = updated
      }
      if (currentActivity && currentActivity.id === id) {
        currentActivity = updated
      }
      return updated
    } catch (error) {
      console.error('Failed to update activity:', error)
      throw error
    }
  }

  async function deleteActivity(id) {
    try {
      await ICSActivity.remove(id)
      activities = activities.filter(a => a.id !== id)
      totalCount = Math.max(0, totalCount - 1)
      if (currentActivity && currentActivity.id === id) {
        currentActivity = null
      }
      return true
    } catch (error) {
      console.error('Failed to delete activity:', error)
      throw error
    }
  }

  async function fetchLogs(activityId) {
    try {
      const response = await ICSActivity.getLogs(activityId)
      activityLogs = response.results || []
      return activityLogs
    } catch (error) {
      console.error('Failed to fetch activity logs:', error)
      throw error
    }
  }

  function getAll() {
    return [...activities]
  }

  function getCurrent() {
    return currentActivity
  }

  function getLogs() {
    return [...activityLogs]
  }

  function getState() {
    return {
      activities: [...activities],
      currentActivity,
      filters,
      currentPage,
      pageSize,
      totalCount,
      activityLogs: [...activityLogs]
    }
  }

  function clearCurrent() {
    currentActivity = null
    activityLogs = []
  }

  return {
    fetchList,
    fetchNext,
    getActivity,
    createActivity,
    updateActivity,
    deleteActivity,
    fetchLogs,
    getAll,
    getCurrent,
    getLogs,
    getState,
    clearCurrent
  }
})()

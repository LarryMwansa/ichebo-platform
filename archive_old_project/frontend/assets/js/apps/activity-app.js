// /assets/js/apps/activity-app.js
// Activity UI page logic — renders activity list, filters, create form, and history view.

const ICSActivityApp = (() => {
  const state = {
    activities: [],
    logs: [],
    selectedActivity: null,
  }

  function query(selector) {
    return document.querySelector(selector)
  }

  function formatDate(value) {
    return value ? new Date(value).toLocaleString() : '—'
  }

  function safeText(value) {
    return String(value || '')
  }

  function showMessage(message, type = 'info') {
    const container = query('#activityMessage')
    if (!container) return
    container.textContent = message
    container.className = `message message-${type}`
    setTimeout(() => {
      container.textContent = ''
      container.className = 'message'
    }, 5000)
  }

  async function refreshActivities() {
    const activityType = query('#filterType')?.value || ''
    const status = query('#filterStatus')?.value || ''

    try {
      const response = await ICSActivityStore.fetchList({ activity_type: activityType, status })
      state.activities = response.activities || response.results || []
      renderActivityList()
    } catch (error) {
      console.error('Failed to refresh activities:', error)
      showMessage('Unable to load activities.', 'error')
    }
  }

  function renderActivityList() {
    const list = query('#activityList')
    const empty = query('#activityEmptyState')
    const count = query('#activityCount')

    if (!list || !empty || !count) return

    list.innerHTML = ''
    count.textContent = state.activities.length

    if (state.activities.length === 0) {
      empty.style.display = 'block'
      return
    }

    empty.style.display = 'none'

    state.activities.forEach(activity => {
      const card = document.createElement('article')
      card.className = 'activity-card'
      card.innerHTML = `
        <div class="activity-card-header">
          <div>
            <h3>${safeText(activity.title)}</h3>
            <div class="meta">${safeText(activity.activity_type)} • ${safeText(activity.status)}</div>
          </div>
          <div class="activity-card-actions">
            <button type="button" class="secondary" data-action="view" data-id="${activity.id}">View</button>
            <button type="button" class="secondary" data-action="complete" data-id="${activity.id}">Complete</button>
            <button type="button" class="danger" data-action="delete" data-id="${activity.id}">Delete</button>
          </div>
        </div>
        <p>${safeText(activity.description)}</p>
        <div class="activity-meta-row">
          <span>Due: ${formatDate(activity.due_at)}</span>
          <span>Scheduled: ${formatDate(activity.scheduled_at)}</span>
          <span>Progress: ${activity.progress ?? 0}%</span>
        </div>
      `

      card.addEventListener('click', (event) => {
        const action = event.target.dataset.action
        const id = event.target.dataset.id
        if (!action || !id) return

        if (action === 'delete') {
          deleteActivity(id)
        } else if (action === 'complete') {
          completeActivity(id)
        } else if (action === 'view') {
          loadActivityLogs(id)
        }
      })

      list.appendChild(card)
    })
  }

  function renderLogs() {
    const logList = query('#activityLogs')
    const logEmpty = query('#activityLogsEmpty')
    const selectedTitle = query('#selectedActivityTitle')

    if (!logList || !logEmpty || !selectedTitle) return

    logList.innerHTML = ''
    selectedTitle.textContent = state.selectedActivity ? state.selectedActivity.title : 'Select an activity to view history'

    if (!state.logs.length) {
      logEmpty.style.display = 'block'
      return
    }

    logEmpty.style.display = 'none'

    state.logs.forEach(log => {
      const entry = document.createElement('section')
      entry.className = 'activity-log-entry'
      entry.innerHTML = `
        <div class="log-header">
          <strong>${safeText(log.event_type)}</strong>
          <span>${formatDate(log.created_at)}</span>
        </div>
        <div class="log-note">${safeText(log.note)}</div>
        <div class="log-meta">from: ${safeText(log.previous_value)} → to: ${safeText(log.new_value)}</div>
      `
      logList.appendChild(entry)
    })
  }

  async function createActivity(event) {
    event.preventDefault()

    const title = query('#activityTitle')?.value.trim() || ''
    const description = query('#activityDescription')?.value.trim() || ''
    const activityType = query('#activityType')?.value || 'task'
    const status = query('#activityStatus')?.value || 'active'
    const scheduledAt = query('#activityScheduledAt')?.value || null
    const dueAt = query('#activityDueAt')?.value || null
    const kgsPillar = query('#activityPillar')?.value || ''
    const kgsPathway = query('#activityPathway')?.value || ''

    if (!title) {
      showMessage('Title is required.', 'error')
      return
    }

    const payload = {
      title,
      description,
      activity_type: activityType,
      status,
      scheduled_at: scheduledAt || null,
      due_at: dueAt || null,
      kgs_pillar: kgsPillar,
      kgs_pathway: kgsPathway,
      progress: 0,
    }

    try {
      await ICSActivityStore.createActivity(payload)
      query('#activityForm')?.reset()
      await refreshActivities()
      showMessage('Activity created successfully.', 'success')
    } catch (error) {
      console.error('Failed to create activity:', error)
      showMessage('Unable to create activity.', 'error')
    }
  }

  async function deleteActivity(id) {
    if (!window.confirm('Delete this activity?')) return

    try {
      await ICSActivityStore.deleteActivity(id)
      await refreshActivities()
      if (state.selectedActivity?.id === id) {
        state.selectedActivity = null
        state.logs = []
        renderLogs()
      }
      showMessage('Activity deleted.', 'success')
    } catch (error) {
      console.error('Failed to delete activity:', error)
      showMessage('Unable to delete activity.', 'error')
    }
  }

  async function completeActivity(id) {
    try {
      await ICSActivityStore.updateActivity(id, { status: 'completed', progress: 100 })
      await refreshActivities()
      showMessage('Activity marked complete.', 'success')
    } catch (error) {
      console.error('Failed to complete activity:', error)
      showMessage('Unable to complete activity.', 'error')
    }
  }

  async function loadActivityLogs(id) {
    try {
      const activity = state.activities.find(item => item.id === id)
      state.selectedActivity = activity || null
      state.logs = await ICSActivityStore.fetchLogs(id)
      renderLogs()
    } catch (error) {
      console.error('Failed to load activity logs:', error)
      showMessage('Unable to load activity history.', 'error')
    }
  }

  function bindEvents() {
    query('#activityForm')?.addEventListener('submit', createActivity)
    query('#filterType')?.addEventListener('change', refreshActivities)
    query('#filterStatus')?.addEventListener('change', refreshActivities)
    query('#refreshActivities')?.addEventListener('click', refreshActivities)
  }

  function init() {
    bindEvents()
    refreshActivities()
  }

  return {
    init,
  }
})()

window.ICSActivityApp = ICSActivityApp

document.addEventListener('DOMContentLoaded', () => {
  ICSActivityApp.init()
})

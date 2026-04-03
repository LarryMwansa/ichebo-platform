// records-app.js — calls DRF endpoints through ICSRecords service

// =========================
// CREATE RECORD
// =========================
async function createRecord(data) {
  try {
    const newRecord = await ICSRecords.create({
      record_class: data.record_class || 'personal',
      record_family: data.record_family || 'journal',
      record_type: data.record_type || 'note',
      title: data.title || '',
      content: data.content || '',
      summary: data.summary || '',
      status: data.status || 'active',
      permissions_data: data.permissions_data || {},
      tags: data.tags || [],
      categories: data.categories || []
    });
    await ICSRecordsStore.createRecord(newRecord);
    return newRecord;
  } catch (error) {
    console.error('Failed to create record:', error);
    throw error;
  }
}

// =========================
// GET ALL RECORDS
// =========================
async function fetchRecords(filters = {}) {
  try {
    return await ICSRecordsStore.fetchList(filters);
  } catch (error) {
    console.error('Failed to fetch records:', error);
    throw error;
  }
}

// =========================
// GET SINGLE RECORD
// =========================
async function getRecord(id) {
  try {
    return await ICSRecordsStore.getRecord(id);
  } catch (error) {
    console.error('Failed to get record:', error);
    throw error;
  }
}

// =========================
// UPDATE RECORD
// =========================
async function updateRecord(id, data) {
  try {
    return await ICSRecordsStore.updateRecord(id, data);
  } catch (error) {
    console.error('Failed to update record:', error);
    throw error;
  }
}

// =========================
// DELETE RECORD
// =========================
async function deleteRecord(id) {
  try {
    return await ICSRecordsStore.deleteRecord(id);
  } catch (error) {
    console.error('Failed to delete record:', error);
    throw error;
  }
}

// =========================
// FILTER BY TYPE
// =========================
async function getRecordsByType(type) {
  try {
    const response = await fetchRecords({ record_type: type });
    return response.records || [];
  } catch (error) {
    console.error('Failed to get records by type:', error);
    throw error;
  }
}

// =========================
// FILTER BY FAMILY
// =========================
async function getRecordsByFamily(family) {
  try {
    const response = await fetchRecords({ record_family: family });
    return response.records || [];
  } catch (error) {
    console.error('Failed to get records by family:', error);
    throw error;
  }
}

// =========================
// GET STORE STATE
// =========================
function getStoreState() {
  return ICSRecordsStore.getState();
}

// =========================
// EXPORT GLOBAL
// =========================
window.ICSRecordsApp = {
  createRecord,
  fetchRecords,
  getRecord,
  updateRecord,
  deleteRecord,
  getRecordsByType,
  getRecordsByFamily,
  getStoreState
};
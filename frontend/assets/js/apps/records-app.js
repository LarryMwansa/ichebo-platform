import { getRecords, saveRecords } from "../../utils/storage.js";

// Generate ID
function generateId() {
  return "rec_" + Date.now();
}

// =========================
// CREATE RECORD
// =========================
export function createRecord(data) {
  const records = getRecords();

  const newRecord = {
    id: generateId(),
    user_id: "user_1", // later from auth
    type: data.type || "note",
    title: data.title || "",
    content: data.content || "",
    context: data.context || {},
    visibility: data.visibility || "private",
    created_at: new Date().toISOString()
  };

  records.unshift(newRecord);
  saveRecords(records);

  return newRecord;
}

// =========================
// GET ALL RECORDS
// =========================
export function fetchRecords() {
  return getRecords();
}

// =========================
// DELETE RECORD
// =========================
export function deleteRecord(id) {
  const records = getRecords().filter(r => r.id !== id);
  saveRecords(records);
}

// =========================
// FILTER BY TYPE
// =========================
export function getRecordsByType(type) {
  return getRecords().filter(r => r.type === type);
}
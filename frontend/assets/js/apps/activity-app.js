import { createRecord, fetchRecords, deleteRecord } from "../records";

let currentFilter = "all";
let searchQuery = "";

// =========================
// RENDER
// =========================
export function renderRecordsUI() {
  const list = document.getElementById("recordsList");
  const empty = document.getElementById("emptyState");

  let records = fetchRecords();

  // FILTER
  if (currentFilter !== "all") {
    records = records.filter(r => r.type === currentFilter);
  }

  // SEARCH
  if (searchQuery) {
    records = records.filter(r =>
      r.title.toLowerCase().includes(searchQuery) ||
      r.content.toLowerCase().includes(searchQuery)
    );
  }

  list.innerHTML = "";

  if (records.length === 0) {
    empty.style.display = "block";
    return;
  }

  empty.style.display = "none";

  records.forEach(record => {
    const card = document.createElement("div");
    card.className = "record-card";

    card.innerHTML = `
      <h3>${record.title}</h3>
      <div class="record-meta">
        ${record.type} • ${new Date(record.created_at).toLocaleString()}
      </div>
      <p>${record.content}</p>

      <div class="record-actions">
        <button data-id="${record.id}">Delete</button>
      </div>
    `;

    list.appendChild(card);
  });
}
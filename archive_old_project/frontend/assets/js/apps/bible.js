// /assets/js/bible.js

import { createRecord } from "/assets/js/records.js";

function initBiblePage() {
  const saveBtn = document.getElementById("saveNote");

  if (!saveBtn) return;

  saveBtn.addEventListener("click", () => {
    createRecord({
      type: "bible-note",
      title: "John 3:16",
      content: "For God so loved the world...",
      context: {
        app: "bible",
        reference: "John 3:16"
      }
    });

    alert("Saved to Records");
  });
}

document.addEventListener("DOMContentLoaded", initBiblePage);
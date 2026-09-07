const API_BASE = window.API_BASE_URL || "";

const form = document.getElementById("note-form");
const titleInput = document.getElementById("title-input");
const contentInput = document.getElementById("content-input");
const statusMsg = document.getElementById("status-msg");
const notesList = document.getElementById("notes-list");

async function loadNotes() {
  try {
    const res = await fetch(`${API_BASE}/api/notes`);
    const notes = await res.json();
    renderNotes(notes);
  } catch (err) {
    statusMsg.textContent = "مقدرش أوصل للسيرفر";
  }
}

function renderNotes(notes) {
  notesList.innerHTML = "";
  notes.forEach((note) => {
    const card = document.createElement("div");
    card.className = "note-card" + (note.is_done ? " done" : "");
    card.innerHTML = `
      <div class="note-header">
        <h3>${escapeHtml(note.title)}</h3>
        <button class="toggle-btn" data-id="${note.id}">
          ${note.is_done ? "↩️ ارجاع" : "✅ خلصت"}
        </button>
      </div>
      <p>${escapeHtml(note.content || "")}</p>
      <div class="note-footer">
        <button class="delete-btn" data-id="${note.id}">حذف</button>
      </div>
    `;
    notesList.appendChild(card);
  });

  document.querySelectorAll(".toggle-btn").forEach((btn) => {
    btn.addEventListener("click", async (e) => {
      const id = e.target.dataset.id;
      await fetch(`${API_BASE}/api/notes/${id}/toggle`, { method: "PATCH" });
      loadNotes();
    });
  });

  document.querySelectorAll(".delete-btn").forEach((btn) => {
    btn.addEventListener("click", async (e) => {
      const id = e.target.dataset.id;
      await fetch(`${API_BASE}/api/notes/${id}`, { method: "DELETE" });
      loadNotes();
    });
  });
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const title = titleInput.value.trim();
  if (!title) return;

  try {
    const res = await fetch(`${API_BASE}/api/notes`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, content: contentInput.value }),
    });

    if (res.ok) {
      titleInput.value = "";
      contentInput.value = "";
      statusMsg.textContent = "";
      loadNotes();
    } else {
      const data = await res.json();
      statusMsg.textContent = `خطأ: ${data.error}`;
    }
  } catch (err) {
    statusMsg.textContent = "حصل خطأ في الاتصال بالسيرفر";
  }
});

loadNotes();

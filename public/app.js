// Remember the selected user and the entry that is currently being edited.
let activeUserId = localStorage.getItem("moneyManagerUser") || "1";
let editingEntryId = null;
let currentEntries = [];

const entryForm = document.getElementById("entry-form");
const entryList = document.getElementById("entry-list");
const entryType = document.getElementById("entry-type");
const entryFilter = document.getElementById("entry-filter");
const searchInput = document.getElementById("search");
const categoryFilter = document.getElementById("category-filter");
const formMessage = document.getElementById("form-message");

document.getElementById("entry-date").value = today();
startPage();

async function request(url, options = {}) {
    // fetch sends a request from this page to the FastAPI server.
    const response = await fetch(url, options);
    const result = await response.json();
    if (!response.ok) throw new Error(result.detail || "Something went wrong.");
    return result;
}

async function startPage() {
    try {
        await loadUsers();
        await loadCategories();
        await loadEntries();
        await loadReport();
    } catch (error) {
        showMessage(error.message);
    }
}

async function loadUsers() {
    const users = await request("/api/users");
    const userSelect = document.getElementById("user-select");
    userSelect.innerHTML = users.map((user) =>
        `<option value="${user.id}">${escapeHtml(user.name)}</option>`
    ).join("");

    // If a saved profile was removed, select the first one that still exists.
    if (!users.some((user) => String(user.id) === activeUserId)) {
        activeUserId = String(users[0].id);
    }
    userSelect.value = activeUserId;
    localStorage.setItem("moneyManagerUser", activeUserId);
}

document.getElementById("user-select").addEventListener("change", async (event) => {
    activeUserId = event.target.value;
    localStorage.setItem("moneyManagerUser", activeUserId);
    resetForm();
    await loadEntries();
    await loadReport();
});

document.getElementById("add-user-button").addEventListener("click", async () => {
    const input = document.getElementById("new-user-name");
    const name = input.value.trim();
    if (!name) return;

    try {
        const user = await request("/api/users", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name }),
        });
        activeUserId = String(user.id);
        input.value = "";
        await loadUsers();
        document.getElementById("user-select").value = activeUserId;
        await loadEntries();
        await loadReport();
    } catch (error) {
        showMessage(error.message);
    }
});

async function loadCategories() {
    const allCategories = await request("/api/categories");
    const categories = allCategories.filter((item) => item.type === entryType.value);
    const filterCategories = allCategories.filter((item) => item.type === entryFilter.value);
    const entryCategory = document.getElementById("category");
    const filterCategory = categoryFilter;
    const previousEntryCategory = entryCategory.value;
    const previousFilterCategory = filterCategory.value;

    entryCategory.innerHTML = categories.map((item) =>
        `<option value="${escapeHtml(item.name)}">${escapeHtml(item.name)}</option>`
    ).join("");
    filterCategory.innerHTML = '<option value="">All categories</option>' + filterCategories.map((item) =>
        `<option value="${escapeHtml(item.name)}">${escapeHtml(item.name)}</option>`
    ).join("");

    if (categories.some((item) => item.name === previousEntryCategory)) {
        entryCategory.value = previousEntryCategory;
    }
    if (filterCategories.some((item) => item.name === previousFilterCategory)) {
        filterCategory.value = previousFilterCategory;
    }

    document.getElementById("category-list").innerHTML = categories.map((item) => `
        <span class="category-chip">
            ${escapeHtml(item.name)}
            <button type="button" aria-label="Delete ${escapeHtml(item.name)}" data-category-id="${item.id}">×</button>
        </span>
    `).join("");
}

document.getElementById("add-category-button").addEventListener("click", async () => {
    const input = document.getElementById("new-category");
    const name = input.value.trim();
    if (!name) return;

    try {
        await request("/api/categories", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name, type: entryType.value }),
        });
        input.value = "";
        await loadCategories();
        await loadEntries();
    } catch (error) {
        formMessage.textContent = error.message;
    }
});

document.getElementById("category-list").addEventListener("click", async (event) => {
    const button = event.target.closest("button[data-category-id]");
    if (!button) return;

    try {
        await request(`/api/categories/${button.dataset.categoryId}`, { method: "DELETE" });
        await loadCategories();
        await loadEntries();
    } catch (error) {
        formMessage.textContent = error.message;
    }
});

entryType.addEventListener("change", async () => {
    await loadCategories();
    await loadEntries();
});

entryFilter.addEventListener("change", async () => {
    entryType.value = entryFilter.value;
    document.getElementById("entries-heading").textContent = entryFilter.value === "income" ? "Income" : "Expenses";
    await loadCategories();
    await loadEntries();
});

categoryFilter.addEventListener("change", loadEntries);
searchInput.addEventListener("input", loadEntries);
document.getElementById("report-button").addEventListener("click", loadReport);
document.getElementById("cancel-button").addEventListener("click", resetForm);

entryForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const values = new FormData(entryForm);
    const entry = {
        user_id: Number(activeUserId),
        title: values.get("title").trim(),
        amount: Number(values.get("amount")),
        category: values.get("category"),
        entry_date: values.get("entry_date"),
        note: values.get("note").trim(),
    };
    const type = entryType.value;
    const url = editingEntryId === null
        ? `/api/entries?type=${type}`
        : `/api/entries/${editingEntryId}?type=${type}`;

    try {
        await request(url, {
            method: editingEntryId === null ? "POST" : "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(entry),
        });
        resetForm();
        formMessage.textContent = "Entry saved.";
        await loadEntries();
        await loadReport();
    } catch (error) {
        formMessage.textContent = error.message;
    }
});

async function loadEntries() {
    const type = entryFilter.value;
    const query = new URLSearchParams({
        user_id: activeUserId,
        type,
        search: searchInput.value.trim(),
        category: categoryFilter.value,
    });
    currentEntries = await request(`/api/entries?${query}`);

    if (currentEntries.length === 0) {
        entryList.innerHTML = '<p class="empty-state">No entries found.</p>';
        return;
    }

    entryList.innerHTML = currentEntries.map((entry) => `
        <article class="expense-item">
            <div>
                <p class="expense-title">${escapeHtml(entry.title)}</p>
                <p class="expense-details">${escapeHtml(entry.category)} · ${escapeHtml(entry.entry_date)}</p>
                ${entry.note ? `<p class="expense-note">${escapeHtml(entry.note)}</p>` : ""}
            </div>
            <div class="expense-side">
                <p class="expense-amount ${type === "income" ? "income-amount" : ""}">${type === "income" ? "+ " : "− "}${formatMoney(entry.amount)}</p>
                <div class="item-actions">
                    <button class="text-button" data-action="edit" data-id="${entry.id}">Edit</button>
                    <button class="text-button delete" data-action="delete" data-id="${entry.id}">Delete</button>
                </div>
            </div>
        </article>
    `).join("");
}

entryList.addEventListener("click", async (event) => {
    const button = event.target.closest("button[data-action]");
    if (!button) return;

    const entry = currentEntries.find((item) => item.id === Number(button.dataset.id));
    if (!entry) return;

    if (button.dataset.action === "edit") {
        editingEntryId = entry.id;
        entryType.value = entry.type;
        await loadCategories();
        document.getElementById("title").value = entry.title;
        document.getElementById("amount").value = entry.amount;
        document.getElementById("category").value = entry.category;
        document.getElementById("entry-date").value = entry.entry_date;
        document.getElementById("note").value = entry.note;
        document.getElementById("form-heading").textContent = "Edit entry";
        document.getElementById("submit-button").textContent = "Update entry";
        document.getElementById("cancel-button").classList.remove("hidden");
        document.getElementById("title").focus();
        return;
    }

    if (window.confirm("Delete this entry?")) {
        try {
            const query = new URLSearchParams({ type: entry.type, user_id: activeUserId });
            await request(`/api/entries/${entry.id}?${query}`, { method: "DELETE" });
            await loadEntries();
            await loadReport();
        } catch (error) {
            showMessage(error.message);
        }
    }
});

async function loadReport() {
    const query = new URLSearchParams({ user_id: activeUserId });
    const start = document.getElementById("report-start").value;
    const end = document.getElementById("report-end").value;
    if (start) query.set("start_date", start);
    if (end) query.set("end_date", end);

    try {
        const report = await request(`/api/reports?${query}`);
        document.getElementById("report-income").textContent = formatMoney(report.income_total);
        document.getElementById("report-expenses").textContent = formatMoney(report.expense_total);
        document.getElementById("report-balance").textContent = formatMoney(report.balance);

        const rows = report.category_totals;
        document.getElementById("report-breakdown").innerHTML = rows.length
            ? rows.map((item) => `
                <div class="breakdown-row">
                    <span>${escapeHtml(item.category)} <small>(${item.type})</small></span>
                    <strong>${formatMoney(item.total)}</strong>
                </div>
            `).join("")
            : '<p class="empty-state">No records in this date range.</p>';
    } catch (error) {
        showMessage(error.message);
    }
}

function resetForm() {
    editingEntryId = null;
    entryForm.reset();
    entryType.value = "expense";
    document.getElementById("entry-date").value = today();
    document.getElementById("form-heading").textContent = "Add an entry";
    document.getElementById("submit-button").textContent = "Save entry";
    document.getElementById("cancel-button").classList.add("hidden");
    loadCategories();
}

function today() {
    return new Date().toISOString().slice(0, 10);
}

function showMessage(message) {
    document.getElementById("page-message").textContent = message;
}

function formatMoney(amount) {
    return new Intl.NumberFormat("en-IN", {
        style: "currency",
        currency: "INR",
        minimumFractionDigits: 2,
    }).format(amount);
}

function escapeHtml(value) {
    // Display user-entered text without allowing it to be treated as HTML.
    return String(value).replace(/[&<>"']/g, (character) => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;",
    })[character]);
}

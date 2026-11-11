import { api } from "../api.js";

let academicTerms = [];

const escapeHTML = (value) => {
  return String(value ?? "").replace(
    /[&<>"']/g,
    (char) =>
      ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
      })[char],
  );
};

const isActive = (value) => value === true || value === 1 || value === "1";

export async function renderAcademicTerms(container) {
  container.innerHTML = `
        <div class="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-3">
            <div>
                <h4 class="mb-1">Academic Terms</h4>
                <p class="text-muted mb-0">
                    Manage academic years and semesters.
                </p>
            </div>

            <button class="btn btn-primary" id="add-term-btn">
                <i class="bi bi-plus-lg me-1"></i>
                Add Academic Term
            </button>
        </div>

        <div id="academic-term-alert"></div>

        <!-- Summary Cards -->
        <div class="row g-3 mb-4">

            <div class="col-md-4">
                <div class="card border-0 shadow-sm p-3">
                    <small class="text-muted">Total Academic Terms</small>
                    <h3 id="total-terms">0</h3>
                </div>
            </div>

            <div class="col-md-4">
                <div class="card border-0 shadow-sm p-3">
                    <small class="text-muted">Active Terms</small>
                    <h5 id="active-term-name" class="mt-2">None</h5>
                </div>
            </div>

            <div class="col-md-4">
                <div class="card border-0 shadow-sm p-3">
                    <small class="text-muted">Inactive Terms</small>
                    <h3 id="inactive-terms">0</h3>
                </div>
            </div>

        </div>

        <!-- Academic Terms Table -->
        <div class="card border-0 shadow-sm">

            <div class="card-body">

                <div class="row mb-3">
                    <div class="col-md-5">
                        <input
                            type="search"
                            id="academic-term-search"
                            class="form-control"
                            placeholder="Search academic term..."
                        >
                    </div>
                </div>

                <div class="table-responsive">
                    <table class="table align-middle">

                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Term Name</th>
                                <th>Academic Year</th>
                                <th>Semester</th>
                                <th>Status</th>
                                <th>Created At</th>
                                <th class="text-end">Actions</th>
                            </tr>
                        </thead>

                        <tbody id="academic-terms-table-body">
                            <tr>
                                <td colspan="7" class="text-center py-4">
                                    <div class="spinner-border spinner-border-sm text-primary"></div>
                                    Loading academic terms...
                                </td>
                            </tr>
                        </tbody>

                    </table>
                </div>

                <div class="text-muted small" id="academic-term-count"></div>

            </div>
        </div>

        <!-- Add/Edit Modal -->
        <div class="modal fade" id="academic-term-modal" tabindex="-1">

            <div class="modal-dialog">

                <div class="modal-content">

                    <form id="academic-term-form">

                        <div class="modal-header">
                            <h5 class="modal-title" id="academic-term-modal-title">
                                Add Academic Term
                            </h5>

                            <button
                                type="button"
                                class="btn-close"
                                data-bs-dismiss="modal"
                            ></button>
                        </div>

                        <div class="modal-body">

                            <input type="hidden" id="academic-term-id">

                            <div class="mb-3">
                                <label class="form-label">
                                    Term Name *
                                </label>

                                <input
                                    type="text"
                                    id="term-name"
                                    class="form-control"
                                    placeholder="Fall 2026"
                                    required
                                    maxlength="100"
                                >

                                <small class="text-muted">
                                    Example: Fall 2026
                                </small>
                            </div>

                            <div class="mb-3">
                                <label class="form-label">
                                    Academic Year *
                                </label>

                                <input
                                    type="text"
                                    id="term-academic-year"
                                    class="form-control"
                                    placeholder="2026-2027"
                                    required
                                    maxlength="30"
                                >
                            </div>

                            <div class="mb-3">
                                <label class="form-label">
                                    Semester *
                                </label>

                                <select
                                    id="term-semester"
                                    class="form-select"
                                    required
                                >
                                    <option value="">Select Semester</option>
                                    <option value="1st">1st Semester</option>
                                    <option value="2nd">2nd Semester</option>
                                    <option value="3rd">3rd Semester</option>
                                    <option value="4th">4th Semester</option>
                                    <option value="5th">5th Semester</option>
                                    <option value="6th">6th Semester</option>
                                    <option value="7th">7th Semester</option>
                                    <option value="8th">8th Semester</option>
                                    <option value="Summer">Summer Semester</option>
                                </select>
                            </div>

                            <div class="form-check form-switch">
                                <input
                                    class="form-check-input"
                                    type="checkbox"
                                    id="term-is-active"
                                >

                                <label class="form-check-label" for="term-is-active">
                                    Set as Active Academic Term
                                </label>
                            </div>

                            <div class="alert alert-info mt-3 mb-0 small">
                                Terms are managed independently. Active and inactive
                                terms can both be used for sections, offerings, and allocations.
                            </div>

                            <div
                                id="academic-term-form-error"
                                class="text-danger small mt-3"
                            ></div>

                        </div>

                        <div class="modal-footer">

                            <button
                                type="button"
                                class="btn btn-light"
                                data-bs-dismiss="modal"
                            >
                                Cancel
                            </button>

                            <button
                                type="submit"
                                class="btn btn-primary"
                                id="save-academic-term-btn"
                            >
                                Save Academic Term
                            </button>

                        </div>

                    </form>

                </div>

            </div>

        </div>
    `;

  const modalElement = document.getElementById("academic-term-modal");
  const modal = bootstrap.Modal.getOrCreateInstance(modalElement);

  document.getElementById("add-term-btn").addEventListener("click", () => {
    openCreateModal();
    modal.show();
  });

  document
    .getElementById("academic-term-search")
    .addEventListener("input", (event) => {
      renderTable(event.target.value);
    });

  document
    .getElementById("academic-term-form")
    .addEventListener("submit", async (event) => {
      event.preventDefault();
      await saveAcademicTerm(modal);
    });

  await loadAcademicTerms();
}

// Load all academic terms
async function loadAcademicTerms() {
  try {
    academicTerms = await api.get("/academic-terms");

    renderTable();
    renderSummary();
  } catch (error) {
    showAlert(error.message, "danger");

    document.getElementById("academic-terms-table-body").innerHTML = `
            <tr>
                <td colspan="7" class="text-center text-danger py-4">
                    Unable to load academic terms.
                    <button
                        class="btn btn-sm btn-outline-primary ms-2"
                        id="retry-academic-terms"
                    >
                        Retry
                    </button>
                </td>
            </tr>
        `;

    document
      .getElementById("retry-academic-terms")
      .addEventListener("click", loadAcademicTerms);
  }
}

// Render summary cards
function renderSummary() {
  const activeTerms = academicTerms.filter((term) => isActive(term.is_active));

  document.getElementById("total-terms").textContent = academicTerms.length;

  document.getElementById("inactive-terms").textContent =
    academicTerms.length - activeTerms.length;

  document.getElementById("active-term-name").textContent = activeTerms.length
    ? activeTerms.map((term) => term.name).join(", ")
    : "None";
}

// Render table
function renderTable(search = "") {
  const tbody = document.getElementById("academic-terms-table-body");

  const keyword = search.toLowerCase();

  const filtered = academicTerms.filter((term) => {
    return (
      String(term.name ?? "")
        .toLowerCase()
        .includes(keyword) ||
      String(term.academic_year ?? "")
        .toLowerCase()
        .includes(keyword) ||
      String(term.semester ?? "")
        .toLowerCase()
        .includes(keyword)
    );
  });

  document.getElementById("academic-term-count").textContent =
    `Showing ${filtered.length} of ${academicTerms.length} academic terms`;

  if (!filtered.length) {
    tbody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center text-muted py-4">
                    No academic terms found.
                </td>
            </tr>
        `;
    return;
  }

  tbody.innerHTML = filtered
    .map((term) => {
      const active = isActive(term.is_active);

      return `
            <tr>

                <td>${escapeHTML(term.id)}</td>

                <td class="fw-semibold">
                    ${escapeHTML(term.name)}
                </td>

                <td>${escapeHTML(term.academic_year)}</td>

                <td>
                    <span class="badge bg-light text-dark">
                        ${escapeHTML(term.semester)}
                    </span>
                </td>

                <td>
                    <span class="badge ${
                      active
                        ? "bg-success-subtle text-success"
                        : "bg-secondary-subtle text-secondary"
                    }">
                        ${active ? "Active" : "Inactive"}
                    </span>
                </td>

                <td>${escapeHTML(term.created_at || "-")}</td>

                <td class="text-end">

                    <div class="btn-group btn-group-sm">

                        <button
                            class="btn btn-outline-primary"
                            data-action="edit"
                            data-id="${Number(term.id)}"
                            title="Edit academic term"
                        >
                            <i class="bi bi-pencil"></i>
                        </button>

                        <button
                            class="btn ${active ? "btn-outline-secondary" : "btn-outline-success"}"
                            data-action="${active ? "deactivate" : "activate"}"
                            data-id="${Number(term.id)}"
                            title="${active ? "Deactivate" : "Activate"} this academic term"
                        >
                            <i class="bi ${active ? "bi-pause-circle" : "bi-play-circle"}"></i>
                        </button>

                    </div>

                </td>

            </tr>
        `;
    })
    .join("");

  tbody.querySelectorAll("button[data-action]").forEach((button) => {
    button.addEventListener("click", () => {
      handleAction(button.dataset.action, Number(button.dataset.id));
    });
  });
}

// Open create modal
function openCreateModal() {
  document.getElementById("academic-term-form").reset();

  document.getElementById("academic-term-id").value = "";
  document.getElementById("term-is-active").checked = false;

  document.getElementById("academic-term-modal-title").textContent =
    "Add Academic Term";

  document.getElementById("save-academic-term-btn").textContent =
    "Save Academic Term";

  document.getElementById("academic-term-form-error").textContent = "";
}

// Open edit modal
async function openEditModal(id) {
  try {
    const term = await api.get(`/academic-terms/${id}`);

    document.getElementById("academic-term-id").value = term.id;
    document.getElementById("term-name").value = term.name;
    document.getElementById("term-academic-year").value = term.academic_year;

    document.getElementById("term-semester").value = term.semester;

    document.getElementById("term-is-active").checked = isActive(
      term.is_active,
    );

    document.getElementById("academic-term-modal-title").textContent =
      "Edit Academic Term";

    document.getElementById("save-academic-term-btn").textContent =
      "Update Academic Term";

    document.getElementById("academic-term-form-error").textContent = "";

    bootstrap.Modal.getOrCreateInstance(
      document.getElementById("academic-term-modal"),
    ).show();
  } catch (error) {
    showAlert(error.message, "danger");
  }
}

// Create or update academic term
async function saveAcademicTerm(modal) {
  const id = document.getElementById("academic-term-id").value;

  const payload = {
    name: document.getElementById("term-name").value.trim(),
    academic_year: document.getElementById("term-academic-year").value.trim(),
    semester: document.getElementById("term-semester").value,
    is_active: document.getElementById("term-is-active").checked,
  };

  const errorElement = document.getElementById("academic-term-form-error");
  const saveButton = document.getElementById("save-academic-term-btn");

  if (!payload.name || !payload.academic_year || !payload.semester) {
    errorElement.textContent = "Please complete all required fields.";
    return;
  }

  saveButton.disabled = true;
  saveButton.textContent = "Saving...";

  try {
    if (id) {
      await api.put(`/academic-terms/${id}`, payload);

      showAlert("Academic term updated successfully.", "success");
    } else {
      await api.post("/academic-terms", payload);

      showAlert("Academic term created successfully.", "success");
    }

    modal.hide();

    await loadAcademicTerms();
  } catch (error) {
    errorElement.textContent = error.message;
  } finally {
    saveButton.disabled = false;

    saveButton.textContent = id ? "Update Academic Term" : "Save Academic Term";
  }
}

// Handle actions
async function handleAction(action, id) {
  if (action === "edit") {
    await openEditModal(id);
    return;
  }

  if (action === "activate") {
    const term = academicTerms.find((item) => Number(item.id) === id);

    if (!term) return;

    try {
      await api.put(`/academic-terms/${id}/activate`, {});
      showAlert(`${term.name} is active. Other terms were not changed.`, "success");

      await loadAcademicTerms();
    } catch (error) {
      showAlert(error.message, "danger");
    }
    return;
  }

  if (action === "deactivate") {
    const term = academicTerms.find((item) => Number(item.id) === id);
    if (!term) return;
    try {
      await api.put(`/academic-terms/${id}/deactivate`, {});
      showAlert(`${term.name} is inactive.`, "success");
      await loadAcademicTerms();
    } catch (error) {
      showAlert(error.message, "danger");
    }
  }
}

// Display notifications
function showAlert(message, type = "success") {
  const container = document.getElementById("academic-term-alert");

  if (!container) return;

  container.innerHTML = `
        <div class="alert alert-${type} alert-dismissible fade show">
            ${escapeHTML(message)}

            <button
                type="button"
                class="btn-close"
                data-bs-dismiss="alert"
            ></button>
        </div>
    `;

  window.setTimeout(() => {
    const alert = container.querySelector(".alert");

    if (alert) {
      bootstrap.Alert.getOrCreateInstance(alert).close();
    }
  }, 4000);
}

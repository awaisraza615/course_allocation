import { api } from "../api.js";

let sections = [];
let departments = [];
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

export async function renderSections(container) {
  container.innerHTML = `
        <!-- Header -->
        <div class="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-3">

            <div>
                <h4 class="mb-1">Sections</h4>
                <p class="text-muted mb-0">
                    Manage department-wise academic sections.
                </p>
            </div>

            <button class="btn btn-primary" id="add-section-btn">
                <i class="bi bi-plus-lg me-1"></i>
                Add Section
            </button>

        </div>

        <div id="section-alert"></div>

        <!-- Summary -->
        <div class="row g-3 mb-4">

            <div class="col-md-4">
                <div class="card border-0 shadow-sm p-3">
                    <small class="text-muted">Total Sections</small>
                    <h3 id="total-sections">0</h3>
                </div>
            </div>

            <div class="col-md-4">
                <div class="card border-0 shadow-sm p-3">
                    <small class="text-muted">Active Sections</small>
                    <h3 id="active-sections">0</h3>
                </div>
            </div>

            <div class="col-md-4">
                <div class="card border-0 shadow-sm p-3">
                    <small class="text-muted">Inactive Sections</small>
                    <h3 id="inactive-sections">0</h3>
                </div>
            </div>

        </div>

        <!-- Section Table -->
        <div class="card border-0 shadow-sm">

            <div class="card-body">

                <!-- Search and Filters -->
                <div class="row g-3 mb-4">

                    <div class="col-md-4">
                        <input
                            type="search"
                            id="section-search"
                            class="form-control"
                            placeholder="Search section..."
                        >
                    </div>

                    <div class="col-md-4">
                        <select id="filter-department" class="form-select">
                            <option value="">All Departments</option>
                        </select>
                    </div>

                    <div class="col-md-4">
                        <select id="filter-academic-term" class="form-select">
                            <option value="">All Academic Terms</option>
                        </select>
                    </div>

                </div>

                <div class="table-responsive">

                    <table class="table align-middle">

                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Section</th>
                                <th>Department</th>
                                <th>Department Code</th>
                                <th>Academic Term</th>
                                <th>Semester</th>
                                <th>Status</th>
                                <th>Created At</th>
                                <th class="text-end">Actions</th>
                            </tr>
                        </thead>

                        <tbody id="sections-table-body">

                            <tr>
                                <td colspan="9" class="text-center py-4">
                                    <div class="spinner-border spinner-border-sm text-primary"></div>
                                    Loading sections...
                                </td>
                            </tr>

                        </tbody>

                    </table>

                </div>

                <div class="text-muted small" id="section-count"></div>

            </div>

        </div>

        <!-- Add/Edit Section Modal -->
        <div class="modal fade" id="section-modal" tabindex="-1">

            <div class="modal-dialog">

                <div class="modal-content">

                    <form id="section-form">

                        <div class="modal-header">

                            <h5 class="modal-title" id="section-modal-title">
                                Add Section
                            </h5>

                            <button
                                type="button"
                                class="btn-close"
                                data-bs-dismiss="modal"
                            ></button>

                        </div>

                        <div class="modal-body">

                            <input type="hidden" id="section-id">

                            <!-- Section Name -->
                            <div class="mb-3">

                                <label class="form-label">
                                    Section Name *
                                </label>

                                <input
                                    type="text"
                                    id="section-name"
                                    class="form-control"
                                    placeholder="A"
                                    maxlength="50"
                                    required
                                >

                            </div>

                            <!-- Department -->
                            <div class="mb-3">

                                <label class="form-label">
                                    Department *
                                </label>

                                <select
                                    id="section-department"
                                    class="form-select"
                                    required
                                >
                                    <option value="">Select Department</option>
                                </select>

                            </div>

                            <!-- Academic Term -->
                            <div class="mb-3">

                                <label class="form-label">
                                    Academic Term *
                                </label>

                                <select
                                    id="section-academic-term"
                                    class="form-select"
                                    required
                                >
                                    <option value="">Select Academic Term</option>
                                </select>

                            </div>

                            <!-- Status -->
                            <div class="form-check form-switch">

                                <input
                                    class="form-check-input"
                                    type="checkbox"
                                    id="section-active"
                                    checked
                                >

                                <label class="form-check-label" for="section-active">
                                    Active Section
                                </label>

                            </div>

                            <div
                                id="section-form-error"
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
                                id="save-section-btn"
                            >
                                Save Section
                            </button>

                        </div>

                    </form>

                </div>

            </div>

        </div>
    `;

  // Initialize event listeners
  document
    .getElementById("add-section-btn")
    .addEventListener("click", () => openCreateModal());

  document
    .getElementById("section-search")
    .addEventListener("input", () => renderTable());

  document
    .getElementById("filter-department")
    .addEventListener("change", () => renderTable());

  document
    .getElementById("filter-academic-term")
    .addEventListener("change", () => renderTable());

  document
    .getElementById("section-form")
    .addEventListener("submit", async (event) => {
      event.preventDefault();
      await saveSection();
    });

  await loadInitialData();
}

// Load sections, departments and academic terms
async function loadInitialData() {
  try {
    const [sectionData, departmentData, termData] = await Promise.all([
      api.get("/sections"),
      api.get("/departments"),
      api.get("/academic-terms"),
    ]);

    sections = sectionData;
    departments = departmentData;
    academicTerms = termData;

    populateDropdowns();
    renderTable();
    renderSummary();
  } catch (error) {
    showAlert(error.message, "danger");

    document.getElementById("sections-table-body").innerHTML = `
            <tr>
                <td colspan="9" class="text-center text-danger py-4">
                    Unable to load section data.

                    <button
                        class="btn btn-sm btn-outline-primary ms-2"
                        id="retry-sections"
                    >
                        Retry
                    </button>
                </td>
            </tr>
        `;

    document
      .getElementById("retry-sections")
      .addEventListener("click", loadInitialData);
  }
}

// Populate all dropdowns
function populateDropdowns() {
  const departmentOptions = departments
    .map(
      (department) => `
        <option value="${Number(department.id)}">
            ${escapeHTML(department.name)}
            (${escapeHTML(department.code)})
            ${isActive(department.is_active) ? "" : "- Inactive"}
        </option>
    `,
    )
    .join("");

  const termOptions = academicTerms
    .map(
      (term) => `
        <option value="${Number(term.id)}">
            ${escapeHTML(term.name)}
            (${escapeHTML(term.academic_year)})
            ${isActive(term.is_active) ? "- Active" : "- Inactive"}
        </option>
    `,
    )
    .join("");

  document.getElementById("section-department").innerHTML = `
        <option value="">Select Department</option>
        ${departmentOptions}
    `;

  document.getElementById("section-academic-term").innerHTML = `
        <option value="">Select Academic Term</option>
        ${termOptions}
    `;

  document.getElementById("filter-department").innerHTML = `
        <option value="">All Departments</option>
        ${departmentOptions}
    `;

  document.getElementById("filter-academic-term").innerHTML = `
        <option value="">All Academic Terms</option>
        ${termOptions}
    `;
}

// Summary cards
function renderSummary() {
  const activeCount = sections.filter((section) =>
    isActive(section.is_active),
  ).length;

  document.getElementById("total-sections").textContent = sections.length;

  document.getElementById("active-sections").textContent = activeCount;

  document.getElementById("inactive-sections").textContent =
    sections.length - activeCount;
}

// Render sections table
function renderTable() {
  const tbody = document.getElementById("sections-table-body");

  if (!tbody) return;

  const keyword = document
    .getElementById("section-search")
    .value.trim()
    .toLowerCase();

  const departmentId = document.getElementById("filter-department").value;

  const termId = document.getElementById("filter-academic-term").value;

  const filtered = sections.filter((section) => {
    const matchesSearch =
      String(section.name ?? "")
        .toLowerCase()
        .includes(keyword) ||
      String(section.department_name ?? "")
        .toLowerCase()
        .includes(keyword) ||
      String(section.department_code ?? "")
        .toLowerCase()
        .includes(keyword) ||
      String(section.academic_term_name ?? "")
        .toLowerCase()
        .includes(keyword) ||
      String(section.academic_year ?? "")
        .toLowerCase()
        .includes(keyword);

    const matchesDepartment =
      !departmentId || String(section.department_id) === departmentId;

    const matchesTerm = !termId || String(section.academic_term_id) === termId;

    return matchesSearch && matchesDepartment && matchesTerm;
  });

  document.getElementById("section-count").textContent =
    `Showing ${filtered.length} of ${sections.length} sections`;

  if (!filtered.length) {
    tbody.innerHTML = `
            <tr>
                <td colspan="9" class="text-center text-muted py-4">
                    No sections found.
                </td>
            </tr>
        `;

    return;
  }

  tbody.innerHTML = filtered
    .map((section) => {
      const active = isActive(section.is_active);

      return `
            <tr>

                <td>${escapeHTML(section.id)}</td>

                <td class="fw-semibold">
                    ${escapeHTML(section.name)}
                </td>

                <td>
                    ${escapeHTML(section.department_name)}
                </td>

                <td>
                    <span class="badge bg-light text-dark">
                        ${escapeHTML(section.department_code)}
                    </span>
                </td>

                <td>
                    ${escapeHTML(section.academic_term_name)}
                </td>

                <td>
                    ${escapeHTML(section.semester)}
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

                <td>
                    ${escapeHTML(section.created_at || "-")}
                </td>

                <td class="text-end">

                    <div class="btn-group btn-group-sm">

                        <button
                            class="btn btn-outline-primary"
                            data-action="edit"
                            data-id="${Number(section.id)}"
                            title="Edit section"
                        >
                            <i class="bi bi-pencil"></i>
                        </button>

                        <button
                            class="btn btn-outline-${
                              active ? "danger" : "success"
                            }"
                            data-action="${active ? "deactivate" : "activate"}"
                            data-id="${Number(section.id)}"
                            title="${
                              active ? "Deactivate" : "Activate"
                            } section"
                        >
                            <i class="bi bi-${
                              active ? "toggle-off" : "toggle-on"
                            }"></i>
                        </button>

                        <button
                            class="btn btn-outline-danger"
                            data-action="permanent-delete"
                            data-id="${Number(section.id)}"
                            title="Permanently delete section and all related offerings, allocations, and history"
                        >
                            <i class="bi bi-trash"></i>
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

// Create section modal
function openCreateModal() {
  if (!departments.length || !academicTerms.length) {
    showAlert(
      "Create a department and academic term before adding sections.",
      "warning",
    );
    return;
  }

  document.getElementById("section-form").reset();

  document.getElementById("section-id").value = "";
  document.getElementById("section-active").checked = true;

  document.getElementById("section-modal-title").textContent = "Add Section";

  document.getElementById("save-section-btn").textContent = "Save Section";

  document.getElementById("section-form-error").textContent = "";

  bootstrap.Modal.getOrCreateInstance(
    document.getElementById("section-modal"),
  ).show();
}

// Edit section modal
async function openEditModal(id) {
  try {
    const section = await api.get(`/sections/${id}`);

    document.getElementById("section-id").value = section.id;

    document.getElementById("section-name").value = section.name;

    document.getElementById("section-department").value = section.department_id;

    document.getElementById("section-academic-term").value =
      section.academic_term_id;

    document.getElementById("section-active").checked = isActive(
      section.is_active,
    );

    document.getElementById("section-modal-title").textContent = "Edit Section";

    document.getElementById("save-section-btn").textContent = "Update Section";

    document.getElementById("section-form-error").textContent = "";

    bootstrap.Modal.getOrCreateInstance(
      document.getElementById("section-modal"),
    ).show();
  } catch (error) {
    showAlert(error.message, "danger");
  }
}

// Save section
async function saveSection() {
  const id = document.getElementById("section-id").value;

  const payload = {
    name: document.getElementById("section-name").value.trim(),

    department_id: Number(document.getElementById("section-department").value),

    academic_term_id: Number(
      document.getElementById("section-academic-term").value,
    ),

    is_active: document.getElementById("section-active").checked,
  };

  const errorElement = document.getElementById("section-form-error");

  const saveButton = document.getElementById("save-section-btn");

  if (!payload.name || !payload.department_id || !payload.academic_term_id) {
    errorElement.textContent = "Please complete all required fields.";

    return;
  }

  saveButton.disabled = true;
  saveButton.textContent = "Saving...";

  try {
    if (id) {
      await api.put(`/sections/${id}`, payload);

      showAlert("Section updated successfully.", "success");
    } else {
      await api.post("/sections", payload);

      showAlert("Section created successfully.", "success");
    }

    bootstrap.Modal.getOrCreateInstance(
      document.getElementById("section-modal"),
    ).hide();

    await loadInitialData();
  } catch (error) {
    errorElement.textContent = error.message;
  } finally {
    saveButton.disabled = false;

    saveButton.textContent = id ? "Update Section" : "Save Section";
  }
}

// Activate / deactivate / edit
async function handleAction(action, id) {
  const section = sections.find((item) => Number(item.id) === id);

  if (!section) return;

  if (action === "edit") {
    await openEditModal(id);
    return;
  }

  if (action === "deactivate") {
    if (!confirm(`Deactivate section "${section.name}"?`)) {
      return;
    }

    try {
      await api.delete(`/sections/${id}`);

      showAlert("Section deactivated successfully.", "success");

      await loadInitialData();
    } catch (error) {
      showAlert(error.message, "danger");
    }

    return;
  }

  if (action === "activate") {
    if (!confirm(`Activate section "${section.name}"?`)) {
      return;
    }

    try {
      await api.put(`/sections/${id}`, {
        is_active: true,
      });

      showAlert("Section activated successfully.", "success");

      await loadInitialData();
    } catch (error) {
      showAlert(error.message, "danger");
    }
    return;
  }

  if (action === "permanent-delete") {
    const confirmed = confirm(
      `Permanently delete section "${section.name}"?\n\nThis also permanently deletes all offerings, allocations, and allocation history for this section. This cannot be undone.`,
    );
    if (!confirmed) return;

    try {
      const result = await api.delete(`/sections/${id}/permanent`);
      showAlert(
        `Section permanently deleted with ${result.deleted_offerings} offerings, ${result.deleted_allocations} allocations, and ${result.deleted_allocation_history} history records.`,
        "success",
      );
      await loadInitialData();
    } catch (error) {
      showAlert(error.message, "danger");
    }
  }
}

// Notifications
function showAlert(message, type = "success") {
  const container = document.getElementById("section-alert");

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

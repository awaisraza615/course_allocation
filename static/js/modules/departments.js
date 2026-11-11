import { api } from "../api.js";

let departments = [];

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

export async function renderDepartments(container) {
  container.innerHTML = `
        <div class="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-3">
            <div>
                <h4 class="mb-1">Departments</h4>
                <p class="text-muted mb-0">
                    Manage university academic departments.
                </p>
            </div>

            <button class="btn btn-primary" id="add-department-btn">
                <i class="bi bi-plus-lg me-1"></i>
                Add Department
            </button>
        </div>

        <div id="department-alert"></div>

        <div class="card border-0 shadow-sm">
            <div class="card-body">

                <div class="row mb-3">
                    <div class="col-md-5">
                        <input
                            type="search"
                            id="department-search"
                            class="form-control"
                            placeholder="Search department name or code..."
                        >
                    </div>
                </div>

                <div class="table-responsive">
                    <table class="table align-middle">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Department Name</th>
                                <th>Code</th>
                                <th>Status</th>
                                <th>Created At</th>
                                <th class="text-end">Actions</th>
                            </tr>
                        </thead>

                        <tbody id="departments-table-body">
                            <tr>
                                <td colspan="6" class="text-center py-4">
                                    <div class="spinner-border spinner-border-sm text-primary"></div>
                                    Loading departments...
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <div class="text-muted small" id="department-count"></div>

            </div>
        </div>

        <!-- Department Modal -->
        <div class="modal fade" id="department-modal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">

                    <form id="department-form">

                        <div class="modal-header">
                            <h5 class="modal-title" id="department-modal-title">
                                Add Department
                            </h5>
                            <button
                                type="button"
                                class="btn-close"
                                data-bs-dismiss="modal"
                            ></button>
                        </div>

                        <div class="modal-body">

                            <input type="hidden" id="department-id">

                            <div class="mb-3">
                                <label class="form-label">
                                    Department Name *
                                </label>
                                <input
                                    type="text"
                                    class="form-control"
                                    id="department-name"
                                    placeholder="Artificial Intelligence"
                                    required
                                    maxlength="150"
                                >
                            </div>

                            <div class="mb-3">
                                <label class="form-label">
                                    Department Code *
                                </label>
                                <input
                                    type="text"
                                    class="form-control text-uppercase"
                                    id="department-code"
                                    placeholder="AI"
                                    required
                                    maxlength="20"
                                >
                            </div>

                            <div class="form-check form-switch">
                                <input
                                    class="form-check-input"
                                    type="checkbox"
                                    id="department-active"
                                    checked
                                >
                                <label class="form-check-label" for="department-active">
                                    Active Department
                                </label>
                            </div>

                            <div id="department-form-error" class="text-danger small mt-3"></div>

                        </div>

                        <div class="modal-footer">
                            <button
                                type="button"
                                class="btn btn-light"
                                data-bs-dismiss="modal"
                            >
                                Cancel
                            </button>

                            <button type="submit" class="btn btn-primary" id="save-department-btn">
                                Save Department
                            </button>
                        </div>

                    </form>

                </div>
            </div>
        </div>

        <!-- Department Sections Modal -->
        <div class="modal fade" id="department-sections-modal" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">

                    <div class="modal-header">
                        <h5 class="modal-title">Department Sections</h5>
                        <button
                            type="button"
                            class="btn-close"
                            data-bs-dismiss="modal"
                        ></button>
                    </div>

                    <div class="modal-body" id="department-sections-content">
                    </div>

                </div>
            </div>
        </div>
    `;

  const modalElement = document.getElementById("department-modal");
  const modal = bootstrap.Modal.getOrCreateInstance(modalElement);

  document
    .getElementById("add-department-btn")
    .addEventListener("click", () => {
      openCreateModal();
      modal.show();
    });

  document
    .getElementById("department-search")
    .addEventListener("input", (event) => {
      renderTable(event.target.value);
    });

  document
    .getElementById("department-form")
    .addEventListener("submit", async (event) => {
      event.preventDefault();
      await saveDepartment(modal);
    });

  await loadDepartments();
}

async function loadDepartments() {
  try {
    departments = await api.get("/departments");
    renderTable();
  } catch (error) {
    showAlert(error.message, "danger");

    document.getElementById("departments-table-body").innerHTML = `
            <tr>
                <td colspan="6" class="text-center text-danger py-4">
                    Unable to load departments.
                    <button class="btn btn-sm btn-outline-primary ms-2" id="retry-departments">
                        Retry
                    </button>
                </td>
            </tr>
        `;

    document
      .getElementById("retry-departments")
      .addEventListener("click", loadDepartments);
  }
}

function renderTable(search = "") {
  const tbody = document.getElementById("departments-table-body");

  const filtered = departments.filter((department) => {
    const keyword = search.toLowerCase();

    return (
      String(department.name ?? "")
        .toLowerCase()
        .includes(keyword) ||
      String(department.code ?? "")
        .toLowerCase()
        .includes(keyword)
    );
  });

  document.getElementById("department-count").textContent =
    `Showing ${filtered.length} of ${departments.length} departments`;

  if (!filtered.length) {
    tbody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center text-muted py-4">
                    No departments found.
                </td>
            </tr>
        `;
    return;
  }

  tbody.innerHTML = filtered
    .map((department) => {
      const active = isActive(department.is_active);

      return `
            <tr>
                <td>${escapeHTML(department.id)}</td>

                <td class="fw-semibold">
                    ${escapeHTML(department.name)}
                </td>

                <td>
                    <span class="badge bg-light text-dark">
                        ${escapeHTML(department.code)}
                    </span>
                </td>

                <td>
                    <span class="badge ${active ? "bg-success-subtle text-success" : "bg-secondary-subtle text-secondary"}">
                        ${active ? "Active" : "Inactive"}
                    </span>
                </td>

                <td>
                    ${escapeHTML(department.created_at || "-")}
                </td>

                <td class="text-end">
                    <div class="btn-group btn-group-sm">

                        <button
                            class="btn btn-outline-info"
                            data-action="sections"
                            data-id="${Number(department.id)}"
                            title="View sections"
                        >
                            <i class="bi bi-eye"></i>
                        </button>

                        <button
                            class="btn btn-outline-primary"
                            data-action="edit"
                            data-id="${Number(department.id)}"
                            title="Edit department"
                        >
                            <i class="bi bi-pencil"></i>
                        </button>

                        <button
                            class="btn btn-outline-${active ? "danger" : "success"}"
                            data-action="${active ? "deactivate" : "activate"}"
                            data-id="${Number(department.id)}"
                            title="${active ? "Deactivate" : "Activate"} department"
                        >
                            <i class="bi bi-${active ? "toggle-off" : "toggle-on"}"></i>
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

function openCreateModal() {
  document.getElementById("department-form").reset();

  document.getElementById("department-id").value = "";
  document.getElementById("department-active").checked = true;
  document.getElementById("department-modal-title").textContent =
    "Add Department";
  document.getElementById("save-department-btn").textContent =
    "Save Department";
  document.getElementById("department-form-error").textContent = "";
}

function openEditModal(department) {
  document.getElementById("department-id").value = department.id;
  document.getElementById("department-name").value = department.name;
  document.getElementById("department-code").value = department.code;
  document.getElementById("department-active").checked = isActive(
    department.is_active,
  );

  document.getElementById("department-modal-title").textContent =
    "Edit Department";
  document.getElementById("save-department-btn").textContent =
    "Update Department";
  document.getElementById("department-form-error").textContent = "";

  bootstrap.Modal.getOrCreateInstance(
    document.getElementById("department-modal"),
  ).show();
}

async function saveDepartment(modal) {
  const id = document.getElementById("department-id").value;

  const payload = {
    name: document.getElementById("department-name").value.trim(),
    code: document.getElementById("department-code").value.trim().toUpperCase(),
    is_active: document.getElementById("department-active").checked,
  };

  const errorElement = document.getElementById("department-form-error");
  const saveButton = document.getElementById("save-department-btn");

  if (!payload.name || !payload.code) {
    errorElement.textContent = "Name and code are required.";
    return;
  }

  saveButton.disabled = true;
  saveButton.textContent = "Saving...";

  try {
    if (id) {
      await api.put(`/departments/${id}`, payload);
      showAlert("Department updated successfully.", "success");
    } else {
      await api.post("/departments", payload);
      showAlert("Department created successfully.", "success");
    }

    modal.hide();
    await loadDepartments();
  } catch (error) {
    errorElement.textContent = error.message;
  } finally {
    saveButton.disabled = false;
    saveButton.textContent = id ? "Update Department" : "Save Department";
  }
}

async function handleAction(action, id) {
  const department = departments.find((item) => Number(item.id) === id);

  if (!department) return;

  if (action === "edit") {
    try {
      const latest = await api.get(`/departments/${id}`);
      openEditModal(latest);
    } catch (error) {
      showAlert(error.message, "danger");
    }
    return;
  }

  if (action === "deactivate") {
    if (!confirm(`Deactivate "${department.name}"?`)) return;

    try {
      await api.delete(`/departments/${id}`);
      showAlert("Department deactivated successfully.", "success");
      await loadDepartments();
    } catch (error) {
      showAlert(error.message, "danger");
    }

    return;
  }

  if (action === "activate") {
    if (!confirm(`Activate "${department.name}"?`)) return;

    try {
      await api.put(`/departments/${id}`, {
        is_active: true,
      });

      showAlert("Department activated successfully.", "success");
      await loadDepartments();
    } catch (error) {
      showAlert(error.message, "danger");
    }

    return;
  }

  if (action === "sections") {
    await loadDepartmentSections(id);
  }
}

async function loadDepartmentSections(id) {
  const department = departments.find((item) => Number(item.id) === id);

  const content = document.getElementById("department-sections-content");

  content.innerHTML = `
        <div class="text-center py-4">
            <div class="spinner-border spinner-border-sm"></div>
            Loading sections...
        </div>
    `;

  bootstrap.Modal.getOrCreateInstance(
    document.getElementById("department-sections-modal"),
  ).show();

  try {
    const sections = await api.get(`/departments/${id}/sections`);

    if (!sections.length) {
      content.innerHTML = `
                <div class="alert alert-info mb-0">
                    No sections found for ${escapeHTML(department.name)}.
                </div>
            `;
      return;
    }

    content.innerHTML = `
            <h6 class="mb-3">${escapeHTML(department.name)}</h6>

            <div class="table-responsive">
                <table class="table table-bordered">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Section</th>
                            <th>Academic Year</th>
                            <th>Semester</th>
                            <th>Status</th>
                        </tr>
                    </thead>

                    <tbody>
                        ${sections
                          .map(
                            (section) => `
                            <tr>
                                <td>${escapeHTML(section.id)}</td>
                                <td>${escapeHTML(section.name)}</td>
                                <td>${escapeHTML(section.academic_year)}</td>
                                <td>${escapeHTML(section.semester)}</td>
                                <td>
                                    ${isActive(section.is_active) ? "Active" : "Inactive"}
                                </td>
                            </tr>
                        `,
                          )
                          .join("")}
                    </tbody>
                </table>
            </div>
        `;
  } catch (error) {
    content.innerHTML = `
            <div class="alert alert-danger">
                ${escapeHTML(error.message)}
            </div>
        `;
  }
}

function showAlert(message, type = "success") {
  const container = document.getElementById("department-alert");

  if (!container) return;

  container.innerHTML = `
        <div class="alert alert-${type} alert-dismissible fade show">
            ${escapeHTML(message)}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;

  window.setTimeout(() => {
    const alert = container.querySelector(".alert");

    if (alert) {
      bootstrap.Alert.getOrCreateInstance(alert).close();
    }
  }, 4000);
}

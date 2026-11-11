import { api } from "../api.js";

export async function renderDesignations(container) {
  let designations = [];
  let editingId = null;

  container.innerHTML = `
        <div class="d-flex justify-content-between align-items-center flex-wrap gap-3 mb-4">
            <div>
                <h3 class="mb-1">Designations</h3>
                <p class="text-muted mb-0">
                    Manage teacher designations and workload policies.
                </p>
            </div>
            <button class="btn btn-primary" id="add-designation-btn">
                <i class="bi bi-plus-lg me-1"></i> Add Designation
            </button>
        </div>

        <div id="designation-alert"></div>

        <div class="row g-3 mb-4">
            <div class="col-md-4">
                <div class="card border-0 shadow-sm">
                    <div class="card-body">
                        <p class="text-muted mb-1">Total Designations</p>
                        <h3 id="total-designations" class="mb-0">0</h3>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card border-0 shadow-sm">
                    <div class="card-body">
                        <p class="text-muted mb-1">Active Designations</p>
                        <h3 id="active-designations" class="mb-0">0</h3>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card border-0 shadow-sm">
                    <div class="card-body">
                        <p class="text-muted mb-1">Inactive Designations</p>
                        <h3 id="inactive-designations" class="mb-0">0</h3>
                    </div>
                </div>
            </div>
        </div>

        <div class="card border-0 shadow-sm">
            <div class="card-body">
                <div class="row g-3 mb-3">
                    <div class="col-md-8">
                        <input
                            type="search"
                            class="form-control"
                            id="designation-search"
                            placeholder="Search designation..."
                        >
                    </div>
                    <div class="col-md-4">
                        <select class="form-select" id="designation-status-filter">
                            <option value="all">All Designations</option>
                            <option value="active">Active Only</option>
                            <option value="inactive">Inactive Only</option>
                        </select>
                    </div>
                </div>

                <div class="table-responsive">
                    <table class="table table-hover align-middle">
                        <thead class="table-light">
                            <tr>
                                <th>#</th>
                                <th>Designation</th>
                                <th>Standard Workload</th>
                                <th>Maximum Workload</th>
                                <th>Status</th>
                                <th>Created At</th>
                                <th class="text-end">Actions</th>
                            </tr>
                        </thead>
                        <tbody id="designations-table-body">
                            <tr>
                                <td colspan="7" class="text-center py-4">
                                    Loading designations...
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- Designation Modal -->
        <div class="modal fade" id="designation-modal" tabindex="-1"
             aria-hidden="true">
            <div class="modal-dialog">
                <div class="modal-content">
                    <form id="designation-form">
                        <div class="modal-header">
                            <h5 class="modal-title" id="designation-modal-title">
                                Add Designation
                            </h5>
                            <button type="button" class="btn-close"
                                    data-bs-dismiss="modal"
                                    aria-label="Close"></button>
                        </div>

                        <div class="modal-body">
                            <div id="designation-form-error"></div>

                            <div class="mb-3">
                                <label for="designation-name" class="form-label">
                                    Designation Name
                                </label>
                                <input
                                    type="text"
                                    class="form-control"
                                    id="designation-name"
                                    placeholder="e.g. Lecturer"
                                    required
                                    maxlength="100"
                                >
                            </div>

                            <div class="mb-3">
                                <label for="standard-workload" class="form-label">
                                    Standard Workload
                                </label>
                                <input
                                    type="number"
                                    class="form-control"
                                    id="standard-workload"
                                    min="0"
                                    step="1"
                                    required
                                >
                                <div class="form-text">
                                    Enter the standard workload value.
                                </div>
                            </div>

                            <div class="mb-3">
                                <label for="maximum-workload" class="form-label">
                                    Maximum Workload
                                </label>
                                <input
                                    type="number"
                                    class="form-control"
                                    id="maximum-workload"
                                    min="0"
                                    step="1"
                                    required
                                >
                            </div>

                            <div class="form-check">
                                <input
                                    class="form-check-input"
                                    type="checkbox"
                                    id="designation-is-active"
                                    checked
                                >
                                <label class="form-check-label"
                                       for="designation-is-active">
                                    Active
                                </label>
                            </div>
                        </div>

                        <div class="modal-footer">
                            <button type="button" class="btn btn-light"
                                    data-bs-dismiss="modal">
                                Cancel
                            </button>
                            <button type="submit" class="btn btn-primary"
                                    id="save-designation-btn">
                                Save Designation
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    `;

  const modalElement = container.querySelector("#designation-modal");
  const modal = new bootstrap.Modal(modalElement);

  const escapeHTML = (value) =>
    String(value ?? "").replace(
      /[&<>"']/g,
      (character) =>
        ({
          "&": "&amp;",
          "<": "&lt;",
          ">": "&gt;",
          '"': "&quot;",
          "'": "&#039;",
        })[character],
    );

  const isActive = (value) => value === true || value === 1 || value === "1";

  function showAlert(message, type = "success") {
    const alertContainer = container.querySelector("#designation-alert");

    alertContainer.innerHTML = `
            <div class="alert alert-${type} alert-dismissible fade show"
                 role="alert">
                ${escapeHTML(message)}
                <button type="button" class="btn-close"
                        data-bs-dismiss="alert"></button>
            </div>
        `;
  }

  function showFormError(message) {
    container.querySelector("#designation-form-error").innerHTML = `
            <div class="alert alert-danger py-2">
                ${escapeHTML(message)}
            </div>
        `;
  }

  function getErrorMessage(error) {
    return (
      error?.response?.data?.detail ||
      error?.detail ||
      error?.message ||
      "Something went wrong. Please try again."
    );
  }

  function updateSummary() {
    const activeCount = designations.filter((item) =>
      isActive(item.is_active),
    ).length;

    container.querySelector("#total-designations").textContent =
      designations.length;

    container.querySelector("#active-designations").textContent = activeCount;

    container.querySelector("#inactive-designations").textContent =
      designations.length - activeCount;
  }

  function renderTable() {
    const search = container
      .querySelector("#designation-search")
      .value.toLowerCase()
      .trim();

    const status = container.querySelector("#designation-status-filter").value;

    const filtered = designations.filter((item) => {
      const matchesSearch = item.name.toLowerCase().includes(search);
      const active = isActive(item.is_active);

      const matchesStatus =
        status === "all" ||
        (status === "active" && active) ||
        (status === "inactive" && !active);

      return matchesSearch && matchesStatus;
    });

    const tbody = container.querySelector("#designations-table-body");

    if (!filtered.length) {
      tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="text-center text-muted py-4">
                        No designations found.
                    </td>
                </tr>
            `;
      return;
    }

    tbody.innerHTML = filtered
      .map((item, index) => {
        const active = isActive(item.is_active);

        return `
                <tr>
                    <td>${index + 1}</td>
                    <td class="fw-semibold">${escapeHTML(item.name)}</td>
                    <td>${item.standard_workload}</td>
                    <td>${item.maximum_workload}</td>
                    <td>
                        <span class="badge ${active ? "bg-success" : "bg-secondary"}">
                            ${active ? "Active" : "Inactive"}
                        </span>
                    </td>
                    <td>${
                      item.created_at ? escapeHTML(item.created_at) : "—"
                    }</td>
                    <td class="text-end">
                        <button class="btn btn-sm btn-outline-primary"
                                data-action="edit"
                                data-id="${item.id}"
                                title="Edit">
                            <i class="bi bi-pencil"></i>
                        </button>

                        ${
                          active
                            ? `
                                <button class="btn btn-sm btn-outline-danger"
                                        data-action="deactivate"
                                        data-id="${item.id}"
                                        title="Deactivate">
                                    <i class="bi bi-toggle-off"></i>
                                </button>
                            `
                            : `
                                <button class="btn btn-sm btn-outline-success"
                                        data-action="activate"
                                        data-id="${item.id}"
                                        title="Activate">
                                    <i class="bi bi-toggle-on"></i>
                                </button>
                            `
                        }
                    </td>
                </tr>
            `;
      })
      .join("");
  }

  async function loadDesignations() {
    try {
      designations = await api.get("/designations");
      updateSummary();
      renderTable();
    } catch (error) {
      showAlert(getErrorMessage(error), "danger");
      container.querySelector("#designations-table-body").innerHTML = `
                <tr>
                    <td colspan="7" class="text-center text-danger py-4">
                        Unable to load designations.
                    </td>
                </tr>
            `;
    }
  }

  function openCreateModal() {
    editingId = null;

    container.querySelector("#designation-form").reset();
    container.querySelector("#designation-is-active").checked = true;
    container.querySelector("#designation-modal-title").textContent =
      "Add Designation";
    container.querySelector("#save-designation-btn").textContent =
      "Save Designation";
    container.querySelector("#designation-form-error").innerHTML = "";

    modal.show();
  }

  async function openEditModal(id) {
    try {
      const item = await api.get(`/designations/${id}`);

      editingId = id;

      container.querySelector("#designation-name").value = item.name;
      container.querySelector("#standard-workload").value =
        item.standard_workload;
      container.querySelector("#maximum-workload").value =
        item.maximum_workload;
      container.querySelector("#designation-is-active").checked = isActive(
        item.is_active,
      );

      container.querySelector("#designation-modal-title").textContent =
        "Edit Designation";
      container.querySelector("#save-designation-btn").textContent =
        "Update Designation";
      container.querySelector("#designation-form-error").innerHTML = "";

      modal.show();
    } catch (error) {
      showAlert(getErrorMessage(error), "danger");
    }
  }

  container
    .querySelector("#add-designation-btn")
    .addEventListener("click", openCreateModal);

  container
    .querySelector("#designation-search")
    .addEventListener("input", renderTable);

  container
    .querySelector("#designation-status-filter")
    .addEventListener("change", renderTable);

  container
    .querySelector("#designations-table-body")
    .addEventListener("click", async (event) => {
      const button = event.target.closest("button[data-action]");
      if (!button) return;

      const id = Number(button.dataset.id);
      const action = button.dataset.action;

      if (action === "edit") {
        await openEditModal(id);
        return;
      }

      const item = designations.find((row) => row.id === id);
      if (!item) return;

      if (action === "deactivate") {
        const confirmed = window.confirm(`Deactivate "${item.name}"?`);
        if (!confirmed) return;

        try {
          await api.delete(`/designations/${id}`);
          showAlert("Designation deactivated successfully.");
          await loadDesignations();
        } catch (error) {
          showAlert(getErrorMessage(error), "danger");
        }
      }

      if (action === "activate") {
        try {
          await api.put(`/designations/${id}`, {
            is_active: true,
          });

          showAlert("Designation activated successfully.");
          await loadDesignations();
        } catch (error) {
          showAlert(getErrorMessage(error), "danger");
        }
      }
    });

  container
    .querySelector("#designation-form")
    .addEventListener("submit", async (event) => {
      event.preventDefault();

      const name = container.querySelector("#designation-name").value.trim();

      const standardWorkload = Number(
        container.querySelector("#standard-workload").value,
      );

      const maximumWorkload = Number(
        container.querySelector("#maximum-workload").value,
      );

      const isActiveValue = container.querySelector(
        "#designation-is-active",
      ).checked;

      if (!name) {
        showFormError("Designation name is required.");
        return;
      }

      if (!Number.isInteger(standardWorkload) || standardWorkload < 0) {
        showFormError("Standard workload must be a non-negative integer.");
        return;
      }

      if (!Number.isInteger(maximumWorkload) || maximumWorkload < 0) {
        showFormError("Maximum workload must be a non-negative integer.");
        return;
      }

      if (maximumWorkload < standardWorkload) {
        showFormError(
          "Maximum workload cannot be less than standard workload.",
        );
        return;
      }

      const payload = {
        name,
        standard_workload: standardWorkload,
        maximum_workload: maximumWorkload,
        is_active: isActiveValue,
      };

      const saveButton = container.querySelector("#save-designation-btn");

      saveButton.disabled = true;
      saveButton.textContent = "Saving...";

      try {
        if (editingId) {
          await api.put(`/designations/${editingId}`, payload);
          showAlert("Designation updated successfully.");
        } else {
          await api.post("/designations", payload);
          showAlert("Designation created successfully.");
        }

        modal.hide();
        await loadDesignations();
      } catch (error) {
        showFormError(getErrorMessage(error));
      } finally {
        saveButton.disabled = false;
        saveButton.textContent = editingId
          ? "Update Designation"
          : "Save Designation";
      }
    });

  await loadDesignations();
}

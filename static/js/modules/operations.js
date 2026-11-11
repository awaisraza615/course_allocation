import { api } from "../api.js";

const escapeHTML = (value) =>
  String(value ?? "").replace(
    /[&<>"']/g,
    (character) =>
      ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
      })[character],
  );

const active = (value) => value === true || value === 1 || value === "1";
const options = (records, valueKey, label) =>
  records
    .map(
      (record) =>
        `<option value="${escapeHTML(record[valueKey])}">${escapeHTML(label(record))}</option>`,
    )
    .join("");

function showError(container, error) {
  const alert = container.querySelector("[data-alert]");
  if (alert) {
    alert.innerHTML = `<div class="alert alert-danger" role="alert">${escapeHTML(error.message)}</div>`;
  }
}

function showSuccess(container, message) {
  const alert = container.querySelector("[data-alert]");
  if (alert) {
    alert.innerHTML = `<div class="alert alert-success" role="status">${escapeHTML(message)}</div>`;
  }
}

function table(headers, rows, emptyMessage = "No records found.") {
  return `
    <div class="table-responsive">
      <table class="table table-hover align-middle">
        <thead class="table-light"><tr>${headers.map((header) => `<th>${header}</th>`).join("")}</tr></thead>
        <tbody>
          ${
            rows.length
              ? rows.join("")
              : `<tr><td class="text-center text-muted py-4" colspan="${headers.length}">${escapeHTML(emptyMessage)}</td></tr>`
          }
        </tbody>
      </table>
    </div>`;
}

function pageHeader(title, description, content) {
  return `
    <div class="mb-4">
      <h3 class="mb-1">${title}</h3>
      <p class="text-muted mb-0">${description}</p>
    </div>
    <div data-alert></div>
    ${content}`;
}

export async function renderTeachers(container) {
  const [teachers, departments, designations] = await Promise.all([
    api.get("/teachers"),
    api.get("/departments"),
    api.get("/designations"),
  ]);
  const activeDepartments = departments.filter((item) => active(item.is_active));
  const activeDesignations = designations.filter((item) => active(item.is_active));
  let editingTeacher = null;

  container.innerHTML = pageHeader(
    "Teachers",
    "Register teachers and maintain their department and designation.",
    `
      <div class="row g-4">
        <div class="col-xl-4">
          <div class="card border-0 shadow-sm"><div class="card-body">
            <h5 class="mb-3" id="teacher-form-title">Add Teacher</h5>
            <form id="teacher-form">
              <div class="mb-3"><label class="form-label" for="teacher-name">Full name</label>
                <input class="form-control" id="teacher-name" required maxlength="150"></div>
              <div class="mb-3"><label class="form-label" for="teacher-code">Employee code (optional)</label>
                <input class="form-control" id="teacher-code" maxlength="50"></div>
              <div class="mb-3"><label class="form-label" for="teacher-department">Department</label>
                <select class="form-select" id="teacher-department" required>
                  <option value="">Select department</option>
                  ${options(activeDepartments, "id", (item) => `${item.name} (${item.code})`)}
                </select></div>
              <div class="mb-3"><label class="form-label" for="teacher-designation">Designation</label>
                <select class="form-select" id="teacher-designation" required>
                  <option value="">Select designation</option>
                  ${options(activeDesignations, "id", (item) => item.name)}
                </select></div>
              <button class="btn btn-primary" type="submit" id="teacher-save">Add Teacher</button>
              <button class="btn btn-light" type="button" id="teacher-cancel" hidden>Cancel edit</button>
            </form>
          </div></div>
        </div>
        <div class="col-xl-8"><div class="card border-0 shadow-sm"><div class="card-body">
          <h5 class="mb-3">Teacher Directory</h5>
          ${table(
            ["Sr. No.", "Name", "Employee Code", "Department", "Designation", "Status", "Actions"],
            teachers.map(
              (teacher, index) => `<tr>
                <td>${index + 1}</td>
                <td>${escapeHTML(teacher.full_name)}</td>
                <td>${escapeHTML(teacher.employee_code || "—")}</td>
                <td>${escapeHTML(teacher.department_name)}</td>
                <td>${escapeHTML(teacher.designation_name)}</td>
                <td>${active(teacher.is_active) ? "Active" : "Inactive"}</td>
                <td>${
                  active(teacher.is_active)
                    ? `<button class="btn btn-sm btn-outline-primary me-1" data-edit-teacher="${teacher.id}">Edit</button><button class="btn btn-sm btn-outline-danger" data-deactivate-teacher="${teacher.id}">Deactivate</button>`
                    : "—"
                }</td>
              </tr>`,
            ),
          )}
        </div></div></div>
      </div>`,
  );

  container.querySelector("#teacher-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      const payload = {
        full_name: container.querySelector("#teacher-name").value.trim(),
        employee_code: container.querySelector("#teacher-code").value.trim() || null,
        department_id: Number(container.querySelector("#teacher-department").value),
        designation_id: Number(container.querySelector("#teacher-designation").value),
      };
      if (editingTeacher) {
        await api.put(`/teachers/${editingTeacher}`, payload);
      } else {
        await api.post("/teachers", payload);
      }
      const wasEditing = Boolean(editingTeacher);
      editingTeacher = null;
      await renderTeachers(container);
      showSuccess(container, wasEditing ? "Teacher updated." : "Teacher created.");
    } catch (error) {
      showError(container, error);
    }
  });
  container.querySelectorAll("[data-edit-teacher]").forEach((button) => {
    button.addEventListener("click", () => {
      const teacher = teachers.find((item) => item.id === Number(button.dataset.editTeacher));
      if (!teacher) return;
      editingTeacher = teacher.id;
      container.querySelector("#teacher-name").value = teacher.full_name;
      container.querySelector("#teacher-code").value = teacher.employee_code || "";
      container.querySelector("#teacher-department").value = teacher.department_id;
      container.querySelector("#teacher-designation").value = teacher.designation_id;
      container.querySelector("#teacher-form-title").textContent = "Edit Teacher";
      container.querySelector("#teacher-save").textContent = "Save Changes";
      container.querySelector("#teacher-cancel").hidden = false;
      container.querySelector("#teacher-form").scrollIntoView({ behavior: "smooth" });
    });
  });
  container.querySelector("#teacher-cancel").addEventListener("click", () => {
    renderTeachers(container);
  });
  container.querySelectorAll("[data-deactivate-teacher]").forEach((button) => {
    button.addEventListener("click", async () => {
      try {
        await api.delete(`/teachers/${button.dataset.deactivateTeacher}`);
        await renderTeachers(container);
        showSuccess(container, "Teacher deactivated.");
      } catch (error) {
        showError(container, error);
      }
    });
  });
}

export async function renderCourses(container) {
  const [courses, departments] = await Promise.all([
    api.get("/courses"),
    api.get("/departments"),
  ]);
  const activeDepartments = departments.filter((item) => active(item.is_active));
  let editingCourse = null;

  container.innerHTML = pageHeader(
    "Courses",
    "Create a course and associate it with one or more departments.",
    `
      <div class="row g-4">
        <div class="col-xl-4">
          <div class="card border-0 shadow-sm"><div class="card-body">
            <h5 class="mb-3" id="course-form-title">Add Course</h5>
            <form id="course-form">
              <div class="mb-3"><label class="form-label" for="course-code">Course code</label>
                <input class="form-control" id="course-code" required maxlength="30"></div>
              <div class="mb-3"><label class="form-label" for="course-name">Course name</label>
                <input class="form-control" id="course-name" required maxlength="200"></div>
              <div class="row">
                <div class="col-6 mb-3"><label class="form-label" for="course-theory">Theory hours</label>
                  <select class="form-select" id="course-theory" required>
                    <option value="3">3</option><option value="2">2</option>
                  </select></div>
                <div class="col-6 mb-3"><label class="form-label" for="course-lab">Lab hours</label>
                  <select class="form-select" id="course-lab" required>
                    <option value="1">1</option><option value="0">0</option>
                  </select></div>
              </div>
              <div class="mb-3">
                <label class="form-label" for="course-departments">Departments</label>
                <select class="form-select" id="course-departments" multiple required size="5">
                  ${options(activeDepartments, "id", (item) => `${item.name} (${item.code})`)}
                </select>
                <div class="form-text">Use Ctrl (Windows/Linux) or Command (Mac) to select multiple departments.</div>
              </div>
              <button class="btn btn-primary" type="submit" id="course-save">Add Course</button>
              <button class="btn btn-light" type="button" id="course-cancel" hidden>Cancel edit</button>
            </form>
          </div></div>
        </div>
        <div class="col-xl-8"><div class="card border-0 shadow-sm"><div class="card-body">
          <h5 class="mb-3">Course Catalog</h5>
          ${table(
            ["Sr. No.", "Code", "Course", "Hours", "Departments", "Status", "Actions"],
            courses.map(
              (course, index) => `<tr>
                <td>${index + 1}</td>
                <td>${escapeHTML(course.course_code)}</td>
                <td>${escapeHTML(course.course_name)}</td>
                <td>${course.theory_hours}+${course.laboratory_hours}</td>
                <td>${escapeHTML((course.departments || []).map((department) => department.code).join(", "))}</td>
                <td>${active(course.is_active) ? "Active" : "Inactive"}</td>
                <td>${
                  active(course.is_active)
                    ? `<button class="btn btn-sm btn-outline-primary me-1" data-edit-course="${course.id}">Edit</button><button class="btn btn-sm btn-outline-danger" data-deactivate-course="${course.id}">Deactivate</button>`
                    : "—"
                }</td>
              </tr>`,
            ),
          )}
        </div></div></div>
      </div>`,
  );

  const theory = container.querySelector("#course-theory");
  const lab = container.querySelector("#course-lab");

  container.querySelector("#course-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const selectedDepartments = [
      ...container.querySelector("#course-departments").selectedOptions,
    ].map((option) => Number(option.value));
    try {
      const payload = {
        course_code: container.querySelector("#course-code").value.trim(),
        course_name: container.querySelector("#course-name").value.trim(),
        theory_hours: Number(theory.value),
        laboratory_hours: Number(lab.value),
        department_ids: selectedDepartments,
      };
      if (editingCourse) {
        await api.put(`/courses/${editingCourse}`, payload);
      } else {
        await api.post("/courses", payload);
      }
      const wasEditing = Boolean(editingCourse);
      editingCourse = null;
      await renderCourses(container);
      showSuccess(
        container,
        wasEditing
          ? "Course updated."
          : "Course created and associated with the selected departments.",
      );
    } catch (error) {
      showError(container, error);
    }
  });
  container.querySelectorAll("[data-edit-course]").forEach((button) => {
    button.addEventListener("click", () => {
      const course = courses.find((item) => item.id === Number(button.dataset.editCourse));
      if (!course) return;
      editingCourse = course.id;
      container.querySelector("#course-code").value = course.course_code;
      container.querySelector("#course-name").value = course.course_name;
      theory.value = String(course.theory_hours);
      lab.value = String(course.laboratory_hours);
      const departmentsSelect = container.querySelector("#course-departments");
      [...departmentsSelect.options].forEach((option) => {
        option.selected = course.department_ids.includes(Number(option.value));
      });
      container.querySelector("#course-form-title").textContent = "Edit Course";
      container.querySelector("#course-save").textContent = "Save Changes";
      container.querySelector("#course-cancel").hidden = false;
      container.querySelector("#course-form").scrollIntoView({ behavior: "smooth" });
    });
  });
  container.querySelector("#course-cancel").addEventListener("click", () => {
    renderCourses(container);
  });
  container.querySelectorAll("[data-deactivate-course]").forEach((button) => {
    button.addEventListener("click", async () => {
      try {
        await api.delete(`/courses/${button.dataset.deactivateCourse}`);
        await renderCourses(container);
        showSuccess(container, "Course deactivated.");
      } catch (error) {
        showError(container, error);
      }
    });
  });
}

export async function renderPreferences(container) {
  const [teachers, courses] = await Promise.all([api.get("/teachers"), api.get("/courses")]);
  const activeTeachers = teachers.filter((teacher) => active(teacher.is_active));
  const activeCourses = courses.filter((course) => active(course.is_active));
  container.innerHTML = pageHeader(
    "Teacher Preferences",
    "Rank teachers' course interests and see all teachers interested in a course.",
    `
      <div class="row g-4">
        <div class="col-lg-5"><div class="card border-0 shadow-sm"><div class="card-body">
          <h5 class="mb-3">Add Preference</h5>
          <form id="preference-form">
            <div class="mb-3"><label class="form-label" for="preference-teacher">Teacher</label>
              <select class="form-select" id="preference-teacher" required>
                <option value="">Select teacher</option>
                ${options(activeTeachers, "id", (teacher) => teacher.full_name)}
              </select></div>
            <div class="mb-3"><label class="form-label" for="preference-course">Course</label>
              <select class="form-select" id="preference-course" required>
                <option value="">Select course</option>
                ${options(activeCourses, "id", (course) => `${course.course_code} — ${course.course_name}`)}
              </select></div>
            <div class="mb-3"><label class="form-label" for="preference-priority">Priority</label>
              <input class="form-control" id="preference-priority" type="number" min="1" step="1" placeholder="Leave blank to add last"></div>
            <button class="btn btn-primary" type="submit">Add Preference</button>
          </form>
        </div></div></div>
        <div class="col-lg-7"><div class="card border-0 shadow-sm"><div class="card-body">
          <h5 class="mb-3">Interested Teachers</h5>
          <div class="input-group mb-3">
            <select class="form-select" id="interested-course">
              <option value="">Select a course</option>
              ${options(activeCourses, "id", (course) => `${course.course_code} — ${course.course_name}`)}
            </select>
            <button class="btn btn-outline-primary" id="load-interested" type="button">View</button>
          </div>
          <div id="interested-list" class="text-muted">Choose a course to see interested teachers.</div>
        </div></div></div>
      </div>
      <div class="card border-0 shadow-sm mt-4"><div class="card-body">
        <h5 class="mb-3">Teacher Preferences</h5>
        <div class="input-group mb-3">
          <select class="form-select" id="preferences-teacher">
            <option value="">Select a teacher</option>
            ${options(activeTeachers, "id", (teacher) => teacher.full_name)}
          </select>
          <button class="btn btn-outline-primary" id="load-preferences" type="button">View</button>
        </div>
        <div id="teacher-preference-list"></div>
      </div></div>`,
  );

  container.querySelector("#preference-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const teacherId = container.querySelector("#preference-teacher").value;
    try {
      const preference = {
          course_id: Number(container.querySelector("#preference-course").value),
      };
      const priority = container.querySelector("#preference-priority").value;
      if (priority) preference.priority = Number(priority);
      await api.post(`/teachers/${teacherId}/preferences`, { preferences: [preference] });
      showSuccess(container, "Preference added.");
      container.querySelector("#load-preferences").click();
    } catch (error) {
      showError(container, error);
    }
  });

  container.querySelector("#load-interested").addEventListener("click", async () => {
    const courseId = container.querySelector("#interested-course").value;
    if (!courseId) return;
    try {
      const interested = await api.get(`/courses/${courseId}/interested-teachers`);
      container.querySelector("#interested-list").innerHTML = table(
        ["Teacher", "Department", "Designation", "Priority"],
        interested.map((item) => `<tr><td>${escapeHTML(item.full_name)}</td>
          <td>${escapeHTML(item.department_name)}</td>
          <td>${escapeHTML(item.designation_name)}</td><td>${item.priority}</td></tr>`),
      );
    } catch (error) {
      showError(container, error);
    }
  });

  container.querySelector("#load-preferences").addEventListener("click", async () => {
    const teacherId = container.querySelector("#preferences-teacher").value;
    if (!teacherId) return;
    try {
      const preferences = await api.get(`/teachers/${teacherId}/preferences`);
      container.querySelector("#teacher-preference-list").innerHTML = table(
        ["Course", "Priority", "Change Priority", "Action"],
        preferences.map((item) => `<tr>
          <td>${escapeHTML(item.course_code)} — ${escapeHTML(item.course_name)}</td>
          <td>${item.priority}</td>
          <td><input class="form-control form-control-sm" type="number" min="1" value="${item.priority}" id="priority-${item.id}"></td>
          <td class="text-nowrap">
            <button class="btn btn-sm btn-outline-primary me-1" data-priority-id="${item.id}">Save</button>
            <button class="btn btn-sm btn-outline-danger" data-delete-preference="${item.id}">Remove</button>
          </td></tr>`),
      );
      container.querySelectorAll("[data-priority-id]").forEach((button) => {
        button.addEventListener("click", async () => {
          try {
            await api.put(`/preferences/${button.dataset.priorityId}`, {
              priority: Number(container.querySelector(`#priority-${button.dataset.priorityId}`).value),
            });
            container.querySelector("#load-preferences").click();
          } catch (error) {
            showError(container, error);
          }
        });
      });
      container.querySelectorAll("[data-delete-preference]").forEach((button) => {
        button.addEventListener("click", async () => {
          try {
            await api.delete(`/preferences/${button.dataset.deletePreference}`);
            container.querySelector("#load-preferences").click();
          } catch (error) {
            showError(container, error);
          }
        });
      });
    } catch (error) {
      showError(container, error);
    }
  });
}

export async function renderOfferings(container) {
  const [offerings, courses, sections, terms] = await Promise.all([
    api.get("/offerings"),
    api.get("/courses?is_active=true"),
    api.get("/sections"),
    api.get("/academic-terms"),
  ]);
  const availableCourses = courses.filter((course) => active(course.is_active));
  const termById = new Map(terms.map((term) => [Number(term.id), term]));
  let eligibleSections = [];
  const selectedSectionIds = new Set();
  container.innerHTML = pageHeader(
    "Course Offerings",
    "Create offerings for sections in any active or inactive academic term.",
    `
      <div class="card border-0 shadow-sm mb-4"><div class="card-body">
        <h5 class="mb-3">Create Offering</h5>
        <form id="offering-form" class="row g-3">
          <div class="col-12"><label class="form-label" for="offering-course">Course</label>
            <select class="form-select" id="offering-course" required>
              <option value="">Select course</option>
              ${options(availableCourses, "id", (course) => `${course.course_code} — ${course.course_name}`)}
            </select>
            <div class="form-text" id="offering-course-departments">Select a course to see its eligible departments and sections.</div>
          </div>
          <div class="col-12" id="offering-section-picker" hidden>
            <div class="d-flex justify-content-between align-items-center gap-2 flex-wrap mb-2">
              <label class="form-label mb-0" for="offering-section-search">Sections</label>
              <span class="small text-muted" id="offering-selected-count">0 selected</span>
            </div>
            <div class="row g-2 mb-2">
              <div class="col-md-7">
                <input class="form-control" id="offering-section-search" type="search" placeholder="Search section or department" aria-label="Search sections">
              </div>
              <div class="col-md-5">
                <select class="form-select" id="offering-section-term" aria-label="Filter sections by term">
                  <option value="">All terms</option>
                  ${options(terms, "id", (term) => `${term.name} (${term.semester}) — ${active(term.is_active) ? "Active" : "Inactive"}`)}
                </select>
              </div>
            </div>
            <div class="d-flex gap-2 mb-2">
              <button class="btn btn-sm btn-outline-secondary" id="offering-select-visible" type="button">Select visible</button>
              <button class="btn btn-sm btn-outline-secondary" id="offering-clear-selection" type="button">Clear selection</button>
            </div>
            <div class="border rounded p-2" id="offering-section-list" style="max-height: 18rem; overflow-y: auto;" aria-live="polite"></div>
          </div>
          <div class="col-12">
            <button class="btn btn-primary" id="offering-submit" type="submit" disabled>Create offerings for selected sections</button>
          </div>
        </form>
      </div></div>
      <div class="card border-0 shadow-sm"><div class="card-body">
        <div class="d-flex justify-content-between align-items-center mb-3">
          <h5 class="mb-0">Offerings</h5>
          <select class="form-select w-auto" id="offering-term-filter">
            <option value="">All terms</option>
            ${options(terms, "id", (term) => `${term.name} (${term.semester}) — ${active(term.is_active) ? "Active" : "Inactive"}`)}
          </select>
        </div>
        <div id="offerings-table"></div>
      </div></div>`,
  );

  const courseSelect = container.querySelector("#offering-course");
  const sectionList = container.querySelector("#offering-section-list");
  const searchInput = container.querySelector("#offering-section-search");
  const termFilter = container.querySelector("#offering-section-term");
  const submitButton = container.querySelector("#offering-submit");

  const updateSelectedCount = () => {
    const count = selectedSectionIds.size;
    container.querySelector("#offering-selected-count").textContent =
      `${count} selected`;
    submitButton.disabled = count === 0;
  };

  const renderSectionChoices = () => {
    const keyword = searchInput.value.trim().toLowerCase();
    const selectedTerm = termFilter.value;
    const filtered = eligibleSections.filter((section) => {
      const matchesTerm =
        !selectedTerm || String(section.academic_term_id) === selectedTerm;
      const matchesSearch = [
        section.name,
        section.department_name,
        section.department_code,
        section.academic_term_name,
        section.semester,
      ].some((value) => String(value ?? "").toLowerCase().includes(keyword));
      return matchesTerm && matchesSearch;
    });

    if (!filtered.length) {
      sectionList.innerHTML =
        '<p class="text-muted small mb-0">No eligible sections match these filters.</p>';
      updateSelectedCount();
      return;
    }

    sectionList.innerHTML = filtered
      .map((section) => {
        const id = Number(section.id);
        const term = termById.get(Number(section.academic_term_id));
        const termStatus = term && active(term.is_active) ? "Active" : "Inactive";
        const checked = selectedSectionIds.has(id) ? "checked" : "";
        return `
            <label class="d-flex align-items-start gap-2 border-bottom py-2 px-1 mb-0">
              <input class="form-check-input mt-1" type="checkbox" value="${id}" data-offering-section ${checked}>
              <span>
                <span class="fw-semibold">${escapeHTML(section.department_name)} (${escapeHTML(section.department_code)}) — ${escapeHTML(section.name)}</span>
                <span class="d-block small text-muted">${escapeHTML(section.academic_term_name)} (${escapeHTML(section.semester)}) · ${termStatus}</span>
              </span>
            </label>`;
        })
        .join("");

      sectionList.querySelectorAll("[data-offering-section]").forEach((checkbox) => {
        checkbox.addEventListener("change", () => {
          const sectionId = Number(checkbox.value);
          if (checkbox.checked) {
            selectedSectionIds.add(sectionId);
          } else {
            selectedSectionIds.delete(sectionId);
          }
          updateSelectedCount();
        });
      });
      updateSelectedCount();
  };

  courseSelect.addEventListener("change", () => {
      const course = availableCourses.find(
        (item) => Number(item.id) === Number(courseSelect.value),
      );
      selectedSectionIds.clear();
      if (!course) {
        eligibleSections = [];
        container.querySelector("#offering-section-picker").hidden = true;
        container.querySelector("#offering-course-departments").textContent =
          "Select a course to see its eligible departments and sections.";
        updateSelectedCount();
        return;
      }

      const departments = course.departments || [];
      const departmentIds = new Set(
        (
          departments.length
            ? departments.map((department) => department.id)
            : [course.department_id]
        ).map(Number),
      );
      const existingSectionIds = new Set(
        offerings
          .filter((offering) => Number(offering.course_id) === Number(course.id))
          .map((offering) => Number(offering.section_id)),
      );
      eligibleSections = sections.filter(
        (section) =>
          active(section.is_active) &&
          departmentIds.has(Number(section.department_id)) &&
          !existingSectionIds.has(Number(section.id)),
      );
      container.querySelector("#offering-section-picker").hidden = false;
      container.querySelector("#offering-course-departments").textContent =
        departments.length
          ? `Eligible departments: ${departments.map((department) => department.name || department.code).join(", ")}`
          : "Choose one or more eligible sections.";
      searchInput.value = "";
      termFilter.value = "";
      renderSectionChoices();
  });
  searchInput.addEventListener("input", renderSectionChoices);
  termFilter.addEventListener("change", renderSectionChoices);
  container.querySelector("#offering-select-visible").addEventListener("click", () => {
      sectionList.querySelectorAll("[data-offering-section]").forEach((checkbox) => {
        checkbox.checked = true;
        selectedSectionIds.add(Number(checkbox.value));
      });
      updateSelectedCount();
  });
  container.querySelector("#offering-clear-selection").addEventListener("click", () => {
      selectedSectionIds.clear();
      renderSectionChoices();
  });

  const renderOfferingTable = (selectedTerm = "") => {
    const filtered = selectedTerm
      ? offerings.filter((offering) => String(offering.academic_term_id) === selectedTerm)
      : offerings;
    container.querySelector("#offerings-table").innerHTML = table(
      ["Sr. No.", "Course", "Section", "Department", "Term", "Workload", "Status", "Action"],
      [...filtered]
        .sort((a, b) =>
          String(a.course_name ?? "").localeCompare(
            String(b.course_name ?? ""),
            undefined,
            { sensitivity: "base" },
          ),
        )
        .map((offering, index) => `<tr>
        <td>${index + 1}</td>
        <td>${escapeHTML(offering.course_code)} — ${escapeHTML(offering.course_name)}</td>
        <td>${escapeHTML(offering.section_name)}</td>
        <td>${escapeHTML(offering.department_name)}</td>
        <td>${escapeHTML(offering.academic_term)} (${active(termById.get(Number(offering.academic_term_id))?.is_active) ? "Active" : "Inactive"})</td>
        <td>${offering.workload_hours}</td>
        <td>${offering.allocation_id ? `Allocated to ${escapeHTML(offering.allocated_teacher_name)}` : "Pending"}</td>
        <td>${offering.allocation_id ? "—" : `<button class="btn btn-sm btn-outline-danger" data-remove-offering="${offering.id}">Remove</button>`}</td>
      </tr>`),
    );
    container.querySelectorAll("[data-remove-offering]").forEach((button) => {
      button.addEventListener("click", async () => {
        try {
          await api.delete(`/offerings/${button.dataset.removeOffering}`);
          await renderOfferings(container);
          showSuccess(container, "Pending offering removed.");
        } catch (error) {
          showError(container, error);
        }
      });
    });
  };
  renderOfferingTable();
  container.querySelector("#offering-term-filter").addEventListener("change", (event) => {
    renderOfferingTable(event.target.value);
  });
  container.querySelector("#offering-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const courseId = Number(courseSelect.value);
    const sectionIds = [...selectedSectionIds];
    if (!courseId || !sectionIds.length) {
      showError(container, new Error("Select a course and at least one section."));
      return;
    }

    submitButton.disabled = true;
    submitButton.textContent = "Creating offerings...";
    const created = [];
    const failures = [];
    try {
      for (const sectionId of sectionIds) {
        try {
          await api.post("/offerings", {
            course_id: courseId,
            section_id: sectionId,
          });
          created.push(sectionId);
        } catch (error) {
          const section = eligibleSections.find(
            (item) => Number(item.id) === sectionId,
          );
          failures.push(
            `${section?.department_code || ""} ${section?.name || sectionId}: ${error.message}`,
          );
        }
      }
      await renderOfferings(container);
      if (failures.length) {
        showError(
          container,
          new Error(
            `Created ${created.length} of ${sectionIds.length} offerings. Failed: ${failures.join("; ")}`,
          ),
        );
      } else {
        showSuccess(
          container,
          `Created ${created.length} offering${created.length === 1 ? "" : "s"}.`,
        );
      }
    } catch (error) {
      showError(container, error);
    } finally {
      if (submitButton.isConnected) {
        submitButton.disabled = false;
        submitButton.textContent = "Create offerings for selected sections";
      }
    }
  });
}

export async function renderWorkload(container) {
  const [teachers, allocations] = await Promise.all([
    api.get("/teachers"),
    api.get("/allocations"),
  ]);
  container.innerHTML = pageHeader(
    "Workload",
    "Review each teacher's assigned courses and combined workload across academic terms.",
    `
      <div class="card border-0 shadow-sm mb-4"><div class="card-body">
        <form id="workload-filter" class="row g-3 align-items-end">
          <div class="col-md-10"><label class="form-label" for="workload-teacher">Teacher</label>
            <select class="form-select" id="workload-teacher"><option value="">All teachers</option>
              ${options(teachers, "id", (teacher) => `${teacher.full_name}${active(teacher.is_active) ? "" : " (Inactive)"}`)}
            </select></div>
          <div class="col-md-2"><button class="btn btn-primary w-100" type="submit">View</button></div>
        </form>
      </div></div>
      <div class="card border-0 shadow-sm"><div class="card-body"><div id="workload-table"></div></div></div>`,
  );
  const workloadByTeacher = new Map(teachers.map((teacher) => [Number(teacher.id), 0]));
  allocations.forEach((allocation) => {
    const teacherId = Number(allocation.teacher_id);
    workloadByTeacher.set(
      teacherId,
      (workloadByTeacher.get(teacherId) ?? 0) + Number(allocation.workload_hours),
    );
  });

  const renderWorkloadTable = () => {
    const selectedTeacher = container.querySelector("#workload-teacher").value;
    const filteredTeachers = selectedTeacher
      ? teachers.filter((teacher) => String(teacher.id) === selectedTeacher)
      : teachers;
    const teacherRows = filteredTeachers.flatMap((teacher) => {
      const assignedCourses = allocations.filter(
        (allocation) => Number(allocation.teacher_id) === Number(teacher.id),
      );
      return (assignedCourses.length ? assignedCourses : [null]).map((allocation) => ({
        teacher,
        allocation,
      }));
    }).sort((a, b) =>
      a.teacher.full_name.localeCompare(b.teacher.full_name, undefined, { sensitivity: "base" })
      || String(a.allocation?.course_name ?? "").localeCompare(
        String(b.allocation?.course_name ?? ""),
        undefined,
        { sensitivity: "base" },
      )
      || String(a.allocation?.section_name ?? "").localeCompare(
        String(b.allocation?.section_name ?? ""),
        undefined,
        { sensitivity: "base" },
      ),
    );
    container.querySelector("#workload-table").innerHTML = table(
      ["Sr. No.", "Teacher", "Teacher Department", "Designation", "Course Code", "Course Name", "Assigned Department", "Section", "Course Workload", "Combined Workload"],
      teacherRows.map(({ teacher, allocation }, index) => `<tr>
        <td>${index + 1}</td><td>${escapeHTML(teacher.full_name)}</td>
        <td>${escapeHTML(teacher.department_name)}</td><td>${escapeHTML(teacher.designation_name)}</td>
        <td>${escapeHTML(allocation?.course_code ?? "—")}</td>
        <td>${escapeHTML(allocation?.course_name ?? "—")}</td>
        <td>${escapeHTML(allocation?.course_department ?? "—")}</td>
        <td>${escapeHTML(allocation?.section_name ?? "—")}</td>
        <td>${allocation?.workload_hours ?? "—"}</td>
        <td>${workloadByTeacher.get(Number(teacher.id))}</td>
      </tr>`),
      "No teachers found.",
    );
  };
  container.querySelector("#workload-filter").addEventListener("submit", (event) => {
    event.preventDefault();
    renderWorkloadTable();
  });
  renderWorkloadTable();
}

export async function renderAllocations(container) {
  const [terms, teachers, offerings, allocations] = await Promise.all([
    api.get("/academic-terms"),
    api.get("/teachers?is_active=true"),
    api.get("/offerings?pending_only=true"),
    api.get("/allocations"),
  ]);
  container.innerHTML = pageHeader(
    "Allocations",
    "Select any academic term, including inactive terms, to preview and run allocation. Run each term separately.",
    `
      <div class="card border-0 shadow-sm mb-4"><div class="card-body">
        <div class="row g-3 align-items-end mb-3">
          <div class="col-md-5"><label class="form-label" for="allocation-term">Academic term</label>
            <select class="form-select" id="allocation-term">
              <option value="">Select term</option>
              ${options(terms, "id", (term) => `${term.name} (${term.semester}) — ${active(term.is_active) ? "Active" : "Inactive"}`)}
            </select></div>
          <div class="col-md-7 d-flex gap-2">
            <button class="btn btn-outline-primary" id="preview-auto" type="button">Preview Automatic</button>
            <button class="btn btn-primary" id="execute-auto" type="button">Run Automatic Allocation</button>
          </div>
        </div>
        <p class="form-text">Automatic allocation assigns up to 12 workload hours per teacher. Remaining offerings stay unallocated for manual assignment; manual assignment can exceed the limit.</p>
        <div id="allocation-preview"></div>
      </div></div>
      <div class="card border-0 shadow-sm mb-4"><div class="card-body">
        <h5 class="mb-3">Manual Allocation</h5>
        <form id="manual-allocation-form" class="row g-3 align-items-end">
          <div class="col-md-5"><label class="form-label" for="manual-offering">Pending offering</label>
            <select class="form-select" id="manual-offering" required>
              <option value="">Select offering</option>
              ${options(offerings, "id", (item) => `${item.course_code} — ${item.section_name} (${item.academic_term}, ${active(terms.find((term) => Number(term.id) === Number(item.academic_term_id))?.is_active) ? "Active" : "Inactive"})`)}
            </select></div>
          <div class="col-md-4"><label class="form-label" for="manual-teacher">Teacher</label>
            <select class="form-select" id="manual-teacher" required>
              <option value="">Select teacher</option>
              ${options(teachers, "id", (teacher) => `${teacher.full_name} — ${teacher.designation_name}`)}
            </select></div>
          <div class="col-md-3"><div class="form-check mb-2">
            <input class="form-check-input" id="manual-override" type="checkbox">
            <label class="form-check-label" for="manual-override">Override preference</label>
          </div><button class="btn btn-primary w-100" type="submit">Assign</button></div>
        </form>
      </div></div>
      <div class="card border-0 shadow-sm"><div class="card-body">
        <h5 class="mb-3">Current Allocations</h5>
        <div id="allocations-table"></div>
      </div></div>`,
  );

  const renderAllocationsTable = (records) => {
    container.querySelector("#allocations-table").innerHTML = table(
      ["Sr. No.", "Course", "Department", "Teacher", "Section", "Term", "Workload", "Actions"],
      [...records]
        .sort((a, b) => a.course_name.localeCompare(b.course_name, undefined, { sensitivity: "base" }))
        .map((record, index) => `<tr>
        <td>${index + 1}</td>
        <td>${escapeHTML(record.course_code)} — ${escapeHTML(record.course_name)}</td>
        <td>${escapeHTML(record.course_department)}</td>
        <td>${escapeHTML(record.teacher_name)}</td><td>${escapeHTML(record.section_name)}</td>
        <td>${escapeHTML(record.academic_term)}</td><td>${record.workload_hours}</td>
        <td class="text-nowrap">
          <select class="form-select form-select-sm d-inline-block w-auto me-1" id="reassign-${record.allocation_id}">
            <option value="">Reassign…</option>
            ${options(teachers, "id", (teacher) => teacher.full_name)}
          </select>
          <button class="btn btn-sm btn-outline-primary me-1" data-reassign="${record.allocation_id}">Save</button>
          <button class="btn btn-sm btn-outline-danger" data-remove-allocation="${record.allocation_id}">Remove</button>
        </td>
      </tr>`),
    );
    container.querySelectorAll("[data-reassign]").forEach((button) => {
      button.addEventListener("click", async () => {
        const allocationId = button.dataset.reassign;
        const teacherId = container.querySelector(`#reassign-${allocationId}`).value;
        if (!teacherId) return;
        try {
          await api.put(`/allocations/${allocationId}`, {
            teacher_id: Number(teacherId),
            override_preference: true,
          });
          await renderAllocations(container);
          showSuccess(container, "Allocation reassigned.");
        } catch (error) {
          showError(container, error);
        }
      });
    });
    container.querySelectorAll("[data-remove-allocation]").forEach((button) => {
      button.addEventListener("click", async () => {
        try {
          await api.delete(`/allocations/${button.dataset.removeAllocation}`);
          await renderAllocations(container);
          showSuccess(container, "Allocation removed.");
        } catch (error) {
          showError(container, error);
        }
      });
    });
  };
  renderAllocationsTable(allocations);

  const termPayload = () => {
    const value = container.querySelector("#allocation-term").value;
    if (!value) {
      throw new Error("Select an academic term before running automatic allocation.");
    }
    return { term_id: Number(value) };
  };
  const renderUnallocatedOfferings = (records) => `
    <h6 class="mt-4">Unallocated offerings — assign manually</h6>
    ${table(
      ["Sr. No.", "Course Code", "Course Name", "Department", "Section", "Reason"],
      records.map((item, index) => `<tr>
        <td>${index + 1}</td><td>${escapeHTML(item.course_code)}</td>
        <td>${escapeHTML(item.course_name)}</td><td>${escapeHTML(item.department_name)}</td>
        <td>${escapeHTML(item.section_name)}</td><td>${escapeHTML(item.reason)}</td>
      </tr>`),
      "All offerings for this term were allocated.",
    )}`;
  container.querySelector("#preview-auto").addEventListener("click", async () => {
    try {
      const result = await api.post("/allocations/auto/preview", termPayload());
      container.querySelector("#allocation-preview").innerHTML = `
        <h6>Proposed assignments</h6>
        ${table(
          ["Sr. No.", "Course Code", "Course Name", "Department", "Academic Year", "Section", "Teacher", "Preference", "Projected Hours", "Status"],
          result.allocations.map((item, index) => `<tr>
            <td>${index + 1}</td><td>${escapeHTML(item.course_code)}</td>
            <td>${escapeHTML(item.course_name)}</td><td>${escapeHTML(item.department_name)}</td>
            <td>${escapeHTML(terms.find((term) => Number(term.id) === Number(item.academic_term_id))?.academic_year)}</td>
            <td>${escapeHTML(item.section_name)}</td>
            <td>${escapeHTML(item.teacher_name)}</td><td>${item.preference_priority}</td>
            <td>${item.projected_workload} / ${item.maximum_workload}</td>
            <td>${item.status}</td></tr>`),
        )}
        ${renderUnallocatedOfferings(result.unallocated)}`;
    } catch (error) {
      showError(container, error);
    }
  });
  container.querySelector("#execute-auto").addEventListener("click", async () => {
    try {
      const result = await api.post("/allocations/auto/execute", termPayload());
      await renderAllocations(container);
      container.querySelector("#allocation-preview").innerHTML =
        renderUnallocatedOfferings(result.unallocated);
      showSuccess(container, `${result.allocations.length} offerings allocated.`);
    } catch (error) {
      showError(container, error);
    }
  });
  container.querySelector("#manual-allocation-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      await api.post("/allocations/manual", {
        offering_id: Number(container.querySelector("#manual-offering").value),
        teacher_id: Number(container.querySelector("#manual-teacher").value),
        override_preference: container.querySelector("#manual-override").checked,
      });
      await renderAllocations(container);
      showSuccess(container, "Offering assigned.");
    } catch (error) {
      showError(container, error);
    }
  });
}

export async function renderReports(container) {
  const [teachers, departments, sections, terms] = await Promise.all([
    api.get("/teachers"),
    api.get("/departments"),
    api.get("/sections"),
    api.get("/academic-terms"),
  ]);
  container.innerHTML = pageHeader(
    "Reports",
    "View teacher, department, section, unallocated course, and allocation history reports.",
    `
      <div class="card border-0 shadow-sm mb-4"><div class="card-body">
        <form id="report-form" class="row g-3 align-items-end">
          <div class="col-md-3"><label class="form-label" for="report-type">Report</label>
            <select class="form-select" id="report-type">
              <option value="teacher">Teacher workload</option>
              <option value="department">Department allocations</option>
              <option value="section">Section offerings</option>
              <option value="unallocated">Unallocated offerings</option>
              <option value="history">Allocation history</option>
            </select></div>
          <div class="col-md-3" id="report-entity-wrap"><label class="form-label" for="report-entity">Record</label>
            <select class="form-select" id="report-entity"></select></div>
          <div class="col-md-3" id="report-term-wrap"><label class="form-label" for="report-term">Academic term</label>
            <select class="form-select" id="report-term"><option value="">Select term</option>
              ${options(terms, "id", (term) => `${term.name} (${term.semester}) — ${active(term.is_active) ? "Active" : "Inactive"}`)}</select></div>
          <div class="col-md-3 d-flex gap-2">
            <button class="btn btn-primary flex-fill" id="report-submit" type="submit">View</button>
            <button class="btn btn-outline-success flex-fill" id="report-download" type="button">Download Excel</button>
          </div>
        </form>
      </div></div>
      <div class="card border-0 shadow-sm"><div class="card-body"><div id="report-result"></div></div></div>`,
  );

  const type = container.querySelector("#report-type");
  const entityWrap = container.querySelector("#report-entity-wrap");
  const termWrap = container.querySelector("#report-term-wrap");
  const entity = container.querySelector("#report-entity");
  const submitButton = container.querySelector("#report-submit");
  const downloadButton = container.querySelector("#report-download");
  const updateFields = () => {
    const recordMap = {
      teacher: [teachers, (record) => `${record.full_name} — ${record.department_name}`],
      department: [departments, (record) => `${record.name} (${record.code})`],
      section: [sections, (record) => `${record.department_code} / ${record.name} — ${record.academic_year} ${record.semester}`],
    };
    const records = recordMap[type.value];
    entityWrap.hidden = !records;
    termWrap.hidden = ["section", "teacher"].includes(type.value);
    submitButton.textContent = type.value === "teacher" ? "View" : "Generate";
    downloadButton.hidden = type.value !== "teacher";
    if (records) {
      entity.innerHTML = `${type.value === "teacher" ? '<option value="">All teachers</option>' : ""}${options(records[0], "id", records[1])}`;
    }
  };
  type.addEventListener("change", updateFields);
  updateFields();

  container.querySelector("#report-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const reportType = type.value;
    const termId = container.querySelector("#report-term").value;
    const entityId = entity.value;
    if (reportType === "teacher") {
      try {
        const [allTeachers, allocations] = await Promise.all([
          api.get("/teachers"),
          api.get("/allocations"),
        ]);
        const filteredTeachers = entityId
          ? allTeachers.filter((teacher) => String(teacher.id) === entityId)
          : allTeachers;
        const teacherTotals = new Map(filteredTeachers.map((teacher) => [Number(teacher.id), 0]));
        allocations.forEach((allocation) => {
          const teacherId = Number(allocation.teacher_id);
          if (teacherTotals.has(teacherId)) {
            teacherTotals.set(
              teacherId,
              teacherTotals.get(teacherId) + Number(allocation.workload_hours),
            );
          }
        });
        const rows = filteredTeachers.flatMap((teacher) => {
          const assignedCourses = allocations.filter(
            (allocation) => Number(allocation.teacher_id) === Number(teacher.id),
          );
          return (assignedCourses.length ? assignedCourses : [null]).map((allocation) => ({
            teacher,
            allocation,
          }));
        }).sort((a, b) =>
          a.teacher.full_name.localeCompare(b.teacher.full_name, undefined, { sensitivity: "base" })
          || String(a.allocation?.course_name ?? "").localeCompare(
            String(b.allocation?.course_name ?? ""),
            undefined,
            { sensitivity: "base" },
          )
          || String(a.allocation?.academic_term ?? "").localeCompare(
            String(b.allocation?.academic_term ?? ""),
            undefined,
            { sensitivity: "base" },
          )
          || String(a.allocation?.section_name ?? "").localeCompare(
            String(b.allocation?.section_name ?? ""),
            undefined,
            { sensitivity: "base" },
          ),
        );
        container.querySelector("#report-result").innerHTML = `
          <h5>Teacher workload report</h5>
          ${table(
            ["Sr. No.", "Teacher", "Teacher Department", "Designation", "Course Code", "Course Name", "Academic Year", "Academic Term", "Semester", "Section", "Assigned Department", "Course Workload (Hours)", "Total Workload (All Terms)"],
            rows.map(({ teacher, allocation }, index) => `<tr>
              <td>${index + 1}</td><td>${escapeHTML(teacher.full_name)}</td>
              <td>${escapeHTML(teacher.department_name)}</td><td>${escapeHTML(teacher.designation_name)}</td>
              <td>${escapeHTML(allocation?.course_code ?? "—")}</td>
              <td>${escapeHTML(allocation?.course_name ?? "No courses assigned")}</td>
              <td>${escapeHTML(terms.find((term) => Number(term.id) === Number(allocation?.academic_term_id))?.academic_year ?? "—")}</td>
              <td>${escapeHTML(allocation?.academic_term ?? "—")}</td>
              <td>${escapeHTML(terms.find((term) => Number(term.id) === Number(allocation?.academic_term_id))?.semester ?? "—")}</td>
              <td>${escapeHTML(allocation?.section_name ?? "—")}</td>
              <td>${escapeHTML(allocation?.course_department ?? "—")}</td>
              <td>${allocation?.workload_hours ?? "—"}</td>
              <td>${teacherTotals.get(Number(teacher.id))}</td>
            </tr>`),
            "No teachers found.",
          )}`;
      } catch (error) {
        showError(container, error);
      }
      return;
    }
    if (!termId && reportType === "unallocated") {
      showError(container, new Error("Select an academic term for this report."));
      return;
    }
    let endpoint;
    if (reportType === "teacher") {
      endpoint = `/reports/teacher/${entityId}`;
    } else if (reportType === "department") {
      endpoint = `/reports/department/${entityId}`;
    } else if (reportType === "section") {
      endpoint = `/reports/section/${entityId}`;
    } else {
      endpoint = `/reports/${reportType}`;
    }
    if (termId && reportType !== "section") {
      endpoint += `${endpoint.includes("?") ? "&" : "?"}term_id=${encodeURIComponent(termId)}`;
    }
    try {
      const result = await api.get(endpoint);
      container.querySelector("#report-result").innerHTML = `
        <h5>Report results</h5>
        <pre class="bg-light border rounded p-3 mb-0">${escapeHTML(JSON.stringify(result, null, 2))}</pre>`;
    } catch (error) {
      showError(container, error);
    }
  });
  downloadButton.addEventListener("click", async () => {
    const teacherId = entity.value;
    try {
      const query = teacherId ? `?teacher_id=${encodeURIComponent(teacherId)}` : "";
      const response = await fetch(`/reports/teacher-workload.xlsx${query}`);
      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || "Unable to generate the teacher workload workbook.");
      }
      const workbook = await response.blob();
      const url = URL.createObjectURL(workbook);
      const link = document.createElement("a");
      link.href = url;
      link.download = teacherId
        ? `teacher-${teacherId}-workload.xlsx`
        : "teacher-workload.xlsx";
      document.body.append(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    } catch (error) {
      showError(container, error);
    }
  });
}

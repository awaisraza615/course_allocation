import { renderDepartments } from "./modules/departments.js";
import { renderAcademicTerms } from "./modules/academic-terms.js";
import { renderSections } from "./modules/sections.js";
import { renderDesignations } from "./modules/designations.js";
import {
  renderAllocations,
  renderCourses,
  renderOfferings,
  renderPreferences,
  renderReports,
  renderTeachers,
  renderWorkload,
} from "./modules/operations.js";

const mainContent = document.getElementById("main-content");
const pageTitle = document.getElementById("page-title");
const pageDescription = document.getElementById("page-description");

const pages = {
  dashboard: {
    title: "Dashboard",
    description: "University academic management overview",
    render: renderDashboard,
  },

  departments: {
    title: "Departments",
    description: "Manage university departments",
    render: renderDepartments,
  },
  "academic-terms": {
    title: "Academic Terms",
    description: "Manage academic years and semesters",
    render: renderAcademicTerms,
  },
  sections: {
    title: "Sections",
    description: "Manage department-wise academic sections",
    render: renderSections,
  },
  designations: {
    title: "Designations",
    description: "Manage teacher designations and workload policies",
    render: renderDesignations,
  },
  teachers: {
    title: "Teachers",
    description: "Manage teacher profiles and assignments",
    render: renderTeachers,
  },
  courses: {
    title: "Courses",
    description: "Manage courses and associated departments",
    render: renderCourses,
  },
  preferences: {
    title: "Preferences",
    description: "Manage teacher course preferences",
    render: renderPreferences,
  },
  offerings: {
    title: "Offerings",
    description: "Offer courses to sections within academic terms",
    render: renderOfferings,
  },
  workload: {
    title: "Workload",
    description: "Review term workload and teaching capacity",
    render: renderWorkload,
  },
  allocations: {
    title: "Allocations",
    description: "Allocate offerings manually or automatically",
    render: renderAllocations,
  },
  reports: {
    title: "Reports",
    description: "Review allocation and workload reports",
    render: renderReports,
  },
};

async function renderDashboard() {
  mainContent.innerHTML = `
        <div class="row g-4">

            ${[
              ["Departments", "building", "Manage academic departments"],
              ["Academic Terms", "calendar3", "Manage academic sessions"],
              ["Sections", "people", "Manage student sections"],
              ["Designations", "person-badge", "Manage teacher designations"],
              ["Teachers", "person", "Manage teacher profiles"],
              ["Courses", "journal-bookmark", "Manage courses and departments"],
              ["Preferences", "star", "Manage course preferences"],
              ["Offerings", "card-list", "Offer courses to sections"],
              ["Workload", "speedometer2", "Review teaching workload"],
              ["Allocations", "diagram-3", "Assign teachers to offerings"],
              ["Reports", "file-earmark-bar-graph", "Review allocation reports"],
            ]
              .map(
                ([title, icon, description]) => `
                <div class="col-md-6 col-xl-3">
                    <div class="card border-0 shadow-sm p-3 h-100">
                        <i class="bi bi-${icon} fs-3 text-primary"></i>
                        <h5 class="mt-3">${title}</h5>
                        <small class="text-muted">${description}</small>
                    </div>
                </div>
            `,
              )
              .join("")}

        </div>

        <div class="card border-0 shadow-sm mt-4 p-4">
            <h5>Welcome to University Management System</h5>
            <p class="text-muted mb-0">
                Manage your university's academic structure from one place.
            </p>
        </div>
    `;
}

async function navigateTo(page) {
  const config = pages[page];

  if (!config) {
    mainContent.innerHTML = `
            <div class="alert alert-info">
                This module is coming soon.
            </div>
        `;
    return;
  }

  pageTitle.textContent = config.title;
  pageDescription.textContent = config.description;

  document.querySelectorAll(".sidebar .nav-link").forEach((link) => {
    link.classList.toggle("active", link.dataset.page === page);
  });

  try {
    await config.render(mainContent);
  } catch (error) {
    mainContent.innerHTML = `
            <div class="alert alert-danger">
                ${error.message}
            </div>
        `;
  }
}

document.querySelectorAll(".sidebar .nav-link").forEach((link) => {
  link.addEventListener("click", (event) => {
    event.preventDefault();
    navigateTo(link.dataset.page);
  });
});

navigateTo("dashboard");

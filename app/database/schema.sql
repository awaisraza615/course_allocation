CREATE TABLE IF NOT EXISTS departments (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    code TEXT NOT NULL UNIQUE,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS academic_terms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    academic_year TEXT NOT NULL DEFAULT '',
    semester TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 0 CHECK (is_active IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE IF NOT EXISTS designations (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    standard_workload INTEGER NOT NULL CHECK (standard_workload >= 0),
    maximum_workload INTEGER NOT NULL CHECK (maximum_workload >= standard_workload),
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    department_id INTEGER NOT NULL,
    academic_term_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1
        CHECK (is_active IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (department_id, academic_term_id, name),

    FOREIGN KEY (department_id)
        REFERENCES departments (id),

    FOREIGN KEY (academic_term_id)
        REFERENCES academic_terms (id)
);

CREATE TABLE IF NOT EXISTS teachers (
    id INTEGER PRIMARY KEY,
    full_name TEXT NOT NULL,
    employee_code TEXT UNIQUE,
    department_id INTEGER NOT NULL,
    designation_id INTEGER NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (department_id) REFERENCES departments (id),
    FOREIGN KEY (designation_id) REFERENCES designations (id)
);

CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY,
    course_code TEXT NOT NULL UNIQUE,
    course_name TEXT NOT NULL,
    theory_hours INTEGER NOT NULL,
    laboratory_hours INTEGER NOT NULL,
    department_id INTEGER NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (
        (theory_hours = 3 AND laboratory_hours IN (0, 1))
        OR (theory_hours = 2 AND laboratory_hours IN (0, 1))
    ),
    FOREIGN KEY (department_id) REFERENCES departments (id)
);

CREATE TABLE IF NOT EXISTS course_departments (
    course_id INTEGER NOT NULL,
    department_id INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (course_id, department_id),
    FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE,
    FOREIGN KEY (department_id) REFERENCES departments (id)
);

CREATE INDEX IF NOT EXISTS idx_course_departments_department_id
    ON course_departments (department_id);

CREATE TABLE IF NOT EXISTS teacher_course_preferences (
    id INTEGER PRIMARY KEY,
    teacher_id INTEGER NOT NULL,
    course_id INTEGER NOT NULL,
    priority INTEGER NOT NULL CHECK (priority > 0),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (teacher_id, course_id),
    UNIQUE (teacher_id, priority),
    FOREIGN KEY (teacher_id) REFERENCES teachers (id),
    FOREIGN KEY (course_id) REFERENCES courses (id)
);

CREATE TABLE IF NOT EXISTS course_offerings (
    id INTEGER PRIMARY KEY,
    course_id INTEGER NOT NULL,
    section_id INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (course_id, section_id),
    FOREIGN KEY (course_id) REFERENCES courses (id),
    FOREIGN KEY (section_id) REFERENCES sections (id)
);

CREATE TABLE IF NOT EXISTS course_allocations (
    id INTEGER PRIMARY KEY,
    offering_id INTEGER NOT NULL,
    teacher_id INTEGER NOT NULL,
    workload_hours INTEGER NOT NULL DEFAULT 0 CHECK (workload_hours >= 0),
    standard_workload_snapshot INTEGER,
    maximum_workload_snapshot INTEGER,
    preference_priority INTEGER,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (offering_id),
    FOREIGN KEY (offering_id) REFERENCES course_offerings (id),
    FOREIGN KEY (teacher_id) REFERENCES teachers (id)
);

CREATE TABLE IF NOT EXISTS allocation_history (
    id INTEGER PRIMARY KEY,
    offering_id INTEGER NOT NULL,
    allocation_id INTEGER,
    action TEXT NOT NULL CHECK (action IN ('assigned', 'reassigned', 'removed')),
    previous_teacher_id INTEGER,
    new_teacher_id INTEGER,
    workload_hours INTEGER,
    standard_workload_snapshot INTEGER,
    maximum_workload_snapshot INTEGER,
    reason TEXT,
    changed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (offering_id) REFERENCES course_offerings (id),
    FOREIGN KEY (allocation_id) REFERENCES course_allocations (id) ON DELETE SET NULL,
    FOREIGN KEY (previous_teacher_id) REFERENCES teachers (id) ON DELETE SET NULL,
    FOREIGN KEY (new_teacher_id) REFERENCES teachers (id) ON DELETE SET NULL
);

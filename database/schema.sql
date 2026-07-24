CREATE TABLE departments (
    id UUID PRIMARY KEY,
    department_name VARCHAR(100) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'Active'
);
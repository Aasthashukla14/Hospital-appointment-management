CREATE TABLE departments (
    id UUID PRIMARY KEY,
    department_name VARCHAR(100) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'Active'
);


CREATE TABLE doctors (
    id UUID PRIMARY KEY,
    employee_id VARCHAR(20) UNIQUE NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    department_id UUID NOT NULL,
    specialization VARCHAR(100),
    consultation_fee DECIMAL(10,2),
    phone VARCHAR(15),
    email VARCHAR(100),
    status VARCHAR(20) DEFAULT 'Active',

    FOREIGN KEY (department_id)
        REFERENCES departments(id)
);
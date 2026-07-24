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


CREATE TABLE patients (
    id UUID PRIMARY KEY,
    uhid VARCHAR(20) UNIQUE NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50),
    gender VARCHAR(10),
    date_of_birth DATE,
    phone VARCHAR(15),
    email VARCHAR(100),
    address TEXT,
    status VARCHAR(20) DEFAULT 'Active'
);

CREATE TABLE appointments (
    id UUID PRIMARY KEY,
    appointment_number VARCHAR(20) UNIQUE NOT NULL,

    patient_id UUID NOT NULL,
    doctor_id UUID NOT NULL,
    department_id UUID NOT NULL,

    appointment_date DATE NOT NULL,
    appointment_time TIME NOT NULL,
    duration_minutes INT DEFAULT 30,

    appointment_type VARCHAR(30),
    priority VARCHAR(20) DEFAULT 'Normal',
    reason TEXT,

    status VARCHAR(20) DEFAULT 'Scheduled',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (patient_id)
        REFERENCES patients(id),

    FOREIGN KEY (doctor_id)
        REFERENCES doctors(id),

    FOREIGN KEY (department_id)
        REFERENCES departments(id)
);
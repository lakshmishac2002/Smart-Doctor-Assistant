-- Database Schema for Smart Doctor Assistant

-- Drop tables if they exist (for clean setup)
DROP TABLE IF EXISTS appointments CASCADE;
DROP TABLE IF EXISTS patients CASCADE;
DROP TABLE IF EXISTS doctors CASCADE;

-- Doctors Table
CREATE TABLE doctors (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    specialization VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),
    available_days TEXT[], -- Array of days: ['Monday', 'Tuesday', ...]
    available_start_time TIME NOT NULL,
    available_end_time TIME NOT NULL,
    slot_duration_minutes INTEGER DEFAULT 30,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Patients Table
CREATE TABLE patients (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),
    date_of_birth DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Appointments Table
CREATE TABLE appointments (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(id) ON DELETE CASCADE,
    doctor_id INTEGER REFERENCES doctors(id) ON DELETE CASCADE,
    appointment_date DATE NOT NULL,
    appointment_time TIME NOT NULL,
    duration_minutes INTEGER DEFAULT 30,
    status VARCHAR(50) DEFAULT 'scheduled', -- scheduled, completed, cancelled, no-show
    symptoms TEXT,
    diagnosis TEXT,
    notes TEXT,
    google_calendar_event_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(doctor_id, appointment_date, appointment_time)
);

-- Indexes for performance
CREATE INDEX idx_appointments_doctor_date ON appointments(doctor_id, appointment_date);
CREATE INDEX idx_appointments_patient ON appointments(patient_id);
CREATE INDEX idx_appointments_status ON appointments(status);
CREATE INDEX idx_doctors_email ON doctors(email);
CREATE INDEX idx_patients_email ON patients(email);

-- Seed Data
INSERT INTO doctors (name, specialization, email, phone, available_days, available_start_time, available_end_time, slot_duration_minutes) VALUES
('Dr. Rajesh Ahuja', 'General Physician', 'dr.ahuja@hospital.com', '+91-9876543210', ARRAY['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'], '09:00:00', '17:00:00', 30),
('Dr. Priya Sharma', 'Cardiologist', 'dr.sharma@hospital.com', '+91-9876543211', ARRAY['Monday', 'Wednesday', 'Friday'], '10:00:00', '18:00:00', 45),
('Dr. Amit Patel', 'Pediatrician', 'dr.patel@hospital.com', '+91-9876543212', ARRAY['Tuesday', 'Thursday', 'Saturday'], '08:00:00', '16:00:00', 30),
('Dr. Sneha Gupta', 'Dermatologist', 'dr.gupta@hospital.com', '+91-9876543213', ARRAY['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'], '11:00:00', '19:00:00', 30);

INSERT INTO patients (name, email, phone, date_of_birth) VALUES
('Rahul Kumar', 'rahul.kumar@email.com', '+91-9123456789', '1990-05-15'),
('Anita Desai', 'anita.desai@email.com', '+91-9123456788', '1985-08-22'),
('Vikram Singh', 'vikram.singh@email.com', '+91-9123456787', '1995-03-10'),
('Meera Reddy', 'meera.reddy@email.com', '+91-9123456786', '1988-12-05');

-- Sample appointments (for testing doctor stats)
INSERT INTO appointments (patient_id, doctor_id, appointment_date, appointment_time, duration_minutes, status, symptoms) VALUES
(1, 1, CURRENT_DATE - INTERVAL '1 day', '10:00:00', 30, 'completed', 'Fever, headache'),
(2, 1, CURRENT_DATE - INTERVAL '1 day', '14:00:00', 30, 'completed', 'Fever, cough'),
(3, 1, CURRENT_DATE, '11:00:00', 30, 'scheduled', 'Regular checkup'),
(4, 2, CURRENT_DATE + INTERVAL '1 day', '15:00:00', 45, 'scheduled', 'Chest pain');

-- schema.sql
-- Drop existing tables (if you want a clean slate)
DROP TABLE IF EXISTS messages CASCADE;
DROP TABLE IF EXISTS chat_sessions CASCADE;
DROP TABLE IF EXISTS documents CASCADE;
DROP TABLE IF EXISTS otp_verifications CASCADE;
DROP TABLE IF EXISTS doctors_registry CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- ==========================
-- USERS
-- ==========================
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role VARCHAR(20) DEFAULT 'general',
    legal_no VARCHAR(50),
    phone_number VARCHAR(20),
    full_name VARCHAR(255),
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================
-- DOCTORS REGISTRY
-- ==========================
CREATE TABLE doctors_registry (
    id SERIAL PRIMARY KEY,
    legal_no VARCHAR(50) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    phone_number VARCHAR(20) NOT NULL,
    specialization VARCHAR(255),
    license_status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================
-- OTP VERIFICATION
-- ==========================
CREATE TABLE otp_verifications (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    phone_number VARCHAR(20) NOT NULL,
    email VARCHAR(255) NOT NULL,
    otp_code VARCHAR(6) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    attempts INT DEFAULT 0,
    max_attempts INT DEFAULT 3,
    expires_at TIMESTAMP NOT NULL,
    verified_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    registration_data JSONB
);

-- ==========================
-- CHAT SESSIONS
-- ==========================
CREATE TABLE chat_sessions (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    title VARCHAR(255) DEFAULT 'New chat',
    summary TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================
-- MESSAGES
-- ==========================
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    session_id INT REFERENCES chat_sessions(id) ON DELETE CASCADE NOT NULL,
    role VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    citations JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================
-- DOCUMENTS
-- ==========================
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    filename VARCHAR(255) NOT NULL,
    filepath TEXT NOT NULL,
    doc_type VARCHAR(50) DEFAULT 'medical' NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================
-- SEED DOCTORS REGISTRY
-- ==========================
INSERT INTO doctors_registry (id, legal_no, full_name, phone_number, specialization, license_status, created_at, updated_at)
VALUES
(1, 'MED001', 'Dr. Rajesh Kumar', '9876543210', 'General Medicine', 'active', '2025-08-24 02:56:43.512152', '2025-08-24 02:56:43.512152'),
(2, 'MED002', 'Dr. Priya Sharma', '8765432109', 'Cardiology', 'active', '2025-08-24 02:56:43.512152', '2025-08-24 02:56:43.512152'),
(3, 'MED003', 'Dr. Amit Patel', '8667213530', 'Orthopedics', 'active', '2025-08-24 02:56:43.512152', '2025-08-25 13:32:05.104663'),
(4, 'MED004', 'Dr. Sunita Reddy', '6543210987', 'Pediatrics', 'active', '2025-08-24 02:56:43.512152', '2025-08-24 02:56:43.512152'),
(5, 'MED005', 'Dr. Vikram Singh', '5432109876', 'Neurology', 'active', '2025-08-24 02:56:43.512152', '2025-08-24 02:56:43.512152'),
(6, 'MED006', 'Dr. Emily Rodriguez', '9876543215', 'Psychiatry', 'active', '2025-08-25 07:13:37.842133', '2025-08-25 07:13:37.842133'),
(7, 'MED007', 'Dr. James Wilson', '9876543216', 'Emergency Medicine', 'active', '2025-08-25 07:13:37.842133', '2025-08-25 07:13:37.842133');

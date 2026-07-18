-- CREATE DATABASE ditec_attendance;
USE ditec_attendance;

CREATE TABLE admins(
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE officers(
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id VARCHAR(20) UNIQUE,
    aadhaar CHAR(12) NOT NULL UNIQUE,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(10),
    face_image VARCHAR(255),
    qr_code VARCHAR(255),
    status ENUM('Pending','Approved','Rejected') DEFAULT 'Pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE attendance(
    id INT AUTO_INCREMENT PRIMARY KEY,
    officer_id INT NOT NULL,
    attendance_date DATE NOT NULL,
    in_time TIME NULL,
    out_time TIME NULL,
    attendance_type ENUM('IN','OUT'),
    face_verified BOOLEAN DEFAULT FALSE,
    qr_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(officer_id) REFERENCES officers(id)
);

CREATE TABLE login_logs(
    id INT AUTO_INCREMENT PRIMARY KEY,
    officer_id INT,
    login_time DATETIME,
    ip_address VARCHAR(50),
    status VARCHAR(20),
    FOREIGN KEY(officer_id) REFERENCES officers(id)
);

-- INSERT INTO admins(username, password)
-- VALUES ('admin', 'admin123');
-- ALTER TABLE officers
-- ADD COLUMN password VARCHAR(255);

CREATE TABLE attendance_photos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    attendance_id INT NOT NULL,
    photo_path VARCHAR(255) NOT NULL,
    captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(attendance_id) REFERENCES attendance(id) ON DELETE CASCADE
);
-- ALTER TABLE officers
-- ADD COLUMN face_descriptor LONGTEXT;
SELECT * FROM officers;
SELECT * FROM admins;
SELECT * FROM attendance;
SELECT * FROM attendance_photos;
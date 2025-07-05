CREATE DATABASE IF NOT EXISTS bill_data CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE bill_data;

CREATE TABLE IF NOT EXISTS thong_tin_hoa_don (
    id INT AUTO_INCREMENT PRIMARY KEY,
    thoi_gian DATETIME,
    nguoi_gui VARCHAR(255),
    ten_khach VARCHAR(255),
    so_dien_thoai VARCHAR(20),
    type_dao_rut VARCHAR(20), 
    ngan_hang VARCHAR(100),
    ngay_giao_dich VARCHAR(50),
    gio_giao_dich VARCHAR(50),
    tong_so_tien VARCHAR(50),
    so_the VARCHAR(100),
    tid VARCHAR(50),
    mid VARCHAR(50),
    so_lo VARCHAR(100),
    so_hoa_don VARCHAR(100),
    ten_may_pos VARCHAR(100),
    lich_canh_bao VARCHAR(50),
    tien_phi VARCHAR(50),
    batch_id VARCHAR(250),
    caption_goc TEXT,
    ket_toan VARCHAR(255),
    ck_ra VARCHAR(255),
    ck_vao VARCHAR(255),
    stk_khach VARCHAR(255),
    stk_cty VARCHAR(255),
    tinh_trang VARCHAR(255),
    ly_do VARCHAR(255),
    dia_chi VARCHAR(300),
    phan_tram_phi VARCHAR(300),
    khach_moi boolean default FALSE null,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS hoa_don_dien (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    nha_cung_cap VARCHAR(255),
    ten_khach_hang VARCHAR(255),
    ma_khach_hang VARCHAR(50),
    dia_chi VARCHAR(500),
    ky_thanh_toan VARCHAR(100),
    so_tien BIGINT,
    ma_giao_dich VARCHAR(100) UNIQUE,
    thoi_gian DATETIME,
    tai_khoan_the VARCHAR(100),
    tong_phi VARCHAR(100),
    trang_thai VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    batch_id VARCHAR(250),
);

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role ENUM('admin', 'manager', 'user') DEFAULT 'user',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);

-- Insert default admin user (password: admin123)
INSERT INTO users (email, username, hashed_password, role, is_active)
VALUES (2,'hieunkbb@gmail.com','hieunguyenkhac','$2b$12$BJcODXLEDQxukS6jHVFvxuDd7ymxIHlVn9VM7ZQMHk3.hwBQ/7pnK','admin',1,'2025-07-02 03:01:33','2025-07-02 03:02:10');

UNLOCK TABLES;ON DUPLICATE KEY UPDATE username=username; 
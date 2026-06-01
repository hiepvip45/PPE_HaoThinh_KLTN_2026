-- ============================================
-- PPE GUARDIAN - Database Setup Script
-- Chạy script này trong MySQL Workbench hoặc XAMPP phpMyAdmin
-- ============================================

CREATE DATABASE IF NOT EXISTS ppe_guardian
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE ppe_guardian;

-- Bảng cấu hình hệ thống
CREATE TABLE IF NOT EXISTS system_config (
    id INT AUTO_INCREMENT PRIMARY KEY,
    config_key VARCHAR(100) NOT NULL UNIQUE,
    config_value TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Bảng lịch sử phát hiện (mỗi frame/ảnh được phân tích)
CREATE TABLE IF NOT EXISTS detections (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(50),
    source_type ENUM('webcam', 'video', 'image') NOT NULL,
    source_name VARCHAR(255),
    detected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    total_persons INT DEFAULT 0,
    has_violation BOOLEAN DEFAULT FALSE,
    image_path VARCHAR(500),
    frame_number INT DEFAULT 0,
    confidence_avg FLOAT DEFAULT 0.0
);

-- Bảng chi tiết từng đối tượng phát hiện
CREATE TABLE IF NOT EXISTS detection_objects (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    detection_id BIGINT NOT NULL,
    class_name VARCHAR(100) NOT NULL,
    confidence FLOAT NOT NULL,
    bbox_x1 FLOAT, bbox_y1 FLOAT,
    bbox_x2 FLOAT, bbox_y2 FLOAT,
    is_violation BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (detection_id) REFERENCES detections(id) ON DELETE CASCADE
);

-- Bảng vi phạm (chỉ lưu khi có vi phạm)
CREATE TABLE IF NOT EXISTS violations (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    detection_id BIGINT NOT NULL,
    violation_type VARCHAR(100) NOT NULL,
    violation_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    image_path VARCHAR(500),
    telegram_sent BOOLEAN DEFAULT FALSE,
    telegram_sent_at DATETIME NULL,
    source_type ENUM('webcam', 'video', 'image') NOT NULL,
    source_name VARCHAR(255),
    confidence FLOAT DEFAULT 0.0,
    FOREIGN KEY (detection_id) REFERENCES detections(id) ON DELETE CASCADE
);

-- Bảng thống kê theo ngày (cache để query nhanh)
CREATE TABLE IF NOT EXISTS daily_stats (
    id INT AUTO_INCREMENT PRIMARY KEY,
    stat_date DATE NOT NULL UNIQUE,
    total_detections INT DEFAULT 0,
    total_violations INT DEFAULT 0,
    total_persons INT DEFAULT 0,
    compliance_rate FLOAT DEFAULT 0.0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Insert cấu hình mặc định
INSERT INTO system_config (config_key, config_value) VALUES
    ('telegram_bot_token', ''),
    ('telegram_chat_id', ''),
    ('alert_cooldown_seconds', '30'),
    ('confidence_threshold', '0.5'),
    ('violation_classes', 'NO-Gloves,NO-Goggles,NO-Hardhat,NO-Mask,NO-Safety Vest,Fall-Detected'),
    ('db_host', 'localhost'),
    ('db_port', '3306'),
    ('db_name', 'ppe_guardian'),
    ('db_user', 'root'),
    ('db_password', ''),
    ('capture_violations', '1'),
    ('send_telegram', '1')
ON DUPLICATE KEY UPDATE config_key = config_key;

-- Index để tăng tốc query
CREATE INDEX idx_detections_date ON detections(detected_at);
CREATE INDEX idx_violations_date ON violations(violation_at);
CREATE INDEX idx_violations_type ON violations(violation_type);
CREATE INDEX idx_detection_objects_class ON detection_objects(class_name);

SELECT 'Database PPE Guardian đã được tạo thành công!' AS message;

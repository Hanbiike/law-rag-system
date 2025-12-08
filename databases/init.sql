CREATE DATABASE IF NOT EXISTS law_rag_users;
USE law_rag_users;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    telegram_id BIGINT UNIQUE,
    lang VARCHAR(2) DEFAULT 'ru',
    response_type VARCHAR(10) DEFAULT 'base',
    balance INT DEFAULT 10,
    last_conversation VARCHAR(255) DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Migration: Add response_type column if not exists
-- ALTER TABLE users ADD COLUMN response_type VARCHAR(10) DEFAULT 'base' AFTER lang;
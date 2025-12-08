CREATE DATABASE IF NOT EXISTS law_rag_users;
USE law_rag_users;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    telegram_id BIGINT UNIQUE,
    lang VARCHAR(2) DEFAULT 'ru',
    balance INT DEFAULT 10,
    last_conversation VARCHAR(255) DEFAULT NULL
);
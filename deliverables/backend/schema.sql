-- ============================================================
-- 青禾志愿 · MySQL 数据库结构（登录/注册用）
-- 当前只建 users 用户表，后续按架构文档逐步扩展其余表。
-- 字符集 utf8mb4，引擎 InnoDB
-- ============================================================

CREATE DATABASE IF NOT EXISTS qinghe_volunteer DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE qinghe_volunteer;

-- 用户账号表
CREATE TABLE IF NOT EXISTS users (
    id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    phone         VARCHAR(20)  NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name          VARCHAR(50)  DEFAULT NULL,
    role          ENUM('student','publisher_internal','publisher_external','admin') NOT NULL DEFAULT 'student',
    student_no    VARCHAR(32)  DEFAULT NULL COMMENT '学号（学生端，登录凭证之一）',
    org           VARCHAR(100) DEFAULT NULL COMMENT '所属机构/单位（发布者/校方）',
    worker_no     VARCHAR(32)  DEFAULT NULL COMMENT '工号（校方端，登录凭证之一）',
    status        ENUM('active','disabled') NOT NULL DEFAULT 'active',
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_users_phone (phone),
    UNIQUE KEY uk_users_student_no (student_no),
    UNIQUE KEY uk_users_worker_no (worker_no)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 活动表（报名/签到用）
CREATE TABLE IF NOT EXISTS activities (
    id           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    name         VARCHAR(100) NOT NULL,
    org          VARCHAR(100) NOT NULL,
    scope        VARCHAR(20)  DEFAULT NULL,
    category     VARCHAR(20)  DEFAULT NULL,
    date         VARCHAR(20)  DEFAULT NULL,
    time         VARCHAR(50)  DEFAULT NULL,
    location     VARCHAR(255) DEFAULT NULL,
    hours        VARCHAR(10)  DEFAULT NULL,
    headcount    INT NOT NULL DEFAULT 0,
    signed_count INT NOT NULL DEFAULT 0,
    gradient     VARCHAR(50)  DEFAULT NULL,
    badge        VARCHAR(20)  DEFAULT NULL,
    status       VARCHAR(20)  NOT NULL DEFAULT 'recruiting',
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 报名表
CREATE TABLE IF NOT EXISTS signups (
    id          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    activity_id BIGINT UNSIGNED NOT NULL,
    user_id     BIGINT UNSIGNED NOT NULL,
    status      VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_signups_activity_user (activity_id, user_id),
    CONSTRAINT fk_signups_activity FOREIGN KEY (activity_id) REFERENCES activities(id),
    CONSTRAINT fk_signups_user FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 签到/签退表
CREATE TABLE IF NOT EXISTS checkins (
    id          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    activity_id BIGINT UNSIGNED NOT NULL,
    user_id     BIGINT UNSIGNED NOT NULL,
    signup_id   BIGINT UNSIGNED DEFAULT NULL,
    type        VARCHAR(10) NOT NULL,
    check_time  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_checkins_activity_user_type (activity_id, user_id, type),
    CONSTRAINT fk_checkins_activity FOREIGN KEY (activity_id) REFERENCES activities(id),
    CONSTRAINT fk_checkins_user FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 志愿时长表（签退后自动生成，待校方认定）
CREATE TABLE IF NOT EXISTS volunteer_hours (
    id          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    activity_id BIGINT UNSIGNED NOT NULL,
    user_id     BIGINT UNSIGNED NOT NULL,
    signup_id   BIGINT UNSIGNED DEFAULT NULL,
    hours       DECIMAL(6,1) NOT NULL DEFAULT 0,
    status      VARCHAR(20) NOT NULL DEFAULT 'pending',
    verified_by BIGINT UNSIGNED DEFAULT NULL,
    verified_at DATETIME DEFAULT NULL,
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_hours_activity_user (activity_id, user_id),
    CONSTRAINT fk_hours_activity FOREIGN KEY (activity_id) REFERENCES activities(id),
    CONSTRAINT fk_hours_user FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 时长申诉表
CREATE TABLE IF NOT EXISTS appeals (
    id          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    hours_id    BIGINT UNSIGNED NOT NULL,
    user_id     BIGINT UNSIGNED NOT NULL,
    reason      VARCHAR(500) NOT NULL,
    status      VARCHAR(20) NOT NULL DEFAULT 'pending',
    handled_by  BIGINT UNSIGNED DEFAULT NULL,
    handled_at  DATETIME DEFAULT NULL,
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_appeals_hours FOREIGN KEY (hours_id) REFERENCES volunteer_hours(id),
    CONSTRAINT fk_appeals_user FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 证书表
CREATE TABLE IF NOT EXISTS certificates (
    id          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id     BIGINT UNSIGNED NOT NULL,
    activity_id BIGINT UNSIGNED DEFAULT NULL,
    type        VARCHAR(20) NOT NULL DEFAULT 'single',
    cert_no     VARCHAR(32) NOT NULL,
    qr_token    VARCHAR(64) NOT NULL,
    hours       DECIMAL(6,1) NOT NULL DEFAULT 0,
    issuer      VARCHAR(100) DEFAULT NULL,
    pdf_url     VARCHAR(255) DEFAULT NULL,
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_certificates_cert_no (cert_no),
    UNIQUE KEY uk_certificates_qr_token (qr_token),
    CONSTRAINT fk_certificates_user FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

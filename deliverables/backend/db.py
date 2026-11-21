#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""数据库访问层：支持 SQLite（零依赖兜底）与 MySQL 双引擎。

- 通过 config.DB_ENGINE 切换。
- query() 返回 list[dict]，query_one() 返回 dict 或 None，execute() 返回 (rowcount, lastrowid)。
- 占位符统一用 ?，MySQL 分支自动替换为 %s。
"""
import os
import sqlite3
from decimal import Decimal

import config


def _mysql_conn():
    import pymysql
    return pymysql.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        database=config.DB_NAME,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )


def _sqlite_conn():
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def get_conn():
    return _mysql_conn() if config.DB_ENGINE == "mysql" else _sqlite_conn()


def _to_py(v):
    """把数据库返回值转成 JSON 友好类型：MySQL 的 Decimal → float。"""
    if isinstance(v, Decimal):
        return float(v)
    return v


def _rows_to_dicts(rows):
    return [{k: _to_py(v) for k, v in dict(r).items()} for r in rows]


def _translate(sql):
    """SQLite 用 ? 占位，MySQL 换成 %s。"""
    return sql.replace("?", "%s") if config.DB_ENGINE == "mysql" else sql


def query(sql, args=()):
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(_translate(sql), args)
        return _rows_to_dicts(cur.fetchall())
    finally:
        conn.close()


def query_one(sql, args=()):
    rows = query(sql, args)
    return rows[0] if rows else None


def execute(sql, args=()):
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(_translate(sql), args)
        if config.DB_ENGINE == "sqlite":
            conn.commit()
        return cur.rowcount, cur.lastrowid
    finally:
        conn.close()


# ---- 建表 ----
_USERS_SQLITE = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    phone         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    name          TEXT,
    role          TEXT NOT NULL DEFAULT 'student',
    student_no    TEXT,
    org           TEXT,
    worker_no     TEXT,
    status        TEXT NOT NULL DEFAULT 'active',
    created_at    TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    updated_at    TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
"""


_ACTIVITIES_SQLITE = """
CREATE TABLE IF NOT EXISTS activities (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    name         TEXT NOT NULL,
    org          TEXT NOT NULL,
    scope        TEXT,
    category     TEXT,
    date         TEXT,
    time         TEXT,
    location     TEXT,
    hours        TEXT,
    headcount    INTEGER NOT NULL DEFAULT 0,
    signed_count INTEGER NOT NULL DEFAULT 0,
    gradient     TEXT,
    badge        TEXT,
    status       TEXT NOT NULL DEFAULT 'recruiting'
);
"""

_SIGNUPS_SQLITE = """
CREATE TABLE IF NOT EXISTS signups (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    activity_id INTEGER NOT NULL REFERENCES activities(id),
    user_id     INTEGER NOT NULL REFERENCES users(id),
    status      TEXT NOT NULL DEFAULT 'active',
    created_at  TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    UNIQUE (activity_id, user_id)
);
"""

_CHECKINS_SQLITE = """
CREATE TABLE IF NOT EXISTS checkins (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    activity_id INTEGER NOT NULL REFERENCES activities(id),
    user_id     INTEGER NOT NULL REFERENCES users(id),
    signup_id   INTEGER REFERENCES signups(id),
    type        TEXT NOT NULL CHECK (type IN ('checkin','checkout')),
    check_time  TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    UNIQUE (activity_id, user_id, type)
);
"""

_HOURS_SQLITE = """
CREATE TABLE IF NOT EXISTS volunteer_hours (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    activity_id INTEGER NOT NULL REFERENCES activities(id),
    user_id     INTEGER NOT NULL REFERENCES users(id),
    signup_id   INTEGER REFERENCES signups(id),
    hours       REAL NOT NULL DEFAULT 0,
    status      TEXT NOT NULL DEFAULT 'pending',
    verified_by INTEGER REFERENCES users(id),
    verified_at TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    UNIQUE (activity_id, user_id)
);
"""

_APPEALS_SQLITE = """
CREATE TABLE IF NOT EXISTS appeals (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    hours_id    INTEGER NOT NULL REFERENCES volunteer_hours(id),
    user_id     INTEGER NOT NULL REFERENCES users(id),
    reason      TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'pending',
    handled_by  INTEGER REFERENCES users(id),
    handled_at  TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
"""

_CERTIFICATES_SQLITE = """
CREATE TABLE IF NOT EXISTS certificates (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id),
    activity_id INTEGER REFERENCES activities(id),
    type        TEXT NOT NULL DEFAULT 'single',
    cert_no     TEXT NOT NULL UNIQUE,
    qr_token    TEXT NOT NULL UNIQUE,
    hours       REAL NOT NULL DEFAULT 0,
    issuer      TEXT,
    pdf_url     TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
"""


def _migrate_sqlite():
    """为旧版 users 表补齐新增列（幂等，不丢数据）。"""
    conn = sqlite3.connect(config.DB_PATH)
    try:
        cur = conn.cursor()
        cols = {r[1] for r in cur.execute("PRAGMA table_info(users)").fetchall()}
        to_add = {"student_no": "TEXT", "org": "TEXT", "worker_no": "TEXT"}
        for col, typ in to_add.items():
            if col not in cols:
                cur.execute(f"ALTER TABLE users ADD COLUMN {col} {typ}")
        conn.commit()
    finally:
        conn.close()


def _migrate_mysql(cur):
    """为旧版 users 表补齐新增列与唯一索引（幂等，不丢数据）。"""
    cur.execute("SHOW COLUMNS FROM users")
    cols = {r[0] for r in cur.fetchall()}
    add_cols = {
        "student_no": "VARCHAR(32) DEFAULT NULL",
        "org": "VARCHAR(100) DEFAULT NULL",
        "worker_no": "VARCHAR(32) DEFAULT NULL",
    }
    for col, ddl in add_cols.items():
        if col not in cols:
            cur.execute(f"ALTER TABLE users ADD COLUMN {col} {ddl}")
    for col in ("student_no", "worker_no"):
        try:
            cur.execute(f"ALTER TABLE users ADD UNIQUE KEY uk_users_{col} ({col})")
        except Exception:
            pass  # 唯一索引已存在


def init_db():
    """初始化：确保数据库与所有表存在，并 seed 活动数据（幂等）。"""
    if config.DB_ENGINE == "mysql":
        _init_mysql()
    else:
        conn = sqlite3.connect(config.DB_PATH)
        conn.executescript(
            _USERS_SQLITE + _ACTIVITIES_SQLITE + _SIGNUPS_SQLITE
            + _CHECKINS_SQLITE + _HOURS_SQLITE + _APPEALS_SQLITE + _CERTIFICATES_SQLITE
        )
        conn.commit()
        conn.close()
        _migrate_sqlite()
    _seed_activities()


def _seed_activities():
    """首次启动时，把 test_data.json 里的活动写入 activities 表（幂等）。"""
    if query_one("SELECT COUNT(*) AS c FROM activities")["c"] > 0:
        return
    import json
    with open(config.DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    for a in data.get("activities", []):
        execute(
            "INSERT INTO activities "
            "(name, org, scope, category, date, time, location, hours, headcount, signed_count, gradient, badge, status) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                a["title"], a["org"], a.get("scope"), a.get("category"), a.get("date"),
                a.get("time"), a.get("location"), a.get("hours"), a["recruit"], a["signed"],
                a.get("gradient"), (a.get("badge") or {}).get("label"),
                "full" if a.get("full") else "recruiting",
            ),
        )


def _mysql_connect(**overrides):
    """建立 MySQL 连接（带重试，适配 MySQL 启动较慢的场景）。"""
    import pymysql
    import time
    kwargs = dict(
        host=config.DB_HOST, port=config.DB_PORT,
        user=config.DB_USER, password=config.DB_PASSWORD,
        charset="utf8mb4", autocommit=True,
    )
    kwargs.update(overrides)
    last_err = None
    for attempt in range(15):  # 最多重试约 15 秒
        try:
            return pymysql.connect(**kwargs)
        except Exception as e:  # noqa: BLE001
            last_err = e
            time.sleep(1)
    raise RuntimeError(
        f"无法连接 MySQL（{config.DB_HOST}:{config.DB_PORT}），"
        "请确认 MySQL 已启动（可双击 start_mysql.bat）。原始错误：{last_err}"
    )


def _init_mysql():
    # 连接服务器（不指定库）以建库
    conn = _mysql_connect()
    cur = conn.cursor()
    cur.execute(
        f"CREATE DATABASE IF NOT EXISTS {config.DB_NAME} "
        "DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
    )
    conn.select_db(config.DB_NAME)
    schema_file = os.path.join(config.BASE_DIR, "schema.sql")
    with open(schema_file, "r", encoding="utf-8") as f:
        for stmt in _split_sql(f.read()):
            if stmt.strip():
                cur.execute(stmt)
    _migrate_mysql(cur)  # 旧表补列 + 唯一索引
    conn.close()


def _split_sql(ddl):
    statements, buf = [], []
    for line in ddl.splitlines():
        s = line.strip()
        if s.startswith("--"):
            continue
        buf.append(line)
        if s.endswith(";"):
            statements.append("\n".join(buf))
            buf = []
    if buf:
        statements.append("\n".join(buf))
    return statements

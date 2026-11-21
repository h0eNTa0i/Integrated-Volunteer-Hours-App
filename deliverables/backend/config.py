#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全局配置：全部可用环境变量覆盖，未设置时使用本地开发默认值。"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.normpath(os.path.join(BASE_DIR, "..", "frontend"))

# 测试数据文件（动态业务数据来源）
DATA_FILE = os.path.join(BASE_DIR, "test_data.json")

# ---- 数据库 ----
# DB_ENGINE=mysql（默认）| sqlite（无 MySQL 时的零依赖兜底）
DB_ENGINE = os.environ.get("DB_ENGINE", "mysql")
DB_PATH = os.environ.get("DB_PATH", os.path.join(BASE_DIR, "qinghe.db"))
DB_HOST = os.environ.get("DB_HOST", "127.0.0.1")
DB_PORT = int(os.environ.get("DB_PORT", "3306"))
DB_USER = os.environ.get("DB_USER", "root")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "123456")
DB_NAME = os.environ.get("DB_NAME", "qinghe_volunteer")

# ---- 鉴权 ----
JWT_SECRET = os.environ.get("JWT_SECRET", "qinghe-dev-secret-please-change")
JWT_ALGORITHM = "HS256"
# token 有效期（分钟）。默认 30 天 = 43200，用于「登录一次、长期免登录」；
# 上线前建议改为短时效 + 独立刷新令牌。
JWT_EXPIRE_MINUTES = int(os.environ.get("JWT_EXPIRE_MINUTES", "43200"))

# ---- CORS ----
CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*")          # 逗号分隔多个来源；* 表示任意

# ---- 服务 ----
PORT = int(os.environ.get("PORT", "8787"))

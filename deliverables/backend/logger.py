#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""日志系统：实时输出控制台 + 按天轮转写盘（保留 30 天），并支持请求 ID 贯穿。

用法：
    import logger
    log = logger.setup()          # 初始化（app.py 启动时调用一次）
    logger.set_request_id(rid)    # 每个请求开始时设置（app.py before_request）
    log.info("...")               # 业务/请求/错误日志，自动带上当前请求 ID

日志文件：backend/logs/app.log（按天轮转，旧文件 app.log.2026-11-05 之类保留 30 天）。
"""
import contextvars
import logging
import os
from logging.handlers import TimedRotatingFileHandler

import config

# 请求 ID 上下文变量：同一请求内的所有日志共享同一个 ID（全链路追踪）
_request_id_var = contextvars.ContextVar("request_id", default="-")

_FORMAT = logging.Formatter(
    "%(asctime)s [%(levelname)s] [rid=%(request_id)s] %(message)s",
    "%Y-%m-%d %H:%M:%S",
)


class _RequestIdFilter(logging.Filter):
    """把当前上下文里的 request_id 注入每条日志记录。"""

    def filter(self, record):
        record.request_id = _request_id_var.get()
        return True


def set_request_id(rid):
    """设置当前请求的 request_id（before_request 时调用）。"""
    _request_id_var.set(rid or "-")


def setup():
    """初始化日志器（幂等），返回 logger。"""
    logger = logging.getLogger("qinghe")
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    logger.addFilter(_RequestIdFilter())

    # 1) 控制台实时输出
    console = logging.StreamHandler()
    console.setFormatter(_FORMAT)
    logger.addHandler(console)

    # 2) 定时写盘：按天轮转（每天零点切新文件），保留 30 天
    log_dir = os.path.join(config.BASE_DIR, "logs")
    os.makedirs(log_dir, exist_ok=True)
    file_handler = TimedRotatingFileHandler(
        os.path.join(log_dir, "app.log"),
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8",
    )
    file_handler.setFormatter(_FORMAT)
    logger.addHandler(file_handler)

    logger.propagate = False  # 避免重复输出到根 logger
    return logger

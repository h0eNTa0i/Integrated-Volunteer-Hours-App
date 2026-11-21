#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""JWT 鉴权：签发/校验令牌 + @token_required 装饰器。"""
import datetime
import functools

import jwt
from flask import jsonify, request

import config


def create_token(user_id, role):
    """签发 access token。"""
    now = datetime.datetime.now(datetime.timezone.utc)
    payload = {
        "sub": str(user_id),
        "role": role,
        "iat": now,
        "exp": now + datetime.timedelta(minutes=config.JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)


def decode_token(token):
    return jwt.decode(token, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM])


def token_required(fn):
    """要求请求携带有效的 Bearer 令牌，把 user 注入 request.user。"""
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({"code": 40101, "message": "缺少认证令牌", "data": None}), 401
        token = auth[7:].strip()
        try:
            payload = decode_token(token)
        except jwt.ExpiredSignatureError:
            return jsonify({"code": 40102, "message": "令牌已过期", "data": None}), 401
        except jwt.InvalidTokenError:
            return jsonify({"code": 40103, "message": "令牌无效", "data": None}), 401
        request.user = {"id": int(payload["sub"]), "role": payload["role"]}
        return fn(*args, **kwargs)
    return wrapper

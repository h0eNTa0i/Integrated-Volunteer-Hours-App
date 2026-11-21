#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
青禾志愿 · 后端主应用

能力：
  - 静态托管 frontend/（index.html、data.json 等）
  - 鉴权：POST /auth/register、POST /auth/login、GET /auth/me
  - 报名：POST /activities/<id>/signups、DELETE /signups/<id>、
          GET /signups/mine、GET /activities/<id>/signups
  - 签到：POST /activities/<id>/checkins、POST /activities/<id>/checkouts、GET /checkins/mine
  - GET /api/v1/test-data  原型前端整包数据（活动来自数据库，其余为演示数据）
  - GET /api/v1/health     健康检查
  - 日志：控制台实时输出 + 按天写盘（logs/app.log）
  - CORS：flask-cors，允许跨域

数据库：users / activities / signups / checkins 四张表。
  - DB_ENGINE=mysql（默认）| sqlite（无 MySQL 时的零依赖兜底）。
统一响应包：{ code, message, data, requestId }
"""
import json
import re
import time
import uuid

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from werkzeug.security import check_password_hash, generate_password_hash

import auth
import config
import db
import logger

app = Flask(__name__, static_folder=None)
app.json.ensure_ascii = False

log = logger.setup()

# CORS（多端部署准备）
_origins = "*" if config.CORS_ORIGINS == "*" else [o.strip() for o in config.CORS_ORIGINS.split(",")]
CORS(app, resources={r"/api/*": {"origins": _origins}})

# 原型专属屏的演示数据（student/checkin/publisher/roster/admin 等，暂未映射真实表）
with open(config.DATA_FILE, "r", encoding="utf-8") as f:
    TEST_DATA = json.load(f)

_PHONE_RE = re.compile(r"^1\d{10}$")  # 中国大陆手机号

# 前端角色名 → 数据库 role 枚举（发布者端统一存 publisher_internal）
_ROLE_MAP = {
    "student": "student",
    "publisher": "publisher_internal",
    "publisher_internal": "publisher_internal",
    "admin": "admin",
}


# ---------------- 请求日志（控制台 + 写盘）+ 请求 ID 贯穿 ----------------
@app.before_request
def _log_before():
    if request.path.startswith("/api/"):
        # 生成请求 ID：优先透传客户端 X-Request-Id，否则新生成短 ID
        rid = request.headers.get("X-Request-Id") or uuid.uuid4().hex[:12]
        request._rid = rid
        logger.set_request_id(rid)
        request._t0 = time.time()
        log.info("→ %s %s", request.method, request.path)


@app.after_request
def _log_after(resp):
    if request.path.startswith("/api/"):
        dt = (time.time() - getattr(request, "_t0", time.time())) * 1000
        rid = getattr(request, "_rid", "-")
        resp.headers["X-Request-Id"] = rid
        log.info("← %s %s -> %s (%.1fms)", request.method, request.path, resp.status_code, dt)
    return resp


# ---------------- 响应工具 ----------------
def _current_rid():
    """当前请求的 requestId（贯穿响应体与日志）。"""
    return getattr(request, "_rid", None) or uuid.uuid4().hex[:12]


def _ok(data):
    return jsonify({"code": 0, "message": "ok", "data": data, "requestId": _current_rid()})


def _fail(code, message, http=200):
    return jsonify({"code": code, "message": message, "data": None, "requestId": _current_rid()}), http


def _user_payload(row):
    """把 users 表一行转成返回给前端的用户信息（不含密码）。"""
    return {
        "id": row["id"],
        "phone": row["phone"],
        "name": row.get("name"),
        "role": row["role"],
        "student_no": row.get("student_no"),
        "org": row.get("org"),
        "worker_no": row.get("worker_no"),
    }


def _parse_activity_id(raw):
    """兼容 'a1' 与 '1' 两种活动 id，返回数据库整数 id；非法返回 None。"""
    s = str(raw).strip()
    if s.lower().startswith("a"):
        s = s[1:]
    try:
        return int(s)
    except (ValueError, TypeError):
        return None


# ---------------- 注册 / 登录 ----------------
@app.post("/api/v1/auth/register")
def register():
    body = request.get_json(silent=True) or {}
    role = _ROLE_MAP.get((body.get("role") or "student").strip())
    phone = (body.get("phone") or "").strip()
    password = body.get("password") or ""
    name = (body.get("name") or "").strip()
    student_no = (body.get("student_no") or "").strip()
    org = (body.get("org") or "").strip()
    worker_no = (body.get("worker_no") or "").strip()

    if not role:
        return _fail(40006, "无效的角色")
    if not _PHONE_RE.fullmatch(phone):
        return _fail(40004, "手机号格式不正确（需 11 位）")
    if len(password) < 6:
        return _fail(40005, "密码至少 6 位")
    if role == "student" and not student_no:
        return _fail(40007, "请填写学号")
    if role == "publisher_internal" and not org:
        return _fail(40008, "请填写所属机构")
    if role == "admin":
        if not org:
            return _fail(40008, "请填写所属单位")
        if not worker_no:
            return _fail(40009, "请填写工号")

    if db.query_one("SELECT id FROM users WHERE phone = ?", (phone,)):
        return _fail(40003, "该手机号已注册")
    if student_no and db.query_one("SELECT id FROM users WHERE student_no = ?", (student_no,)):
        return _fail(40010, "该学号已注册")
    if worker_no and db.query_one("SELECT id FROM users WHERE worker_no = ?", (worker_no,)):
        return _fail(40011, "该工号已注册")

    password_hash = generate_password_hash(password)
    _, user_id = db.execute(
        "INSERT INTO users (phone, password_hash, name, role, student_no, org, worker_no) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (phone, password_hash, name or None, role, student_no or None, org or None, worker_no or None),
    )
    row = db.query_one(
        "SELECT id, phone, name, role, student_no, org, worker_no FROM users WHERE id = ?", (user_id,)
    )
    log.info("注册成功 user_id=%s role=%s", user_id, role)
    token = auth.create_token(row["id"], row["role"])
    return _ok({"token": token, "user": _user_payload(row)})


@app.post("/api/v1/auth/login")
def login():
    body = request.get_json(silent=True) or {}
    account = (body.get("account") or body.get("phone") or "").strip()
    password = body.get("password") or ""

    if not account:
        return _fail(40012, "请输入账号")

    row = db.query_one(
        "SELECT id, phone, password_hash, name, role, student_no, org, worker_no, status FROM users "
        "WHERE phone = ? OR student_no = ? OR worker_no = ?",
        (account, account, account),
    )
    if not row or not check_password_hash(row["password_hash"], password):
        return _fail(40001, "账号或密码错误")
    if row["status"] != "active":
        return _fail(40002, "账号已被禁用")

    log.info("登录成功 user_id=%s role=%s", row["id"], row["role"])
    token = auth.create_token(row["id"], row["role"])
    return _ok({"token": token, "user": _user_payload(row)})


@app.get("/api/v1/auth/me")
@auth.token_required
def me():
    row = db.query_one(
        "SELECT id, phone, name, role, student_no, org, worker_no FROM users WHERE id = ?",
        (request.user["id"],),
    )
    if not row:
        return _fail(40401, "用户不存在")
    return _ok(_user_payload(row))


# ---------------- 报名 ----------------
@app.post("/api/v1/activities/<activity_id>/signups")
@auth.token_required
def signup(activity_id):
    if request.user["role"] != "student":
        return _fail(40301, "仅学生可报名", http=403)
    aid = _parse_activity_id(activity_id)
    if aid is None:
        return _fail(40402, "活动不存在", http=404)
    uid = request.user["id"]

    act = db.query_one(
        "SELECT id, headcount, signed_count, status FROM activities WHERE id = ?", (aid,)
    )
    if not act:
        return _fail(40402, "活动不存在", http=404)
    if act["status"] == "full" or act["signed_count"] >= act["headcount"]:
        return _fail(11001, "名额已满，报名失败")

    existing = db.query_one("SELECT id, status FROM signups WHERE activity_id = ? AND user_id = ?", (aid, uid))
    if existing and existing["status"] == "active":
        return _fail(11002, "已报名，请勿重复报名")

    # 防超卖：原子扣减名额
    rowcount, _ = db.execute(
        "UPDATE activities SET signed_count = signed_count + 1 "
        "WHERE id = ? AND signed_count < headcount",
        (aid,),
    )
    if rowcount == 0:
        return _fail(11001, "名额已满，报名失败")

    if existing:
        # 之前取消过（软删除仍占 UNIQUE 约束），恢复为 active 实现「重新报名」
        db.execute("UPDATE signups SET status = 'active' WHERE id = ?", (existing["id"],))
        signup_id = existing["id"]
    else:
        try:
            _, signup_id = db.execute(
                "INSERT INTO signups (activity_id, user_id, status) VALUES (?, ?, ?)",
                (aid, uid, "active"),
            )
        except Exception:
            db.execute("UPDATE activities SET signed_count = signed_count - 1 WHERE id = ? AND signed_count > 0", (aid,))
            return _fail(11002, "报名失败（可能重复报名）")

    db.execute("UPDATE activities SET status = 'full' WHERE id = ? AND signed_count >= headcount", (aid,))
    log.info("报名成功 user_id=%s activity_id=%s signup_id=%s", uid, aid, signup_id)
    return _ok({"signupId": signup_id, "activityId": aid, "status": "active"})


@app.delete("/api/v1/signups/<int:signup_id>")
@auth.token_required
def cancel_signup(signup_id):
    uid = request.user["id"]
    s = db.query_one(
        "SELECT id, activity_id, status FROM signups WHERE id = ? AND user_id = ?", (signup_id, uid)
    )
    if not s:
        return _fail(40403, "报名记录不存在", http=404)
    if s["status"] != "active":
        return _fail(11004, "该报名已取消")

    db.execute("UPDATE signups SET status = 'cancelled' WHERE id = ?", (signup_id,))
    db.execute("UPDATE activities SET signed_count = signed_count - 1 WHERE id = ? AND signed_count > 0", (s["activity_id"],))
    db.execute("UPDATE activities SET status = 'recruiting' WHERE id = ? AND signed_count < headcount", (s["activity_id"],))
    log.info("取消报名 user_id=%s signup_id=%s", uid, signup_id)
    return _ok({"signupId": signup_id, "status": "cancelled"})


@app.get("/api/v1/signups/mine")
@auth.token_required
def my_signups():
    rows = db.query(
        "SELECT s.id AS signup_id, s.activity_id, s.status, s.created_at, "
        "a.name, a.location, a.time, a.hours, a.scope, a.category, a.gradient, a.date "
        "FROM signups s JOIN activities a ON a.id = s.activity_id "
        "WHERE s.user_id = ? AND s.status = 'active' ORDER BY s.id DESC",
        (request.user["id"],),
    )
    return _ok(rows)


@app.get("/api/v1/activities/<activity_id>/signups")
def activity_signups(activity_id):
    aid = _parse_activity_id(activity_id)
    if aid is None:
        return _fail(40402, "活动不存在", http=404)
    rows = db.query(
        "SELECT s.id AS signup_id, s.status, s.created_at, u.name, u.student_no, u.phone "
        "FROM signups s JOIN users u ON u.id = s.user_id "
        "WHERE s.activity_id = ? ORDER BY s.id",
        (aid,),
    )
    return _ok(rows)


# ---------------- 签到 / 签退 ----------------
@app.post("/api/v1/activities/<activity_id>/checkins")
@auth.token_required
def checkin(activity_id):
    aid = _parse_activity_id(activity_id)
    if aid is None:
        return _fail(40402, "活动不存在", http=404)
    uid = request.user["id"]

    s = db.query_one(
        "SELECT id FROM signups WHERE activity_id = ? AND user_id = ? AND status = 'active'", (aid, uid)
    )
    if not s:
        return _fail(12001, "请先报名该活动")

    if db.query_one("SELECT id FROM checkins WHERE activity_id = ? AND user_id = ? AND type = 'checkin'", (aid, uid)):
        return _fail(12002, "已签到，请勿重复签到")
    try:
        _, cid = db.execute(
            "INSERT INTO checkins (activity_id, user_id, signup_id, type) VALUES (?, ?, ?, ?)",
            (aid, uid, s["id"], "checkin"),
        )
    except Exception:
        return _fail(12002, "已签到，请勿重复签到")

    log.info("签到成功 user_id=%s activity_id=%s", uid, aid)
    return _ok({"checkinId": cid, "type": "checkin"})


@app.post("/api/v1/activities/<activity_id>/checkouts")
@auth.token_required
def checkout(activity_id):
    aid = _parse_activity_id(activity_id)
    if aid is None:
        return _fail(40402, "活动不存在", http=404)
    uid = request.user["id"]

    s = db.query_one(
        "SELECT id FROM signups WHERE activity_id = ? AND user_id = ? AND status = 'active'", (aid, uid)
    )
    if not s:
        return _fail(12001, "请先报名该活动")

    if db.query_one("SELECT id FROM checkins WHERE activity_id = ? AND user_id = ? AND type = 'checkout'", (aid, uid)):
        return _fail(12003, "已签退，请勿重复签退")
    try:
        _, cid = db.execute(
            "INSERT INTO checkins (activity_id, user_id, signup_id, type) VALUES (?, ?, ?, ?)",
            (aid, uid, s["id"], "checkout"),
        )
    except Exception:
        return _fail(12003, "已签退，请勿重复签退")

    log.info("签退成功 user_id=%s activity_id=%s", uid, aid)
    _ensure_hours(aid, uid, s["id"])
    return _ok({"checkinId": cid, "type": "checkout", "hours": _activity_hours(aid)})


@app.get("/api/v1/checkins/mine")
@auth.token_required
def my_checkins():
    rows = db.query(
        "SELECT c.id, c.activity_id, c.type, c.check_time, a.name "
        "FROM checkins c JOIN activities a ON a.id = c.activity_id "
        "WHERE c.user_id = ? ORDER BY c.id DESC",
        (request.user["id"],),
    )
    return _ok(rows)


# ---------------- 时长认定 ----------------
def _activity_hours(aid):
    act = db.query_one("SELECT hours FROM activities WHERE id = ?", (aid,))
    try:
        return float(act["hours"]) if act and act.get("hours") else 0.0
    except (TypeError, ValueError):
        return 0.0


def _ensure_hours(aid, uid, signup_id):
    """签退后自动生成一条待认定时长记录（幂等）。"""
    if db.query_one("SELECT id FROM volunteer_hours WHERE activity_id = ? AND user_id = ?", (aid, uid)):
        return
    h = _activity_hours(aid)
    db.execute(
        "INSERT INTO volunteer_hours (activity_id, user_id, signup_id, hours, status) VALUES (?, ?, ?, ?, ?)",
        (aid, uid, signup_id, h, "pending"),
    )
    log.info("生成待认定时长 user_id=%s activity_id=%s hours=%s", uid, aid, h)


@app.get("/api/v1/hours/mine")
@auth.token_required
def my_hours():
    rows = db.query(
        "SELECT h.id, h.activity_id, h.hours, h.status, h.verified_at, h.created_at, a.name "
        "FROM volunteer_hours h JOIN activities a ON a.id = h.activity_id "
        "WHERE h.user_id = ? ORDER BY h.id DESC",
        (request.user["id"],),
    )
    return _ok(rows)


@app.get("/api/v1/hours/pending")
@auth.token_required
def hours_pending():
    if request.user["role"] != "admin":
        return _fail(40301, "仅校方可操作", http=403)
    rows = db.query(
        "SELECT h.id, h.activity_id, h.hours, h.status, h.created_at, "
        "u.name, u.student_no, a.name AS activity_name "
        "FROM volunteer_hours h "
        "JOIN users u ON u.id = h.user_id "
        "JOIN activities a ON a.id = h.activity_id "
        "WHERE h.status = 'pending' ORDER BY h.id DESC"
    )
    return _ok(rows)


@app.post("/api/v1/hours/<int:hours_id>/verify")
@auth.token_required
def hours_verify(hours_id):
    if request.user["role"] != "admin":
        return _fail(40301, "仅校方可操作", http=403)
    h = db.query_one("SELECT id FROM volunteer_hours WHERE id = ?", (hours_id,))
    if not h:
        return _fail(40404, "时长记录不存在", http=404)
    db.execute(
        "UPDATE volunteer_hours SET status = 'verified', verified_by = ?, verified_at = ? WHERE id = ?",
        (request.user["id"], time.strftime("%Y-%m-%d %H:%M:%S"), hours_id),
    )
    log.info("时长认定通过 hours_id=%s by=%s", hours_id, request.user["id"])
    return _ok({"hoursId": hours_id, "status": "verified"})


@app.post("/api/v1/hours/<int:hours_id>/reject")
@auth.token_required
def hours_reject(hours_id):
    if request.user["role"] != "admin":
        return _fail(40301, "仅校方可操作", http=403)
    h = db.query_one("SELECT id FROM volunteer_hours WHERE id = ?", (hours_id,))
    if not h:
        return _fail(40404, "时长记录不存在", http=404)
    db.execute(
        "UPDATE volunteer_hours SET status = 'rejected', verified_by = ?, verified_at = ? WHERE id = ?",
        (request.user["id"], time.strftime("%Y-%m-%d %H:%M:%S"), hours_id),
    )
    log.info("时长驳回 hours_id=%s by=%s", hours_id, request.user["id"])
    return _ok({"hoursId": hours_id, "status": "rejected"})


# ---------------- 证书 ----------------
def _make_cert_no():
    return "QH-" + time.strftime("%Y") + "-" + uuid.uuid4().hex[:8].upper()


@app.post("/api/v1/certificates")
@auth.token_required
def create_certificate():
    body = request.get_json(silent=True) or {}
    ctype = body.get("type") or "single"
    hours_id = body.get("hours_id")
    uid = request.user["id"]

    if ctype == "single":
        h = db.query_one(
            "SELECT h.id, h.hours, h.activity_id, h.status "
            "FROM volunteer_hours h WHERE h.id = ? AND h.user_id = ?",
            (hours_id, uid),
        )
        if not h:
            return _fail(40404, "时长记录不存在", http=404)
        if h["status"] != "verified":
            return _fail(13001, "该时长尚未认定，无法生成证书")
        cert_hours = float(h["hours"])
        activity_id = h["activity_id"]
    elif ctype == "total":
        row = db.query_one(
            "SELECT COALESCE(SUM(hours), 0) AS total FROM volunteer_hours "
            "WHERE user_id = ? AND status = 'verified'",
            (uid,),
        )
        cert_hours = float(row["total"]) if row else 0.0
        activity_id = None
    else:
        return _fail(40013, "无效的证书类型")

    cert_no = _make_cert_no()
    qr_token = uuid.uuid4().hex
    issuer = "青禾大学团委"
    _, cid = db.execute(
        "INSERT INTO certificates (user_id, activity_id, type, cert_no, qr_token, hours, issuer, pdf_url) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (uid, activity_id, ctype, cert_no, qr_token, cert_hours, issuer, ""),
    )
    log.info("生成证书 cert_id=%s cert_no=%s user_id=%s", cid, cert_no, uid)
    return _ok({"certificateId": cid, "certNo": cert_no, "hours": cert_hours, "type": ctype})


@app.get("/api/v1/certificates/mine")
@auth.token_required
def my_certificates():
    rows = db.query(
        "SELECT c.id, c.type, c.cert_no, c.hours, c.issuer, c.pdf_url, c.created_at, a.name AS activity_name "
        "FROM certificates c LEFT JOIN activities a ON a.id = c.activity_id "
        "WHERE c.user_id = ? ORDER BY c.id DESC",
        (request.user["id"],),
    )
    return _ok(rows)


@app.get("/api/v1/verify")
def verify_certificate():
    cert_no = (request.args.get("certNo") or "").strip()
    if not cert_no:
        return _fail(40014, "请提供证书编号")
    c = db.query_one(
        "SELECT c.cert_no, c.hours, c.type, c.issuer, c.created_at, u.name "
        "FROM certificates c JOIN users u ON u.id = c.user_id "
        "WHERE c.cert_no = ?",
        (cert_no,),
    )
    if not c:
        return _fail(40405, "证书不存在", http=404)
    return _ok({
        "valid": True,
        "certNo": c["cert_no"],
        "hours": c["hours"],
        "type": c["type"],
        "issuer": c["issuer"],
        "holder": c["name"],
        "issuedAt": c["created_at"],
    })


# ---------------- 申诉 ----------------
@app.post("/api/v1/appeals")
@auth.token_required
def create_appeal():
    body = request.get_json(silent=True) or {}
    hours_id = body.get("hours_id")
    reason = (body.get("reason") or "").strip()
    if not hours_id:
        return _fail(40015, "请指定时长记录")
    if not reason:
        return _fail(40016, "请填写申诉理由")
    uid = request.user["id"]
    h = db.query_one("SELECT id, status FROM volunteer_hours WHERE id = ? AND user_id = ?", (hours_id, uid))
    if not h:
        return _fail(40404, "时长记录不存在", http=404)
    if db.query_one("SELECT id FROM appeals WHERE hours_id = ? AND status = 'pending'", (hours_id,)):
        return _fail(14001, "该时长已有待处理申诉")
    _, apid = db.execute(
        "INSERT INTO appeals (hours_id, user_id, reason, status) VALUES (?, ?, ?, ?)",
        (hours_id, uid, reason, "pending"),
    )
    db.execute("UPDATE volunteer_hours SET status = 'appealing' WHERE id = ?", (hours_id,))
    log.info("提交申诉 appeal_id=%s hours_id=%s user_id=%s", apid, hours_id, uid)
    return _ok({"appealId": apid, "status": "pending"})


@app.get("/api/v1/appeals/mine")
@auth.token_required
def my_appeals():
    rows = db.query(
        "SELECT ap.id, ap.hours_id, ap.reason, ap.status, ap.created_at, h.hours, a.name AS activity_name "
        "FROM appeals ap JOIN volunteer_hours h ON h.id = ap.hours_id "
        "JOIN activities a ON a.id = h.activity_id "
        "WHERE ap.user_id = ? ORDER BY ap.id DESC",
        (request.user["id"],),
    )
    return _ok(rows)


@app.get("/api/v1/appeals/pending")
@auth.token_required
def appeals_pending():
    if request.user["role"] != "admin":
        return _fail(40301, "仅校方可操作", http=403)
    rows = db.query(
        "SELECT ap.id, ap.hours_id, ap.reason, ap.created_at, h.hours, u.name, a.name AS activity_name "
        "FROM appeals ap JOIN volunteer_hours h ON h.id = ap.hours_id "
        "JOIN users u ON u.id = ap.user_id JOIN activities a ON a.id = h.activity_id "
        "WHERE ap.status = 'pending' ORDER BY ap.id DESC"
    )
    return _ok(rows)


@app.post("/api/v1/appeals/<int:appeal_id>/resolve")
@auth.token_required
def resolve_appeal(appeal_id):
    if request.user["role"] != "admin":
        return _fail(40301, "仅校方可操作", http=403)
    body = request.get_json(silent=True) or {}
    action = body.get("action") or "reject"  # approve / reject
    ap = db.query_one("SELECT id, hours_id, status FROM appeals WHERE id = ?", (appeal_id,))
    if not ap:
        return _fail(40406, "申诉不存在", http=404)
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    if action == "approve":
        db.execute("UPDATE appeals SET status = 'resolved', handled_by = ?, handled_at = ? WHERE id = ?",
                   (request.user["id"], now, appeal_id))
        db.execute("UPDATE volunteer_hours SET status = 'verified', verified_by = ?, verified_at = ? WHERE id = ?",
                   (request.user["id"], now, ap["hours_id"]))
    else:
        db.execute("UPDATE appeals SET status = 'rejected', handled_by = ?, handled_at = ? WHERE id = ?",
                   (request.user["id"], now, appeal_id))
        db.execute("UPDATE volunteer_hours SET status = 'rejected' WHERE id = ?", (ap["hours_id"],))
    log.info("处理申诉 appeal_id=%s action=%s by=%s", appeal_id, action, request.user["id"])
    return _ok({"appealId": appeal_id, "status": "resolved" if action == "approve" else "rejected"})


# ---------------- 数据与静态 ----------------
def _demo_activities():
    rows = db.query("SELECT * FROM activities ORDER BY id")
    return [
        {
            "id": "a" + str(r["id"]),
            "title": r["name"],
            "org": r["org"],
            "scope": r["scope"],
            "category": r["category"],
            "date": r["date"],
            "hours": r["hours"],
            "recruit": r["headcount"],
            "signed": r["signed_count"],
            "time": r["time"],
            "location": r["location"],
            "gradient": r["gradient"],
            "badge": {"label": r["badge"]},
            "full": r["signed_count"] >= r["headcount"],
        }
        for r in rows
    ]


@app.get("/api/v1/test-data")
def get_test_data():
    """原型前端整包数据：活动来自数据库，其余为演示数据。"""
    data = json.loads(json.dumps(TEST_DATA))  # 深拷贝，避免污染缓存
    data["activities"] = _demo_activities()
    return _ok(data)


@app.get("/api/v1/health")
def health():
    return _ok({"status": "up", "engine": config.DB_ENGINE})


@app.get("/")
def index():
    return send_from_directory(config.FRONTEND_DIR, "index.html")


@app.get("/<path:filename>")
def static_files(filename):
    return send_from_directory(config.FRONTEND_DIR, filename)


if __name__ == "__main__":
    db.init_db()
    log.info("青禾志愿后端启动 DB=%s 端口=%s", config.DB_ENGINE, config.PORT)
    app.run(host="127.0.0.1", port=config.PORT, debug=False)

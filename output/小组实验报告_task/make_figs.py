# -*- coding: utf-8 -*-
"""生成《软件工程》项目报告插图（青禾志愿 志愿时长 App）。"""
import os
from diaglib import (Canvas, f, BLUE, PURPLE, DARK, GRAY, LINE, LIGHT_BLUE,
                     LIGHT_PURPLE, LIGHT_GRAY, WHITE, GREEN, ORANGE, wrap)

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "figs")
os.makedirs(FIG, exist_ok=True)


def save(c, name):
    p = os.path.join(FIG, name)
    c.save(p)
    print("saved", name)


# ---------- 图1-1 系统总体功能模块结构图 ----------
def fig_modules():
    c = Canvas(920, 470)
    c.node((280, 18, 640, 74), "青禾志愿 · 志愿时长认证与活动管理平台",
           fill=PURPLE, outline=PURPLE, tcolor=WHITE, size=16)
    cols = [(28, "学生端", BLUE, LIGHT_BLUE, ["浏览 / 筛选活动", "一键报名与候补", "GPS+二维码签到签退", "时长明细与申诉", "证书导出与核验"]),
            (330, "发布者端", PURPLE, LIGHT_PURPLE, ["发布志愿招募", "报名名单管理", "现场核销签到", "批量时长 / 证书", "数据导出上报"]),
            (632, "校方端", GREEN, "#ECFDF5", ["招募认可审核", "志愿时长认定", "证书落款模板", "全校数据看板", "审计日志追溯"])]
    for x, title, col, lite, items in cols:
        c.node((x, 130, x + 260, 172), title, fill=col, outline=col, tcolor=WHITE, size=18)
        c.arrow((460, 74), (x + 130, 128), fill=LINE, width=2)
        yy = 184
        for it in items:
            c.rect((x, yy, x + 260, yy + 42), fill=lite, outline=col, width=1, radius=8)
            c.text((x + 16, yy + 21), "• " + it, 14, DARK, anchor="lm")
            yy += 52
    save(c, "fig1_1_modules.png")


# ---------- 图1-2 项目进度甘特图 ----------
def fig_gantt():
    c = Canvas(920, 470, scale=2)
    weeks = ["第1周", "第2周", "第3周", "第4周", "第5周", "第6周", "第7周", "第8周"]
    x0, y0 = 250, 90
    cw, rh = 78, 38
    # 表头
    c.rect((20, 20, 900, y0 - 4), fill=LIGHT_GRAY, outline=LINE, width=1, radius=4)
    c.text((30, (20 + y0 - 4) / 2), "阶段 / 任务", 16, DARK, True, anchor="lm")
    for i, w in enumerate(weeks):
        c.text((x0 + i * cw + cw / 2, (20 + y0 - 4) / 2), w, 14, GRAY, anchor="mm")
    tasks = [
        ("需求调研与NABCD分析", 0, 2, BLUE),
        ("原型设计与需求评审", 1, 3, PURPLE),
        ("架构与数据库设计", 2, 2, BLUE),
        ("后端接口开发", 3, 4, GREEN),
        ("前端页面联调", 4, 3, PURPLE),
        ("功能测试与修复", 5, 3, ORANGE),
        ("部署发布与用户反馈", 6, 2, GREEN),
        ("报告撰写与答辩准备", 6, 2, BLUE),
    ]
    y = y0
    for name, start, dur, col in tasks:
        c.text((30, y + rh / 2), name, 15, DARK, anchor="lm")
        c.rect((x0 + start * cw + 3, y + 7, x0 + (start + dur) * cw - 3, y + rh - 7),
               fill=col, outline=col, radius=6)
        c.line((x0, y + rh, x0 + len(weeks) * cw, y + rh), fill="#E5E7EB", width=1)
        y += rh
    save(c, "fig1_2_gantt.png")


# ---------- 图2-1 用例图 ----------
def fig_usecase():
    c = Canvas(920, 470)
    # 系统边界
    c.rect((250, 40, 760, 430), fill=WHITE, outline=LINE, width=2, radius=24)
    c.text((505, 60), "志愿时长认证与活动管理系统", 16, GRAY, anchor="mm")
    # 三个角色
    actors = [(120, "学生", BLUE), (860, "发布者", PURPLE), (505, "校方管理员", GREEN)]
    for x, name, col in actors:
        c.node((x - 55, 200, x + 55, 246), name, fill=col, outline=col, tcolor=WHITE, size=16)
    cases = [
        (300, 100, "浏览/报名活动"),
        (300, 175, "签到签退"),
        (300, 250, "时长明细/申诉"),
        (300, 325, "证书导出"),
        (560, 100, "发布招募"),
        (560, 175, "名单/核销管理"),
        (560, 250, "批量时长证书"),
        (560, 325, "导出上报"),
    ]
    for x, y, t in cases:
        c.rect((x, y, x + 150, y + 38), fill=LIGHT_BLUE if x < 500 else LIGHT_PURPLE,
               outline=BLUE if x < 500 else PURPLE, width=1, radius=18)
        c.text_center(x + 75, y + 19, t, 13, DARK)
    # 连线
    for y in [119, 194, 269, 344]:
        c.line([(175, 223), (235, 223), (235, y), (298, y)], fill=BLUE, width=1)
    for y in [119, 194, 269, 344]:
        c.line([(805, 223), (835, 223), (835, y), (712, y)], fill=PURPLE, width=1)
    for y in [119, 194, 269, 344]:
        c.arrow((505, 246), (505 if 505 in range(300, 450) else 635, y + 19), fill=GREEN, width=1)
    save(c, "fig2_1_usecase.png")


# ---------- 图2-2 报名→签到→时长→证明 核心闭环 ----------
def fig_flow():
    c = Canvas(920, 300)
    steps = [("报名", "学籍字段自动带出\n30秒完成", BLUE, LIGHT_BLUE),
             ("签到签退", "GPS+动态二维码\n防代签", PURPLE, LIGHT_PURPLE),
             ("时长认定", "签退自动计时\n校方审核溯源", GREEN, "#ECFDF5"),
             ("证书证明", "PDF一键导出\n唯一编号核验", ORANGE, "#FEF3C7")]
    x = 30
    for i, (t, s, col, lite) in enumerate(steps):
        c.node((x, 70, x + 190, 190), t, sub=s, fill=lite, outline=col, tcolor=col, size=20, subsize=13)
        # 序号
        c.rect((x + 78, 30, x + 112, 64), fill=col, outline=col, radius=17)
        c.text_center(x + 95, 47, str(i + 1), 18, WHITE, True)
        if i < 3:
            c.arrow((x + 192, 130), (x + 218, 130), fill=LINE, width=3, head=11)
        x += 228
    c.text((460, 275), "四道信任壁垒：双签到防作弊 · 时长可溯源 · 证书唯一可核验 · 审计不可篡改", 13, GRAY, anchor="mm")
    save(c, "fig2_2_flow.png")


# ---------- 图3-1 系统分层架构图 ----------
def fig_arch():
    c = Canvas(920, 540)
    layers = [
        (30, "表现层 · 三端 Web 原型", BLUE, LIGHT_BLUE, "学生端 / 发布者端 / 校方端（HTML + JavaScript 单页应用）"),
        (140, "接入层 · API 网关", PURPLE, LIGHT_PURPLE, "Flask 路由 / flask-cors 跨域 / JWT Bearer 鉴权 / 统一响应包 {code,message,data,requestId}"),
        (250, "业务层 · 模块化单体", BLUE, LIGHT_BLUE, "认证 · 活动 · 报名 · 签到 · 时长 · 证书 · 申诉 七大模块（按领域拆分，演进为微服务）"),
        (360, "数据访问层 · db.py", GREEN, "#ECFDF5", "统一 CRUD 封装 / SQL 占位符自动转义 / 双引擎适配（MySQL ⇄ SQLite）"),
        (470, "存储层", ORANGE, "#FEF3C7", "MySQL 8.0（主库）：users / activities / signups / checkins / volunteer_hours / appeals / certificates"),
    ]
    for y, title, col, lite, desc in layers:
        c.node((90, y, 830, y + 88), "", fill=lite, outline=col, tcolor=DARK)
        c.text((110, y + 26), title, 17, col, True, anchor="lm")
        c.text((110, y + 60), desc, 13, DARK, anchor="lm")
        if y < 470:
            c.arrow((460, y + 89), (460, y + 118), fill=LINE, width=2, head=8)
    save(c, "fig3_1_arch.png")


# ---------- 图3-2 核心类图 ----------
def fig_class():
    c = Canvas(920, 560)
    classes = [
        (40, 60, "User 用户", ["+id: BIGINT", "+phone: VARCHAR", "+password_hash", "+role: ENUM", "+student_no", "+org / worker_no", "+status: ENUM"], BLUE, LIGHT_BLUE),
        (360, 60, "Activity 活动", ["+id: BIGINT", "+name: VARCHAR", "+org: VARCHAR", "+date / time / location", "+hours: DECIMAL", "+headcount / signed_count", "+status: ENUM"], PURPLE, LIGHT_PURPLE),
        (680, 60, "Signup 报名", ["+id: BIGINT", "+activity_id: FK", "+user_id: FK", "+status: ENUM", "+created_at"], GREEN, "#ECFDF5"),
        (40, 320, "Checkin 签到", ["+id: BIGINT", "+activity_id: FK", "+user_id: FK", "+signup_id: FK", "+type: checkin/checkout", "+check_time"], ORANGE, "#FEF3C7"),
        (360, 320, "VolunteerHours 时长", ["+id: BIGINT", "+activity_id: FK", "+user_id: FK", "+hours: DECIMAL", "+status: pending/verified", "+verified_by / verified_at"], BLUE, LIGHT_BLUE),
        (680, 320, "Certificate 证书", ["+id: BIGINT", "+user_id: FK", "+cert_no: UNIQUE", "+qr_token: UNIQUE", "+hours / issuer", "+pdf_url"], PURPLE, LIGHT_PURPLE),
    ]
    for x, y, title, attrs, col, lite in classes:
        c.rect((x, y, x + 220, y + 190), fill=lite, outline=col, width=2, radius=6)
        c.rect((x, y, x + 220, y + 34), fill=col, outline=col, radius=6)
        c.text_center(x + 110, y + 17, title, 15, WHITE, True)
        yy = y + 48
        for a in attrs:
            c.text((x + 12, yy), a, 12, DARK, anchor="lm")
            yy += 20
    c.arrow((260, 130), (358, 130), fill=LINE, width=2)
    c.arrow((580, 130), (678, 130), fill=LINE, width=2)
    c.arrow((150, 250), (150, 318), fill=LINE, width=2)
    c.arrow((470, 250), (470, 318), fill=LINE, width=2)
    c.arrow((580, 380), (678, 380), fill=LINE, width=2)
    save(c, "fig3_2_class.png")


# ---------- 图3-3 数据库 E-R 图 ----------
def fig_er():
    c = Canvas(920, 500)
    entities = [
        (40, 60, "用户 User", BLUE, LIGHT_BLUE),
        (370, 60, "活动 Activity", PURPLE, LIGHT_PURPLE),
        (700, 60, "报名 Signup", GREEN, "#ECFDF5"),
        (40, 300, "签到 Checkin", ORANGE, "#FEF3C7"),
        (370, 300, "志愿时长 Hours", BLUE, LIGHT_BLUE),
        (700, 300, "证书 Certificate", PURPLE, LIGHT_PURPLE),
    ]
    for x, y, t, col, lite in entities:
        c.node((x, y, x + 180, y + 60), t, fill=lite, outline=col, tcolor=col, size=16)
    c.line([(220, 90), (368, 90)], fill=LINE, width=2)
    c.text_center(294, 78, "1 : n 发布/参与", 11, GRAY)
    c.line([(550, 90), (698, 90)], fill=LINE, width=2)
    c.text_center(624, 78, "1 : n", 11, GRAY)
    c.line([(130, 120), (130, 298)], fill=LINE, width=2)
    c.text_center(190, 210, "1 : n", 11, GRAY)
    c.line([(460, 120), (460, 298)], fill=LINE, width=2)
    c.text_center(520, 210, "1 : 1", 11, GRAY)
    c.line([(790, 120), (790, 298)], fill=LINE, width=2)
    c.text_center(850, 210, "1 : n", 11, GRAY)
    c.line([(220, 330), (368, 330)], fill=LINE, width=2)
    c.text_center(294, 318, "溯源 n : 1", 11, GRAY)
    save(c, "fig3_3_er.png")


# ---------- 图4-1 关键算法：签到幂等 + 时长认定流程 ----------
def fig_algo():
    c = Canvas(920, 430)
    steps = [
        (30, "用户签退请求", BLUE, LIGHT_BLUE),
        (250, "校验报名状态\n(active)", BLUE, LIGHT_BLUE),
        (470, "查重：是否已\n签到/签退", PURPLE, LIGHT_PURPLE),
        (690, "写入 checkins\n唯一约束防重", GREEN, "#ECFDF5"),
    ]
    for x, t, col, lite in steps:
        c.node((x, 60, x + 180, 140), t, fill=lite, outline=col, tcolor=DARK, size=14)
    for x in [210, 430, 650]:
        c.arrow((x, 100), (x + 38, 100), fill=LINE, width=2)
    # 第二行
    steps2 = [
        (690, "_ensure_hours\n幂等生成时长", BLUE, LIGHT_BLUE),
        (470, "状态=pending\n校方待认定", PURPLE, LIGHT_PURPLE),
        (250, "verify/reject\n认定或驳回", GREEN, "#ECFDF5"),
        (30, "certificates\n唯一编号入库", ORANGE, "#FEF3C7"),
    ]
    for x, t, col, lite in steps2:
        c.node((x, 250, x + 180, 330), t, fill=lite, outline=col, tcolor=DARK, size=14)
    for x in [690, 470, 250]:
        c.arrow((x + 90, 142), (x + 90, 246), fill=LINE, width=2)
    for x in [690, 470, 250]:
        c.arrow((x, 290), (x - 38, 290), fill=LINE, width=2)
    c.text((460, 412), "说明：以(activity_id,user_id,type)建唯一索引，重复签退返回12003，避免时长重复累加。", 12, GRAY, anchor="mm")
    save(c, "fig4_1_algo.png")


# ---------- 图2-3 数据流图（顶层 + 0层） ----------
def fig_dfd():
    c = Canvas(920, 500)
    c.text((460, 28), "顶层数据流图（上下文图）", 16, DARK, True, anchor="mm")
    # 外部实体
    ext = [(60, "学生", BLUE), (400, "发布者", PURPLE), (740, "校方管理员", GREEN)]
    for x, name, col in ext:
        c.node((x - 55, 70, x + 55, 116), name, fill=col, outline=col, tcolor=WHITE, size=16)
    # 中心系统
    c.node((330, 170, 590, 250), "青禾志愿系统", sub="活动/报名/签到/时长/证书", fill=LIGHT_BLUE, outline=BLUE, tcolor=BLUE, size=18, subsize=12)
    flows = [
        (115, 116, 345, 188, "报名/签到/查时长/下载证书"),
        (455, 116, 460, 200, "发布活动/核销/批量登记"),
        (795, 116, 575, 188, "审核/认定时长/落款"),
    ]
    for x1, y1, x2, y2, label in flows:
        c.arrow((x1, y1), (x2, y2), fill=LINE, width=2)
    c.text((460, 300), "第二层：关键数据流（学生报名→签到签退→时长生成→认定→证书核验）", 13, GRAY, anchor="mm")
    # 0层核心数据流
    stores = ["报名表 signups", "签到表 checkins", "时长表 volunteer_hours", "证书表 certificates"]
    boxes = [("1. 报名", "学生→提交报名\n写入 signups", BLUE, LIGHT_BLUE),
             ("2. 签到/签退", "校验报名→写 checkins\n签退触发时长", PURPLE, LIGHT_PURPLE),
             ("3. 时长生成", "_ensure_hours\n幂等生成 pending", GREEN, "#ECFDF5"),
             ("4. 认定与证书", "verify→certificates\n唯一编号入库", ORANGE, "#FEF3C7")]
    x = 30
    for t, s, col, lite in boxes:
        c.node((x, 340, x + 190, 430), t, sub=s, fill=lite, outline=col, tcolor=col, size=15, subsize=11)
        if x > 30:
            c.arrow((x - 10, 385), (x, 385), fill=LINE, width=2)
        x += 228
    c.text((460, 470), "数据存储：MySQL（主）+ SQLite（兜底），统一经 db.py 访问", 12, GRAY, anchor="mm")
    save(c, "fig2_3_dfd.png")


# ---------- 图4-2 关键函数调用关系图 ----------
def fig_funcs():
    c = Canvas(920, 520)
    # 控制器层（Flask 路由）
    c.text((460, 26), "控制层（Flask 路由）", 15, DARK, True, anchor="mm")
    controllers = ["register / login", "signup / cancel", "checkin / checkout", "hours_verify", "create_certificate", "create_appeal"]
    cx = 40
    for t in controllers:
        c.node((cx, 48, cx + 130, 88), t, fill=LIGHT_BLUE, outline=BLUE, tcolor=DARK, size=12)
        cx += 148
    c.text((460, 118), "业务/工具函数", 15, DARK, True, anchor="mm")
    utils = [
        (40, "_ensure_hours", "幂等生成时长", BLUE),
        (250, "_make_cert_no", "证书唯一编号", PURPLE),
        (460, "auth.create_token", "JWT 签发", GREEN),
        (670, "auth.token_required", "鉴权装饰器", ORANGE),
    ]
    for x, t, s, col in utils:
        c.node((x, 140, x + 180, 200), t, sub=s, fill=WHITE, outline=col, tcolor=col, size=14, subsize=11)
    # 数据访问层
    c.text((460, 232), "数据访问层（db.py）", 15, DARK, True, anchor="mm")
    dal = ["query(sql,args)", "execute(sql,args)", "query_one(sql,args)", "get_conn()"]
    dx = 60
    for t in dal:
        c.node((dx, 254, dx + 190, 294), t, fill=LIGHT_GRAY, outline=LINE, tcolor=DARK, size=12)
        dx += 210
    c.text((460, 322), "存储层（MySQL / SQLite 双引擎，经 _translate 自动转义占位符）", 13, GRAY, anchor="mm")
    c.node((110, 340, 810, 384), "users · activities · signups · checkins · volunteer_hours · appeals · certificates（共 7 张表）",
           fill="#FEF3C7", outline=ORANGE, tcolor=DARK, size=13)
    # 连线（示意主要调用）
    edges = [
        ((105, 88), (130, 138), "签退→"),
        ((253, 88), (340, 138), "认证→"),
        ((401, 88), (460, 138), "签发→"),
        ((549, 88), (670, 138), "校验→"),
        ((130, 200), (105, 252), "时长→"),
        ((340, 200), (340, 252), "查询→"),
        ((460, 200), (460, 252), "查询→"),
        ((670, 200), (670, 252), "查询→"),
    ]
    for p1, p2, lbl in edges:
        c.arrow(p1, p2, fill=LINE, width=1)
    c.text((460, 450), "调用关系：路由 → 业务/工具函数 → db.py 统一 CRUD → 存储引擎；鉴权装饰器横切所有受保护接口", 12, GRAY, anchor="mm")
    save(c, "fig4_2_funcs.png")


if __name__ == "__main__":
    fig_modules()
    fig_gantt()
    fig_usecase()
    fig_flow()
    fig_dfd()
    fig_arch()
    fig_class()
    fig_er()
    fig_algo()
    fig_funcs()
    print("all figures generated")

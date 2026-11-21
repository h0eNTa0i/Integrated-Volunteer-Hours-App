# 数据库表结构设计

**日期**：2026-10-23
**类型**：数据库设计（PRD v1.5 配套）
**关联文档**：`prd-volunteer-certification-2026-10-16.md`（v1.5）、`role-permission-matrix-2026-10-23.md`

> 类型采用通用 SQL 约定（参考 MySQL）。`BIGINT` 主键、`DATETIME` 时间、`ENUM` 枚举、`JSON` 结构化字段、`DECIMAL` 精度数值。以下为 v1.0a（MVP）核心表，P1/P2 表以「扩展」标注。

---

## 1. 设计原则

1. **账号与角色分离**：`users` 存账号/登录，`students`（学生档案）、`publishers`（发布者认证）作为角色扩展表，支持一人多角色（如学生干部既是学生又是发布者）。
2. **认证与认可分离**：`publishers.verified_status`（发布者身份认证）与 `activity_approvals`（招募的校内认可）是两个独立关卡。
3. **时长可溯源**：`volunteer_hours` 通过 `activity_id → signup → checkin` 形成完整证据链（对应 R14 溯源）。
4. **编辑留痕**：`activity_edit_logs` 记录字段级 `old_value → new_value`，不可篡改（对应 R24/R31 审计）。
5. **软删除与留痕**：活动取消不物理删除，改状态为 `cancelled`（对应 R26）。

---

## 2. ER 关系总览

```
schools 1 ──── n students          (学生属于学校)
schools 1 ──── n organizations     (校内组织属于学校；校外机构 school_id 为空)
users   1 ──── 1 students          (账号 → 学生档案)
users   1 ──── 1 publishers        (账号 → 发布者认证)
organizations 1 ─ n publishers     (发布者归属组织/机构)

publishers 1 ─ n activities        (发布者发布活动)
organizations 1 ─ n activities     (活动归属组织)
activities 1 ─ n activity_positions (活动含多个岗位)
activities 1 ─ n activity_approvals (活动认可审核记录)
activities 1 ─ n activity_edit_logs  (活动编辑审计)
activities 1 ─ n signups           (活动被报名)
activities 1 ─ n checkins          (活动签到记录)

signups 1 ─ n checkins             (一次报名对应签到/签退)
signups 1 ─ 1 volunteer_hours      (一次报名对应一条时长)
activities 1 ─ n volunteer_hours   (活动维度汇总)
volunteer_hours 1 ─ n appeals      (时长申诉)
students 1 ─ n certificates        (学生证书)
students 1 ─ n signups             (学生报名)
users 1 ─ n notifications          (用户通知)
publishers 1 ─ n templates/drafts  (发布者模板/草稿)
```

---

## 3. 核心表结构

### 3.1 `schools` — 学校表
| 字段 | 类型 | 说明 | 约束 |
|------|------|------|------|
| id | BIGINT | 主键 | PK, AUTO_INCREMENT |
| name | VARCHAR(100) | 学校名称 | NOT NULL |
| code | VARCHAR(32) | 学校代码（学籍数据源标识） | UNIQUE |
| created_at | DATETIME | 创建时间 | DEFAULT NOW() |

### 3.2 `users` — 用户账号表
| 字段 | 类型 | 说明 | 约束 |
|------|------|------|------|
| id | BIGINT | 主键 | PK |
| phone | VARCHAR(20) | 手机号（登录账号） | UNIQUE, NOT NULL |
| password_hash | VARCHAR(255) | 密码哈希 | NOT NULL |
| role | ENUM('student','publisher_internal','publisher_external','admin') | 主角色 | NOT NULL |
| status | ENUM('active','disabled') | 账号状态 | DEFAULT 'active' |
| created_at / updated_at | DATETIME | 时间戳 | — |

### 3.3 `students` — 学生档案表（R34）
| 字段 | 类型 | 说明 | 约束 |
|------|------|------|------|
| id | BIGINT | 主键 | PK |
| user_id | BIGINT | 账号 | FK → users.id, UNIQUE |
| school_id | BIGINT | 学校 | FK → schools.id |
| student_no | VARCHAR(32) | 学号 | NOT NULL, INDEX |
| real_name | VARCHAR(50) | 真实姓名 | NOT NULL |
| college | VARCHAR(100) | 学院 | NOT NULL |
| class_name | VARCHAR(100) | 班级 | NOT NULL |
| grade | VARCHAR(16) | 年级 | — |
| verified_status | ENUM('pending','verified','rejected') | 学籍校验状态 | DEFAULT 'pending' |
| verified_at | DATETIME | 校验时间 | — |
| created_at | DATETIME | 创建时间 | — |

> 约束：`(school_id, student_no)` 联合唯一，防止跨校学号冲突。

### 3.4 `organizations` — 组织/机构表
| 字段 | 类型 | 说明 | 约束 |
|------|------|------|------|
| id | BIGINT | 主键 | PK |
| school_id | BIGINT | 学校（校内组织） | FK → schools.id，校外机构为 NULL |
| type | ENUM('internal_student_org','internal_dept','external_org') | 类型 | NOT NULL |
| name | VARCHAR(100) | 组织/机构名 | NOT NULL |
| legal_info | VARCHAR(255) | 机构资质（校外） | 校外必填 |
| status | ENUM('active','disabled') | 状态 | DEFAULT 'active' |
| created_at | DATETIME | 创建时间 | — |

### 3.5 `publishers` — 发布者认证表（R35）
| 字段 | 类型 | 说明 | 约束 |
|------|------|------|------|
| id | BIGINT | 主键 | PK |
| user_id | BIGINT | 账号 | FK → users.id, UNIQUE |
| organization_id | BIGINT | 归属组织/机构 | FK → organizations.id |
| identity_type | ENUM('internal','external') | 校内/校外 | NOT NULL |
| verified_status | ENUM('pending','verified','rejected') | 认证状态 | DEFAULT 'pending' |
| verified_by | BIGINT | 审核人 | FK → users.id |
| verified_at | DATETIME | 审核时间 | — |
| created_at | DATETIME | 申请时间 | — |

### 3.6 `activities` — 活动/招募表（R21/R27）
| 字段 | 类型 | 说明 | 约束 |
|------|------|------|------|
| id | BIGINT | 主键 | PK |
| publisher_id | BIGINT | 发布者 | FK → publishers.id |
| organization_id | BIGINT | 组织/机构 | FK → organizations.id |
| name | VARCHAR(40) | 活动名称 | NOT NULL |
| event_start_time | DATETIME | 活动开始 | NOT NULL |
| event_end_time | DATETIME | 活动结束 | NOT NULL |
| location | VARCHAR(255) | 活动地点 | NOT NULL |
| duration_hours | DECIMAL(4,1) | 志愿时长（0.5 步进） | NOT NULL |
| headcount_limit | INT | 人数上限 | NOT NULL |
| signup_deadline | DATETIME | 报名截止 | NOT NULL |
| checkin_method | ENUM('gps','qr','both') | 签到方式 | NOT NULL |
| description | TEXT | 描述 | — |
| cover | VARCHAR(255) | 封面 URL | — |
| contact | VARCHAR(100) | 联系方式 | — |
| notes | VARCHAR(500) | 补充说明 | — |
| status | ENUM('draft','recruiting','full','deadline','ongoing','finished','cancelled') | 活动状态 | DEFAULT 'draft' |
| approval_status | ENUM('pending','approved','rejected') | 认可状态 | DEFAULT 'pending' |
| is_credit_hours | TINYINT(1) | 是否可加时长（认可通过） | DEFAULT 0 |
| created_at / updated_at | DATETIME | 时间戳 | — |

> 索引：`(status)`、`(organization_id, status)`、`(event_start_time)`。约束：`event_end_time > event_start_time > signup_deadline`。

### 3.7 `activity_positions` — 活动岗位表
| 字段 | 类型 | 说明 | 约束 |
|------|------|------|------|
| id | BIGINT | 主键 | PK |
| activity_id | BIGINT | 活动 | FK → activities.id |
| name | VARCHAR(50) | 岗位名 | NOT NULL |
| headcount | INT | 岗位人数 | NOT NULL |

### 3.8 `activity_approvals` — 招募认可审核表（R36）
| 字段 | 类型 | 说明 | 约束 |
|------|------|------|------|
| id | BIGINT | 主键 | PK |
| activity_id | BIGINT | 活动 | FK → activities.id |
| publisher_type | ENUM('internal','external') | 发布者类型 | NOT NULL |
| status | ENUM('pending','approved','rejected') | 认可状态 | DEFAULT 'pending' |
| reviewed_by | BIGINT | 审核人（校方） | FK → users.id |
| review_comment | VARCHAR(500) | 审核意见 | — |
| reviewed_at | DATETIME | 审核时间 | — |
| created_at | DATETIME | 提交时间 | — |

### 3.9 `activity_edit_logs` — 编辑审计日志表（R24/R31）
| 字段 | 类型 | 说明 | 约束 |
|------|------|------|------|
| id | BIGINT | 主键 | PK |
| activity_id | BIGINT | 活动 | FK → activities.id |
| editor_id | BIGINT | 编辑者 | FK → users.id |
| editor_role | ENUM('publisher_internal','publisher_external','admin') | 编辑者角色 | NOT NULL |
| field_name | VARCHAR(32) | 修改字段 | NOT NULL |
| old_value | VARCHAR(500) | 修改前值 | — |
| new_value | VARCHAR(500) | 修改后值 | — |
| edit_seq | INT | 该活动第几次编辑 | NOT NULL |
| notified | TINYINT(1) | 是否已通知报名者 | DEFAULT 0 |
| created_at | DATETIME | 编辑时间 | NOT NULL |

> 审计日志只追加、不更新、不删除（不可篡改）。

### 3.10 `signups` — 报名表（R2/R13/R30）
| 字段 | 类型 | 说明 | 约束 |
|------|------|------|------|
| id | BIGINT | 主键 | PK |
| activity_id | BIGINT | 活动 | FK → activities.id |
| student_id | BIGINT | 学生 | FK → students.id |
| position_id | BIGINT | 岗位（可选） | FK → activity_positions.id |
| status | ENUM('active','waitlist','cancelled') | 报名/候补/已撤销 | DEFAULT 'active' |
| signup_time | DATETIME | 报名时间 | NOT NULL |
| created_at | DATETIME | 创建时间 | — |

> 约束：`(activity_id, student_id)` 联合唯一（防重复报名）。防超卖：报名写入时对 `activities.headcount_limit` 做原子扣减（对应 R30）。

### 3.11 `checkins` — 签到/签退表（R4/R5/R8）
| 字段 | 类型 | 说明 | 约束 |
|------|------|------|------|
| id | BIGINT | 主键 | PK |
| activity_id | BIGINT | 活动 | FK → activities.id |
| signup_id | BIGINT | 报名记录 | FK → signups.id |
| student_id | BIGINT | 学生 | FK → students.id |
| type | ENUM('checkin','checkout') | 签到/签退 | NOT NULL |
| method | ENUM('gps','qr') | 签到方式 | NOT NULL |
| gps_lat / gps_lng | DECIMAL(10,6) | 定位坐标 | 可空 |
| gps_accuracy | DECIMAL(6,1) | 定位精度（米） | 可空 |
| distance_m | INT | 距围栏中心距离（米） | 可空 |
| qr_token | VARCHAR(64) | 动态二维码凭证 | 可空 |
| check_time | DATETIME | 签到/签退时间 | NOT NULL |
| created_at | DATETIME | 记录时间 | — |

### 3.12 `volunteer_hours` — 志愿时长表（R5/R6/R14）
| 字段 | 类型 | 说明 | 约束 |
|------|------|------|------|
| id | BIGINT | 主键 | PK |
| activity_id | BIGINT | 活动 | FK → activities.id |
| student_id | BIGINT | 学生 | FK → students.id |
| signup_id | BIGINT | 报名记录 | FK → signups.id |
| hours | DECIMAL(4,1) | 认定时长（签退−签到） | NOT NULL |
| status | ENUM('pending','verified','appealing') | 待认定/已认定/申诉中 | DEFAULT 'pending' |
| verified_by | BIGINT | 认定人（校方） | FK → users.id |
| verified_at | DATETIME | 认定时间 | — |
| created_at | DATETIME | 生成时间 | — |

> 约束：`(activity_id, student_id)` 联合唯一。时长可溯源链：`activity → signup → checkin(checkin/checkout) → hours`。

### 3.13 `appeals` — 时长申诉表（R9）
| 字段 | 类型 | 说明 | 约束 |
|------|------|------|------|
| id | BIGINT | 主键 | PK |
| hours_id | BIGINT | 时长记录 | FK → volunteer_hours.id |
| student_id | BIGINT | 学生 | FK → students.id |
| reason | VARCHAR(500) | 申诉理由 | NOT NULL |
| evidence | JSON | 凭证（截图/照片 URL） | — |
| status | ENUM('pending','reviewed','resolved') | 状态 | DEFAULT 'pending' |
| handled_by | BIGINT | 处理人 | FK → users.id |
| handled_at | DATETIME | 处理时间 | — |
| created_at | DATETIME | 申诉时间 | — |

### 3.14 `certificates` — 证书表（R7/R10）
| 字段 | 类型 | 说明 | 约束 |
|------|------|------|------|
| id | BIGINT | 主键 | PK |
| student_id | BIGINT | 学生 | FK → students.id |
| activity_id | BIGINT | 活动（累计证明为空） | FK → activities.id, 可空 |
| type | ENUM('single','total') | 单次/累计证明 | NOT NULL |
| cert_no | VARCHAR(32) | 证书唯一编号 | UNIQUE, NOT NULL |
| qr_token | VARCHAR(64) | 核验二维码凭证 | UNIQUE, NOT NULL |
| hours | DECIMAL(6,1) | 证书时长 | NOT NULL |
| issuer | ENUM('school','joint') | 落款（本校/本校+机构联署） | NOT NULL |
| pdf_url | VARCHAR(255) | PDF 地址 | NOT NULL |
| created_at | DATETIME | 生成时间 | — |

### 3.15 `notifications` — 通知表（R12/R25）
| 字段 | 类型 | 说明 | 约束 |
|------|------|------|------|
| id | BIGINT | 主键 | PK |
| user_id | BIGINT | 接收人 | FK → users.id |
| type | ENUM('signup','checkin','hours','certificate','appeal','activity_change','activity_cancel') | 通知类型 | NOT NULL |
| title | VARCHAR(100) | 标题 | NOT NULL |
| content | TEXT | 内容（含变更摘要） | NOT NULL |
| need_receipt | TINYINT(1) | 是否需回执（强制通知） | DEFAULT 0 |
| receipt_status | ENUM('none','read','confirmed') | 回执状态 | DEFAULT 'none' |
| created_at | DATETIME | 发送时间 | — |

### 3.16 `templates` — 模板表（R23，扩展 P1）
| 字段 | 类型 | 说明 | 约束 |
|------|------|------|------|
| id | BIGINT | 主键 | PK |
| publisher_id | BIGINT | 发布者 | FK → publishers.id |
| name | VARCHAR(50) | 模板名 | NOT NULL |
| content | JSON | 字段模板快照 | NOT NULL |
| created_at | DATETIME | 创建时间 | — |

### 3.17 `drafts` — 草稿表（R22，扩展 P1）
| 字段 | 类型 | 说明 | 约束 |
|------|------|------|------|
| id | BIGINT | 主键 | PK |
| publisher_id | BIGINT | 发布者 | FK → publishers.id |
| content | JSON | 草稿内容快照 | NOT NULL |
| updated_at | DATETIME | 更新时间 | — |

---

## 4. 关键索引与约束汇总

| 表 | 索引/约束 | 目的 |
|----|----------|------|
| students | UNIQUE(school_id, student_no) | 学号全校唯一、防冒用 |
| activities | INDEX(status)、INDEX(organization_id, status) | 活动列表/状态筛选 |
| signups | UNIQUE(activity_id, student_id) | 防重复报名 |
| signups | 报名事务 + 名额原子扣减 | 防超卖（R30） |
| volunteer_hours | UNIQUE(activity_id, student_id) | 一次活动一条时长 |
| certificates | UNIQUE(cert_no)、UNIQUE(qr_token) | 证书编号与核验唯一 |
| activity_edit_logs | 只追加不更新不删除 | 审计不可篡改 |

---

## 5. 枚举字典汇总

| 枚举 | 取值 |
|------|------|
| users.role | student / publisher_internal / publisher_external / admin |
| activities.status | draft / recruiting / full / deadline / ongoing / finished / cancelled |
| activities.approval_status | pending / approved / rejected |
| signups.status | active / waitlist / cancelled |
| checkins.type | checkin / checkout |
| checkins.method | gps / qr |
| volunteer_hours.status | pending / verified / appealing |
| certificates.type | single / total |
| certificates.issuer | school / joint |
| organizations.type | internal_student_org / internal_dept / external_org |

---

## 6. 状态机映射（数据库 ↔ 业务）

| 业务状态 | 对应字段 | 流转 |
|---------|---------|------|
| 活动状态 | activities.status | draft→recruiting→(full/deadline)→ongoing→(finished/cancelled) |
| 招募认可 | activities.approval_status + is_credit_hours | pending→approved(rejected)；approved 时 is_credit_hours=1 |
| 报名状态 | signups.status | active→(waitlist/cancelled)；waitlist→active（候补转正） |
| 时长认定 | volunteer_hours.status | pending→verified；pending→appealing→verified |
| 编辑审计 | activity_edit_logs | 只追加，形成字段级变更链 |

---

## 7. 待确认

1. **数据库选型**：MySQL / PostgreSQL？建议 MySQL（团队熟悉度优先），JSON 字段两者均支持。
2. **学籍数据源对接**：`students` 的学号白名单由校方批量导入还是 API 实时校验？（对应 R34）
3. **动态二维码存储**：`checkins.qr_token` 的生成与过期策略（30-60s 失效，是否存 Redis 而非落库）。
4. **历史数据迁移**：试点校已有 Excel/青协数据是否导入 `volunteer_hours` 作为初始档案？

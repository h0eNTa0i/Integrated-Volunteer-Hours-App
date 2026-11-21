# 系统架构规格说明书 · 青禾志愿（大学志愿时长服务）

**日期**：2026-11-05
**类型**：后端架构设计
**关联文档**：`prd-volunteer-certification-2026-10-16.md`（PRD v1.5）、`database-schema-design-2026-10-23.md`（17 张核心表）、`role-permission-matrix-2026-10-23.md`（四角色权限矩阵）
**配套提示词**：`backend-architecture-prompt-2026-11-05.md`

> 本文档是可落地的后端架构蓝图：从「单校试点（1–3 万用户）」起步，到「多校（10–30 万）」，再到「规模化（100–300 万）」，分阶段演进，不做一次性过度设计。

---

## 0. 执行摘要

| 维度 | 结论 |
|------|------|
| **架构模式** | 模块化单体（Modular Monolith）起步 → 按热区拆分微服务 → 业务域微服务 |
| **核心语言/框架** | Node.js 20 + TypeScript + NestJS（与前端同栈；备选 Java 21 + Spring Boot 3） |
| **数据层** | MySQL 8（读写分离）+ Redis 7（缓存/防超卖/分布式锁）+ OSS（PDF/图片） |
| **异步层** | RocketMQ 5（削峰/通知/证书生成/审计） |
| **高可用** | 目标 99.9%；应用多副本 + DB 主从 + Redis Sentinel/Cluster + MQ 集群 |
| **高性能** | 核心接口 P95 ≤ 200ms、P99 ≤ 500ms；慢查询 < 100ms；重任务异步化 |
| **高并发** | 报名防超卖（原子扣减 + Redis 预扣）、签到幂等写入、查询多级缓存 |
| **安全合规** | 《个人信息保护法》《数据安全法》；敏感信息加密/脱敏；RBAC 四角色 |

**三个必须优先解决的技术难点**（决定架构成败）：
1. **报名防超卖**（R30）——秒杀式并发下的原子扣减与候补队列。
2. **签到防作弊 + 高并发写入**（R4/R5/R8）——GPS 电子围栏 + 动态二维码 + 幂等。
3. **证书导出的年度洪峰**（R7）——PDF 生成异步化 + 对象存储，避免拖垮 API。

---

## 1. 总体架构

### 1.1 架构模式与演进路线

| 阶段 | 用户规模 | 架构模式 | 理由 |
|------|---------|---------|------|
| **V1.0（试点）** | 1–3 万 | **模块化单体** | 团队小、迭代快、运维简单；模块边界清晰，为拆分留好缝隙 |
| **V1.1–V1.2（增长）** | 10–30 万 | 单体 + **拆出热区服务**（签到、证书、通知） | 热区资源密集，独立扩容更划算 |
| **V2.0（规模化）** | 100–300 万 | **业务域微服务** + API 网关 + 服务发现 | 独立扩容、故障隔离、多校多租户 |

> **决策**：不从微服务起步。微服务在试点阶段只会带来部署/链路追踪/数据一致性的额外成本，而收益几乎为零。模块化单体（同一进程内按 module 强隔离、禁止跨 module 直接访问他人表）可以在 1–2 周内升级为「按需拆服务」，兼顾速度与扩展性。

### 1.2 通信方式

- **对外**：REST（JSON，`/api/v1`）为主；签到动态二维码刷新、时长认定结果等需要「推送」的场景用 **WebSocket / SSE** 补充。
- **对内**：模块化单体阶段用进程内方法调用 + 领域事件（本地事件总线）；拆分后改为 MQ 异步事件 + gRPC/REST 同步调用。
- **数据流模式**：传统 CRUD + 少量 CQRS（时长汇总、看板统计走读模型/缓存）。

### 1.3 分层架构图

```
                        ┌──────────────────────────────────────────────┐
                        │              接入层 / 网关                    │
                        │   CDN → Nginx/SLB（SSL终结、静态资源、限流）   │
                        └───────────────────┬──────────────────────────┘
                                            │ REST / WS
        ┌───────────────────────────────────┴───────────────────────────┐
        │                    应用服务层（模块化单体）                     │
        │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐  │
        │  │ 认证授权 │ │ 活动模块 │ │ 报名模块 │ │ 签到模块 │ │ 时长模块 │  │
        │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘  │
        │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐              │
        │  │ 证书模块 │ │ 通知模块 │ │ 看板导出 │ │ 审计留痕 │  (统一鉴权/   │
        │  └─────────┘ └─────────┘ └─────────┘ └─────────┘   限流/幂等)  │
        └──────┬──────────────┬───────────────┬──────────────┬───────────┘
               │              │               │              │
        ┌──────▼──────┐ ┌─────▼──────┐ ┌──────▼──────┐ ┌─────▼──────────┐
        │  MySQL 8    │ │  Redis 7   │ │  RocketMQ 5 │ │  OSS/COS       │
        │ (主从/分片)  │ │(缓存/预扣/锁)│ │ (削峰/事件)  │ │ (PDF/图片/凭证) │
        └─────────────┘ └────────────┘ └─────────────┘ └────────────────┘
```

---

## 2. 技术选型表

| 类别 | 选型 | 理由 | 替代方案 |
|------|------|------|---------|
| 语言/框架 | **Node.js 20 + TypeScript + NestJS** | 与前端同栈、类型安全、模块化（Module/DI/Guard/Interceptor）天生契合「模块化单体」；CRUD+IO 密集场景性能足够 | Java 21 + Spring Boot 3（易招人、生态最成熟，强类型长期维护更稳） |
| 主数据库 | **MySQL 8.0（InnoDB）** | 团队熟悉、生态成熟、读写分离/分片方案成熟；JSON 字段够用 | PostgreSQL（JSONB 更强、并发控制更好） |
| 缓存 | **Redis 7** | 缓存 + 防超卖预扣 + 分布式锁 + 幂等/限流计数，一专多能 | — |
| 消息队列 | **RocketMQ 5** | 国内成熟、支持事务消息/延迟消息（证书延迟生成、签到延迟兜底） | RabbitMQ（轻量易运维）；Kafka（海量日志/审计流） |
| 对象存储 | **阿里云 OSS / 腾讯云 COS** | PDF、活动封面、申诉凭证，免自建文件服务 | MinIO（私有化/本地） |
| 网关 | **Nginx + 云 SLB**（MVP）；**APISIX/Kong**（规模化） | MVP 轻量；规模化需动态路由/鉴权/限流插件 | — |
| 鉴权 | **JWT（access 15min）+ Refresh Token（Redis 可撤销）** | 无状态水平扩展 + 可撤销（登出/封号即时生效） | Session（有状态，不利于扩展） |
| 定时任务 | **XXL-Job** | 活动状态流转、漏签退兜底、证书批量、通知定时 | 云函数定时触发器 |
| 搜索 | MVP：MySQL 前缀/全文索引；规模化：**Elasticsearch** | MVP 数据量小，ES 是过度设计；规模化再引入 | — |
| 可观测性 | **Prometheus + Grafana + Loki + SkyWalking** | 指标/日志/链路三件套，开源免费 | 云厂商监控 |
| 部署 | MVP：Docker + 云服务器；规模化：**Kubernetes** | 循序渐进，试点不需要 K8s 复杂度 | — |

---

## 3. 服务/模块拆解

模块化单体内部按业务域划分 module，每个 module 拥有自己的表访问权，**禁止跨 module 直接读写他人表**（只能通过服务接口或领域事件），为后续拆分奠定基础。

| 模块 | 职责 | 关键表 | 对外 API（示例） | 关键事件 |
|------|------|--------|-----------------|---------|
| **auth** | 登录/注册、JWT 签发、Refresh、设备管理 | users | `POST /auth/login`、`POST /auth/refresh`、`POST /auth/logout` | UserLoggedIn |
| **identity** | 学籍校验（学号+学校）、发布者/机构认证（R34/R35） | students、schools、organizations、publishers | `POST /students/profile`、`POST /publishers/apply` | StudentVerified、PublisherVerified |
| **activity** | 活动发布/编辑/草稿/模板/状态机/取消/认可审核（R21–R33/R36） | activities、activity_positions、activity_approvals、activity_edit_logs、templates、drafts | `POST /activities`、`PUT /activities/{id}`、`POST /activities/{id}/approve` | ActivityPublished、ActivityEdited、ActivityCancelled |
| **signup** | 报名/候补/撤销 + 防超卖（R2/R13/R30） | signups、activities（名额计数） | `POST /activities/{id}/signups`、`DELETE /signups/{id}` | SignupCreated、SignupWaitlisted |
| **checkin** | 签到/签退、GPS 围栏、动态二维码、防作弊（R4/R5/R8） | checkins、volunteer_hours（生成待认定） | `POST /activities/{id}/checkins`、`POST /activities/{id}/checkouts` | CheckinDone、CheckoutDone、HoursGenerated |
| **hours** | 时长认定、溯源、申诉（R6/R9/R14） | volunteer_hours、appeals | `GET /students/me/hours`、`POST /hours/{id}/appeals` | HoursVerified、AppealSubmitted |
| **certificate** | 单次/累计证书、PDF 生成、在线核验（R7/R10） | certificates | `POST /certificates`、`GET /certificates/{id}`、`GET /verify?certNo=` | CertificateGenerated |
| **notification** | 站内信 + 推送、变更分档 + 回执（R12/R25） | notifications | `GET /notifications`、`POST /notifications/{id}/receipt` | NotificationSent |
| **report** | 看板统计、名单/时长导出、官方平台对接（R11/R19） | （读模型/汇总表） | `GET /reports/summary`、`POST /exports/roster` | ExportCompleted |
| **common** | 鉴权中间件、限流、幂等、审计、脱敏 | — | — | — |

> **拆出热区的时机**（从单体迁出）：当某个模块的 CPU/IO 独立于其它模块出现明显尖峰（如签到写入、证书 PDF 生成）且需独立扩容时，先把该 module 拆为独立服务，通信改为 MQ/REST。签到服务是第一个候选。

---

## 4. 数据库设计（高并发改造）

**基线**：沿用既有 17 张表结构（见 `database-schema-design-2026-10-23.md`），在「不推翻」前提下做并发与规模改造。

### 4.0 核心表清单（17 张，自包含总览）

> 完整字段定义见 `database-schema-design-2026-10-23.md`，下表为设计要点总览。

| # | 表 | 用途 | 关键字段 | 关键约束 / 索引 |
|---|----|------|---------|----------------|
| 1 | `schools` | 学校 | id, name, code | `code` UNIQUE |
| 2 | `users` | 账号（登录/角色） | phone, password_hash, role, status | `phone` UNIQUE；role 枚举四角色 |
| 3 | `students` | 学生档案（学籍） | user_id, school_id, student_no, real_name, college, class_name, verified_status | `(school_id, student_no)` 联合唯一；student_no INDEX |
| 4 | `organizations` | 组织/机构 | school_id, type, name, legal_info, status | type 枚举（校内学生组织/校内部门/校外机构） |
| 5 | `publishers` | 发布者认证 | user_id, organization_id, identity_type, verified_status | `user_id` UNIQUE |
| 6 | `activities` | 活动/招募 | publisher_id, organization_id, name, event_start/end_time, duration_hours, headcount_limit, signup_deadline, checkin_method, status, approval_status, is_credit_hours | `(status)`、`(organization_id,status)`、`(event_start_time)`；**新增 `signed_up_count` 计数器列（防超卖）** |
| 7 | `activity_positions` | 活动岗位 | activity_id, name, headcount | `activity_id` INDEX |
| 8 | `activity_approvals` | 招募认可审核 | activity_id, publisher_type, status, reviewed_by | — |
| 9 | `activity_edit_logs` | 编辑审计（只追加） | activity_id, editor_id, field_name, old_value, new_value, edit_seq | 只追加不更新不删除 |
| 10 | `signups` | 报名 | activity_id, student_id, position_id, status, signup_time | `(activity_id, student_id)` 联合唯一（防重复/防超卖） |
| 11 | `checkins` | 签到/签退 | activity_id, signup_id, student_id, type, method, gps_lat/lng, distance_m, qr_token, check_time | `(activity_id, student_id, type)` 联合唯一（幂等） |
| 12 | `volunteer_hours` | 志愿时长 | activity_id, student_id, signup_id, hours, status, verified_by | `(activity_id, student_id)` 联合唯一 |
| 13 | `appeals` | 时长申诉 | hours_id, student_id, reason, evidence, status | — |
| 14 | `certificates` | 证书 | student_id, activity_id, type, cert_no, qr_token, hours, issuer, pdf_url | `cert_no` UNIQUE、`qr_token` UNIQUE |
| 15 | `notifications` | 通知 | user_id, type, title, content, need_receipt, receipt_status | `(user_id, created_at)` INDEX |
| 16 | `templates` | 发布模板（P1） | publisher_id, name, content(JSON) | — |
| 17 | `drafts` | 草稿（P1） | publisher_id, content(JSON), updated_at | — |

> **一处结构性改动**：`activities` 表新增 `signed_up_count INT DEFAULT 0` 计数器列，作为防超卖的原子扣减载体（见 4.3）。这是唯一对既有表结构的改动，其余表保持原设计。

### 4.1 读写分离与索引

- **读写分离**：主库 1 台负责写，从库 1–N 台负责读（活动列表、时长查询、看板全走从库）。读写延迟 < 50ms 的业务（如「报名后立即查我的报名」）走主库或「写完读主」。
- **索引补充**（在既有索引基础上）：
  - `signups(activity_id, status)`、`signups(student_id, created_at)` —— 报名列表、我的报名分页。
  - `checkins(activity_id, student_id, type)` 联合唯一 + 查询索引。
  - `volunteer_hours(student_id, status)` —— 我的时长明细。
  - `activities(school_id, status, event_start_time)` —— 校级活动列表（为多校预留）。
  - `notifications(user_id, created_at)` —— 通知分页。

### 4.2 分库分表策略（分阶段）

| 阶段 | 策略 |
|------|------|
| **单校（试点）** | 单库单实例 + 读写分离，不拆表 |
| **多校（10–30 万）** | 按 `school_id` 分库：`activities/signups/checkins/volunteer_hours/certificates` 分片；`users/schools/organizations` 全局表 |
| **百万级** | 引入 **ShardingSphere** 做分片中间件；`checkins/volunteer_hours` 历史数据按月冷热分离，热数据 SSD、冷数据归档到低成本存储 |

> 分片键统一选 `school_id`（或派生 `activity_id`），因为业务天然按校隔离（v1 单校），且 90% 查询都带 school/activity 维度。

### 4.3 报名防超卖（R30，核心）

**方案 A（MVP，推荐）——MySQL 原子扣减 + 唯一约束**：

```sql
-- 报名时：先原子扣减名额计数（活动表增加 signed_up_count 计数器列）
UPDATE activities
SET signed_up_count = signed_up_count + 1
WHERE id = ? AND signed_up_count < headcount_limit AND status = 'recruiting';

-- 受影响行数 = 1 → 名额扣减成功，继续插入报名记录
-- 受影响行数 = 0 → 满员，转候补
INSERT INTO signups(activity_id, student_id, position_id, status, signup_time)
VALUES (?, ?, ?, 'active', NOW());
```

- 关键：`signups` 表 `UNIQUE(activity_id, student_id)` 兜底防重复报名；`signed_up_count` 用行锁保证原子性。
- 撤销/取消报名时 `signed_up_count = signed_up_count - 1`，并触发候补转正。

**方案 B（百万级升级）——Redis 预扣库存 + Lua 原子扣减**：

```lua
-- Redis Lua：原子扣减名额，返回 1 成功 / 0 满员
local stock = redis.call('GET', KEYS[1])            -- activity:stock:{id}
if tonumber(stock or 0) > 0 then
  redis.call('DECR', KEYS[1])
  return 1
else
  return 0
end
```

- 活动发布时将名额写入 `activity:stock:{id}`；报名走 Lua 预扣 → 成功则发 MQ 异步落库（`signed_up_count` 同步更新），失败走候补。
- Redis 扣减成功但落库失败时，用**补偿任务**回滚库存；`UNIQUE(activity_id, student_id)` 保证最终不超卖。
- **演进判断**：单校试点用方案 A 足够（单活动报名 QPS 在数百量级，MySQL 行锁能扛）；当报名 QPS 达数千/秒杀压测暴露瓶颈时切换到方案 B。

### 4.4 签到幂等（R4/R5/R8）

- `checkins` 表 `UNIQUE(activity_id, student_id, type)` —— 一次活动每个学生只能有一条「签到」+ 一条「签退」。
- 接口幂等：`Idempotency-Key` 请求头（或业务幂等键）落 Redis，重复请求直接返回原结果。
- 动态二维码：`qr_token` 存 Redis，30–60s 过期、一次性消费（`DEL` 原子判断），防截图复用。

### 4.5 冷热分离

- `activity_edit_logs`、`checkins`、`notifications` 属于高频写入但低频读的历史数据：保留近 6 个月热数据，更早按月归档到归档库/低成本存储，审计查询走归档索引。

---

## 5. API 设计规范

### 5.1 通用规范

- **风格**：RESTful，统一前缀 `/api/v1`；版本化通过路径（v2 时新开 `/api/v2`）。
- **统一响应包**：
```json
{ "code": 0, "message": "ok", "data": { }, "requestId": "uuid" }
```
- **错误码**：业务错误 5 位（如 `11001` 活动已满、`11002` 重复报名、`21001` 未认证学生、`31001` 签到超时）；系统错误 `500xx`；鉴权错误 `401xx/403xx`。
- **分页**：`page`（从 1 起）+ `size`（默认 20，上限 100），返回 `{ items, page, size, total }`。
- **限流**：网关 IP 级 + 用户级（Redis 令牌桶/漏桶）；报名、签到接口单独收紧。
- **幂等**：写接口支持 `Idempotency-Key` 头，服务端 Redis 缓存结果 24h。

### 5.2 四个核心接口示例

**① 报名** `POST /api/v1/activities/{activityId}/signups`

```json
// Request（Header: Authorization: Bearer <access>）
{ "positionId": 1024 }

// Response 201
{
  "code": 0,
  "data": {
    "signupId": "18823",
    "status": "active",           // active | waitlist
    "position": { "id": 1024, "name": "引导岗" }
  }
}

// 满员时返回 code 11001（转候补）或直接 status: "waitlist"
```

**② 签到** `POST /api/v1/activities/{activityId}/checkins`

```json
// Request（Header 含 Idempotency-Key）
{
  "method": "gps",                 // gps | qr
  "gpsLat": 30.123456, "gpsLng": 114.123456, "gpsAccuracy": 15.2,
  "qrToken": null
}

// Response 200
{
  "code": 0,
  "data": {
    "checkinId": "9102",
    "checkTime": "2026-11-05T17:02:00+08:00",
    "distanceM": 45.3,
    "withinFence": true
  }
}
// 围栏外 / 二维码过期 → code 31001，前端回退另一种签到方式
```

**③ 时长查询** `GET /api/v1/students/me/hours?status=verified&page=1&size=20`

```json
{
  "code": 0,
  "data": {
    "totalHours": 42.5,
    "verifiedHours": 38.0,
    "pendingHours": 4.5,
    "items": [
      { "hoursId": "71", "activityName": "社区敬老", "hours": 4.0,
        "status": "verified", "verifiedAt": "2026-10-20T10:00:00+08:00" }
    ]
  }
}
```

**④ 证书导出** `POST /api/v1/certificates`

```json
// Request
{ "type": "single", "activityId": 123 }   // 或 { "type": "total" }

// Response 202（异步生成）
{
  "code": 0,
  "data": { "certId": "77", "certNo": "QH-2026-0001234", "status": "generating" }
}

// 轮询 GET /api/v1/certificates/77 → status: "ready", "pdfUrl": "https://oss.../xxx.pdf"
// 在线核验 GET /api/v1/verify?certNo=QH-2026-0001234（公开、免登录）
```

### 5.3 API 详细列表（完整接口清单）

> 权限图例：公开＝无需登录；学生＝学生；发布者＝校内/校外发布者；管理员＝校方管理员。所有写接口支持 `Idempotency-Key` 幂等；`⏱` 表示接口单独限流（报名/签到/证书）。

**① 认证与账号（auth）**

| Method | 路径 | 说明 | 权限 |
|--------|------|------|------|
| POST | `/auth/sms-code` | 发送短信验证码 | 公开 |
| POST | `/auth/register` | 注册（手机号+验证码） | 公开 |
| POST | `/auth/login` | 登录，返回 access+refresh | 公开 |
| POST | `/auth/refresh` | 刷新 access token | 公开（持 refresh） |
| POST | `/auth/logout` | 登出（refresh 加入黑名单） | 学生/发布者/管理员 |
| GET | `/auth/me` | 当前登录用户信息 | 学生/发布者/管理员 |

**② 身份与认证（identity）**

| Method | 路径 | 说明 | 权限 |
|--------|------|------|------|
| GET | `/schools` | 学校列表（注册选择） | 公开 |
| POST | `/students/profile` | 提交/完善学籍档案（学号+学校校验，R34） | 学生 |
| GET | `/students/me` | 我的学籍档案 | 学生 |
| PUT | `/students/me` | 更新档案 | 学生 |
| POST | `/publishers/apply` | 发布者/机构认证申请（R35） | 学生（申请升级） |
| GET | `/publishers/me` | 我的发布者认证状态 | 发布者 |
| GET | `/admin/verifications/students` | 学籍待核验列表 | 管理员 |
| POST | `/admin/students/{id}/verify` | 审核学籍（通过/驳回） | 管理员 |
| GET | `/admin/verifications/publishers` | 发布者认证待审核列表 | 管理员 |
| POST | `/admin/publishers/{id}/verify` | 审核发布者/机构认证 | 管理员 |

**③ 活动（activity）**

| Method | 路径 | 说明 | 权限 |
|--------|------|------|------|
| GET | `/activities` | 活动列表（筛选/搜索/分页） | 公开 |
| GET | `/activities/{id}` | 活动详情（含岗位） | 公开 |
| POST | `/activities` | 发布活动（R21） | 发布者 |
| PUT | `/activities/{id}` | 编辑活动（分级字段+留痕，R24/R28） | 发布者（本人/同组织）、管理员 |
| POST | `/activities/{id}/cancel` | 取消活动（留痕，R26） | 发布者、管理员 |
| GET | `/activities/mine` | 我发布的活动 | 发布者 |
| GET | `/activities/{id}/edit-logs` | 编辑审计日志（R31） | 发布者、管理员 |
| POST | `/activities/{id}/approve` | 招募认可审核（R36） | 管理员 |
| GET | `/drafts` / POST `/drafts` / PUT `/drafts/{id}` / DELETE `/drafts/{id}` | 草稿箱（R22） | 发布者 |
| GET | `/templates` / POST `/templates` / DELETE `/templates/{id}` | 发布模板（R23） | 发布者 |

**④ 报名（signup）**

| Method | 路径 | 说明 | 权限 |
|--------|------|------|------|
| POST | `/activities/{id}/signups` | 报名（防超卖，R30）⏱ | 学生 |
| DELETE | `/signups/{id}` | 撤销报名（释放名额） | 学生 |
| GET | `/signups/mine` | 我的报名记录 | 学生 |
| GET | `/activities/{id}/signups` | 报名名单（R11） | 发布者、管理员 |
| PUT | `/signups/{id}/confirm` | 候补转正 | 发布者 |
| POST | `/activities/{id}/signups/export` | 导出报名名单 Excel/CSV | 发布者、管理员 |

**⑤ 签到（checkin）**

| Method | 路径 | 说明 | 权限 |
|--------|------|------|------|
| POST | `/activities/{id}/checkins` | 签到（GPS/二维码，R4）⏱ | 学生 |
| POST | `/activities/{id}/checkouts` | 签退（记录实际时长，R5）⏱ | 学生 |
| GET | `/activities/{id}/checkin-qr` | 获取现场动态二维码（30–60s 刷新，R8） | 发布者 |
| GET | `/checkins/mine` | 我的签到记录 | 学生 |

**⑥ 时长（hours）**

| Method | 路径 | 说明 | 权限 |
|--------|------|------|------|
| GET | `/students/me/hours` | 我的时长（汇总+明细，R6） | 学生 |
| GET | `/hours/{id}` | 时长详情（全链溯源，R14） | 学生/发布者/管理员 |
| POST | `/hours/{id}/appeals` | 发起时长申诉（R9） | 学生 |
| GET | `/hours/{id}/appeals` | 申诉记录与处理进度 | 学生/发布者/管理员 |
| POST | `/activities/{id}/hours/batch` | 批量录入时长（R11） | 发布者 |
| POST | `/hours/{id}/verify` | 时长认定（最终盖章，R36） | 管理员 |
| GET | `/admin/hours` | 待认定时长列表 | 管理员 |

**⑦ 证书（certificate）**

| Method | 路径 | 说明 | 权限 |
|--------|------|------|------|
| POST | `/certificates` | 申请证书（single/total，R7）⏱ | 学生 |
| GET | `/certificates` | 我的证书列表 | 学生 |
| GET | `/certificates/{id}` | 证书状态/下载地址 | 学生 |
| POST | `/activities/{id}/certificates/batch` | 批量生成证书（R11） | 发布者、管理员 |
| GET | `/verify?certNo=` | 在线核验真伪（R10） | 公开 |

**⑧ 通知（notification）**

| Method | 路径 | 说明 | 权限 |
|--------|------|------|------|
| GET | `/notifications` | 通知列表（分页） | 学生/发布者/管理员 |
| GET | `/notifications/unread-count` | 未读数 | 学生/发布者/管理员 |
| POST | `/notifications/{id}/receipt` | 回执确认（强制通知，R25） | 学生/发布者 |

**⑨ 看板与导出（report）**

| Method | 路径 | 说明 | 权限 |
|--------|------|------|------|
| GET | `/reports/summary` | 数据看板统计（R19） | 发布者（本组织）、管理员（全校） |
| POST | `/exports/roster` | 导出报名名单 | 发布者、管理员 |
| POST | `/exports/hours` | 导出时长报表 | 发布者、管理员 |
| POST | `/exports/official` | 导出官方平台格式（志愿汇/中国志愿服务网，R15） | 发布者、管理员 |

**⑩ 元数据与通用（meta）**

| Method | 路径 | 说明 | 权限 |
|--------|------|------|------|
| GET | `/meta/enums` | 枚举字典（状态/角色/签到方式等） | 公开 |
| GET | `/meta/school-config` | 本校配置（综测规则展示，R17） | 公开 |

> 合计约 **55 个接口**，覆盖 PRD 需求池 R1–R36 的全部功能域。落地时按「auth → identity → activity → signup → checkin → hours → certificate」顺序实现（对应关键路径依赖）。

---

## 6. 缓存设计

### 6.1 多级缓存

| 层级 | 用途 | 示例 |
|------|------|------|
| CDN | 静态资源、活动封面 | index.html、图片 |
| 本地缓存 | 极热数据（学校配置、枚举字典） | 进程内 1min 短 TTL |
| Redis | 业务缓存 + 防超卖 + 锁 + 限流 | 活动详情、时长汇总、名额库存 |
| MySQL 从库 | 兜底读 | — |

### 6.2 缓存键规范

```
activity:{id}                      活动详情（TTL 10min，编辑/取消时主动失效）
activity:list:{schoolId}:{hash}    活动列表（按筛选条件哈希，TTL 5min）
activity:stock:{id}                名额库存（防超卖预扣，活动期间常驻）
hours:summary:{studentId}          学生时长汇总（TTL 10min，认定后失效）
student:{id}                       学生档案（TTL 30min）
checkin:qr:{activityId}:{token}    动态二维码凭证（30–60s，一次性）
idempotency:{key}                  幂等结果（TTL 24h）
```

### 6.3 防护三件套

- **穿透**：对「不存在的活动 id」返回空值缓存（TTL 短）；规模化用布隆过滤器。
- **击穿**：热点活动详情用互斥锁（`SET NX`）只让一个请求回源，其余等待；活动发布时预热缓存。
- **雪崩**：缓存 TTL 加随机抖动（±10%）；Redis 用 Sentinel/Cluster 高可用 + 本地缓存兜底。

---

## 7. 消息队列与异步任务

### 7.1 事件流（Topic 与消费方）

| Topic | 事件 | 消费方 | 用途 |
|-------|------|--------|------|
| `signup` | SignupCreated / SignupWaitlisted | notification、report | 报名成功通知、名额统计 |
| `checkin` | CheckinDone / CheckoutDone | hours、notification | 生成待认定时长、签到提醒 |
| `hours` | HoursGenerated / HoursVerified | certificate、notification | 触发可导出证书、认定结果通知 |
| `certificate` | CertificateGenerateRequested | certificate-worker | 异步生成 PDF |
| `activity` | ActivityEdited / ActivityCancelled | notification | 变更分档通知 + 回执 |
| `audit` | 各类关键操作日志 | audit-consumer | 审计留痕（只追加） |

### 7.2 削峰与可靠性

- **报名削峰**：报名请求入 MQ 后异步写库（百万级），峰值队列堆积由 RocketMQ 缓冲，消费端水平扩容。
- **延迟消息**：漏签退兜底（活动结束后 N 小时仍未签退则按预设规则生成时长）、证书批量生成排队。
- **重试与死信**：消费失败指数退避重试，超过阈值进死信队列，人工介入；保证消息**至少一次**投递，消费端做幂等（凭业务唯一键）。

---

## 8. 高可用与容灾

### 8.1 部署拓扑

```
                用户
                 │
          ┌──────▼──────┐   CDN（静态资源）
          │  SLB / Nginx │──┐
          └──────┬──────┘  │
        ┌────────┼────────┐│
   ┌────▼───┐┌───▼────┐┌─▼───┐
   │ App #1 ││ App #2 ││ App │  （多副本，无状态，水平扩展）
   └───┬────┘└───┬────┘└──┬──┘
       │         │        │
   ┌───▼───┐ ┌───▼────┐ ┌─▼─────┐
   │MySQL主│─│MySQL从 │ │ Redis │  （主从 + Sentinel/Cluster）
   └───────┘ └────────┘ └───────┘
   ┌─────────────┐  ┌──────────────┐
   │ RocketMQ 集群 │  │   OSS/COS    │
   └─────────────┘  └──────────────┘
```

- **应用层**：无状态多副本（≥2），挂掉自动摘除，通过负载均衡切换。
- **MySQL**：主从 + 半同步复制；主库故障自动主从切换（或云 RDS 高可用版）。
- **Redis**：Sentinel（小规模）/ Cluster（规模化）主从切换。
- **MQ**：RocketMQ 主从/多副本，保证消息不丢。

### 8.2 备份与恢复

- **全量备份**：每日一次；**增量**：binlog 持续归档。
- **PITR**：支持时间点恢复，RPO ≤ 5 分钟，RTO ≤ 30 分钟。
- **容灾**：核心数据跨可用区（或跨机房）冗余；定期做恢复演练。

### 8.3 熔断降级

- **熔断器**：下游（DB/Redis/MQ/OSS）故障时自动熔断，快速失败并降级。
- **降级策略**：证书 PDF 生成失败→提示稍后重试并保留请求；缓存失效→直连从库兜底；非核心功能（排行榜、看板）降级关停，保核心闭环（报名→签到→时长→证书）。

---

## 9. 监控告警与可观测性

| 类别 | 工具 | 关键指标 |
|------|------|---------|
| 指标 | Prometheus + Grafana | QPS、P95/P99 延迟、错误率、慢查询、缓存命中率、队列积压、JVM/内存/GC |
| 日志 | Loki（或 ELK） | 结构化日志，requestId 贯穿链路；审计日志独立存储只追加 |
| 链路追踪 | SkyWalking | 报名/签到/证书全链路耗时定位 |
| 告警 | AlertManager | 见下表阈值 |

**核心告警阈值（示例）**：

| 指标 | 阈值 | 级别 |
|------|------|------|
| 接口错误率 | > 1% 持续 5min | P1 告警 |
| 核心接口 P95 | > 500ms 持续 5min | P2 告警 |
| MySQL 慢查询 | 单条 > 100ms 数量突增 | P2 告警 |
| Redis 缓存命中率 | < 80% 持续 10min | P3 提示 |
| MQ 队列积压 | > 10 万条或消费延迟 > 1min | P1 告警 |
| 报名接口 QPS | 超过容量 80% | P1 告警（触发扩容） |

> **业务埋点**（对齐 PRD 第 5 节）：`user_register / activity_view / activity_signup / activity_checkin / certificate_export / hours_summary_view`，签到事件带 `method / gps_accuracy / distance_m / duration_credited`，用于防作弊分析与北极星指标「月活跃认证时长」。

---

## 10. 性能与压测方案

### 10.1 压测场景与目标

| 场景 | 目标 QPS | 目标指标 |
|------|---------|---------|
| 活动列表查询 | 5000 QPS | P95 ≤ 200ms，缓存命中 ≥ 90% |
| 活动详情 | 2000 QPS | P95 ≤ 150ms |
| 报名（含防超卖） | 2000 QPS 峰值 | 不超卖、P95 ≤ 500ms、无死锁 |
| 签到写入 | 1000 QPS 峰值 | 幂等正确、P95 ≤ 300ms |
| 时长查询 | 3000 QPS | P95 ≤ 200ms |
| 证书导出 | 1000 并发提交 | 异步排队不阻塞 API，PDF 生成成功率 ≥ 99.9% |

### 10.2 容量规划与弹性

- **单副本能力**：以压测为准，按「单副本承载 2000–3000 QPS 读」估算，写接口按 500–1000 QPS 估算。
- **弹性扩容**：报名/签到/证书高峰期（学期末、综测季、活动秒杀）自动加副本；平时缩容至最小 2 副本控成本。
- **成本控制**：K8s HPA + 定时扩容（XXL-Job 在已知高峰前预扩）；冷数据归档降存储成本。

---

## 11. 安全设计清单

| 类别 | 措施 |
|------|------|
| **认证鉴权** | JWT + Refresh（Redis 可撤销）；RBAC 四角色 + 接口级鉴权（`@Roles()` Guard）；水平/垂直越权校验（所有按 id 查询都校验归属） |
| **密码安全** | bcrypt（cost 12）哈希；登录失败限流 + 账号锁定 |
| **敏感信息** | 学号/手机号/姓名/定位：静态加密存储（字段级 AES 或透明加密）、TLS 1.2+ 传输、展示脱敏（手机号 138****5678）、最小权限访问 |
| **接口防护** | 参数化查询防 SQL 注入；输入校验 + 输出转义防 XSS；CSRF Token；防重放（签到/报名幂等）；动态二维码 30–60s 防截图 |
| **限流防刷** | 网关 IP 限流 + 用户级限流；报名/签到接口收紧；验证码防批量注册 |
| **审计留痕** | 活动编辑、时长认定、证书落款等关键操作只追加、不可篡改（`activity_edit_logs`） |
| **数据隔离** | 单校数据隔离（v1）；所有查询强制带 `school_id` 维度，为多租户隔离预留 |
| **合规** | 《个人信息保护法》《数据安全法》：最小化采集、明确授权、可删除（用户注销）、数据出境评估 |

---

## 12. 演进路线图

| 阶段 | 用户规模 | 架构升级点 | 触发条件 |
|------|---------|-----------|---------|
| **V1.0（单校试点）** | 1–3 万 | 模块化单体 + MySQL 读写分离 + Redis + MQ（通知/证书异步）+ 方案 A 防超卖 | 立项即启动，最快 6–8 周上线 |
| **V1.1–V1.2（多校）** | 10–30 万 | 拆出「签到服务」「证书生成服务」「通知服务」；报名切换方案 B（Redis 预扣）；按 school_id 分库 | 报名 QPS 破千、证书导出 CPU 尖峰、单库写入瓶颈 |
| **V2.0（规模化）** | 100–300 万 | 业务域微服务 + API 网关（APISIX）+ 服务发现 + ShardingSphere 分片 + Elasticsearch 搜索 + 多租户隔离 | 百万级压测、多校多租户、Q4 前完成压测 |

---

## 附录：待确认的开放项（设计落地前需拍板）

1. **单校峰值并发量**：首所试点校学生规模与热门活动报名并发量级，决定是否提前上方案 B。
2. **预算/云厂商**：阿里云 or 腾讯云，影响 RDS/Redis/MQ/OSS 选型细节与成本。
3. **学号数据源对接方式**（R34）：校方学号白名单是批量导入还是 API 实时校验，决定 identity 模块实现。
4. **漏签退兜底规则**：签到后未签退的时长口径（预设时长 or 签到至活动结束），影响延迟消息逻辑。
5. **证书公章/核验权威**：PDF 电子章自动加盖 or 线下盖章；在线核验权威方（本产品/校方/官方平台）。
6. **官方平台对接格式**：志愿汇/中国志愿服务网的具体导入字段与规范，影响 report 导出模块。

---

> 本架构由 Backend Architect 基于项目既有 PRD 与数据库设计产出，关键决策请由产品负责人与后端 Lead 评审后落地。

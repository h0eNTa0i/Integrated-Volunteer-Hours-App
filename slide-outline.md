# Slide Outline

## Meta
- Topic: 面向中国大学生的「志愿时长认证与活动管理」App（青禾志愿）项目汇报
- Scenario: 老师/评委项目答辩汇报，正式、结构清晰、突出产品价值与实现成果
- Content Source: provided（PRD v1.5 + index.html 三端原型 + 数据库设计 + 后端架构 + 开发日志）
- Research: light — 补充全国志愿规模与高校志愿需求权威数据（民政部/中国高校志愿服务发展报告）
- Style: 沿用「青禾志愿」品牌色——蓝 #3B82F6 + 紫 #8B5CF6，清爽科技风，浅底 + 深蓝紫强调
- Slide Count: 19
- Generated At: 2026-11-06

## Source Materials
- PRD v1.5（R1–R36 需求池、用户画像 A/B/C、竞品对比、市场数据、路线图 M1–M6）
- index.html（26 屏三端高保真原型：学生端/发布者端/校方端）
- database-schema-design（17 张表）
- backend-architecture-spec（模块化单体→微服务、MySQL+Redis+RocketMQ+OSS、约55个API）
- 外部补充：民政部「十五五」规划（实名注册志愿者2.4亿、队伍135万支、服务时长超53亿小时）；
  陕西团省委82校观测（注册占比87%）；《中国高校志愿服务发展报告2024》（重点校52h vs 普通校28h）；
  调研（期望激励：志愿时长认证89.34%、综测加分86.07%）

## Slide-by-Slide Outline
1. **Slide 1 — Cover** — 志愿时长App项目汇报 | 青禾志愿（30秒认证闭环）| Layout: L02 | Dark | 装饰+渐变
2. **Slide 2 — Agenda** — 汇报议程（背景→方案→实现→成果→展望）| Layout: L19 | 
3. **Slide 3 — 背景与痛点** — 大学生志愿时长的三大痛点（不透明/易漏记、签到防作弊难、证书不可验证）| Layout: L07
4. **Slide 4 — 市场与需求** — 2.4亿注册志愿者 / 高校年均时长52h vs 28h / 89%期望时长认证 | Layout: L09/L11 | Dark | Chart
5. **Slide 5 — 产品定位** — 校园志愿执行工具 + 官方平台上游；30秒闭环 + 北极星「月活认证时长」| Layout: L04/L05
6. **Slide 6 — 用户画像** — A综测刷分党 / B志愿达人 / C组织者学生干部 | Layout: L07
7. **Slide 7 — 解决方案总览** — 三端双角色（学生端/发布者端/校方端）+ 统一认可机制 | Layout: L07/L16
8. **Slide 8 — 核心闭环** — 报名→签到→时长→证明 30秒闭环（4步流程）| Layout: L13 | Process
9. **Slide 9 — 学生端功能** — 浏览筛选/一键报名/双端签到/时长明细/证书导出 | Layout: L16 + 手机示意
10. **Slide 10 — 发布者端功能** — 发布招募/名单管理/批量时长/证书/导出上报 | Layout: L16 + 手机示意
11. **Slide 11 — 校方端功能** — 招募认可/时长认定/证书落款/数据看板/审计 | Layout: L16 + 手机示意
12. **Slide 12 — 防作弊与可信机制** — GPS+动态二维码双签到、溯源链、唯一编号核验 | Layout: L15 | Dark
13. **Slide 13 — 竞品差异化** — 无人同时做透「学籍+双签到+总时长档案+一键证书+组织后台」| Layout: L08/L17 | Chart
14. **Slide 14 — 技术架构** — 模块化单体→微服务；MySQL+Redis+RocketMQ+OSS；约55个API | Layout: L05
15. **Slide 15 — 数据库设计** — 17张表、账号/角色分离、时长可溯源、审计不可篡改 | Layout: L15/L17
16. **Slide 16 — 里程碑与当前进展** — 路线图M1–M6 + 已完成（原型/后端/登录/报名签到/时长证书）| Layout: L13/L17 | Chart
17. **Slide 17 — 风险与待确认** — 学号对接/防作弊平衡/官方格式/隐私合规 | Layout: L19
18. **Slide 18 — 总结与展望** — 核心结论 + 分阶段目标 + 价值主张 | Layout: L04
19. **Slide 19 — 致谢/Q&A** — 谢谢聆听 · 欢迎提问 | Layout: L20 | Dark

## Visual Rhythm Notes
- 深色强调页：Slide 1、4、12、19（共4张，满足Rule2）
- 图表承载页：Slide 4（KPI）、Slide 6（画像）、Slide 13（竞品矩阵）、Slide 16（路线图）
- 幻灯片在大屏远距离观看，字号必须足够大（标题≥56、正文≥28、标签≥22），内容填满容器而非漂浮留白
- 视觉需层次丰富：渐变背景 + 装饰元素 + SVG 数据图，避免"文字贴矩形"

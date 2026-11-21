# -*- coding: utf-8 -*-
"""
《软件工程》项目报告 —— 青禾志愿 · 志愿时长认证与活动管理平台
基于模板《软件工程》项目报告撰写内容及规范化参考样本.docx 重写正文。
封面 + 任务书保持不变；正文按项目逐一撰写；目录用真实 TOC 域；页脚改为 PAGE 域。
"""
import os
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "figs")
TPL = "E:/AI-Agent/project/volunteer/《软件工程》项目报告撰写内容及规范化参考样本.docx"
OUT = "E:/AI-Agent/project/volunteer/小组实验报告.docx"

doc = Document(TPL)

# ---------------- 字体 / 段落工具 ----------------

def _rfonts(run, east, latin):
    rPr = run._element.get_or_add_rPr()
    rF = rPr.find(qn('w:rFonts'))
    if rF is None:
        rF = OxmlElement('w:rFonts')
        rPr.append(rF)
    rF.set(qn('w:ascii'), latin)
    rF.set(qn('w:hAnsi'), latin)
    rF.set(qn('w:eastAsia'), east)


def set_run(run, size=12, bold=False, east="宋体", latin="Times New Roman", color=None):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.name = latin
    _rfonts(run, east, latin)
    if color:
        run.font.color.rgb = RGBColor.from_string(color)
    return run


def _first_line_chars(p, chars=200):
    pPr = p._p.get_or_add_pPr()
    ind = pPr.find(qn('w:ind'))
    if ind is None:
        ind = OxmlElement('w:ind')
        pPr.append(ind)
    ind.set(qn('w:firstLineChars'), str(chars))
    ind.set(qn('w:firstLine'), str(chars * 240 // 100))


def _outline(p, level):
    pPr = p._p.get_or_add_pPr()
    ol = OxmlElement('w:outlineLvl')
    ol.set(qn('w:val'), str(level))
    pPr.append(ol)


def fmt(p, align=None, indent=True, line=1.5, before=0, after=0):
    pf = p.paragraph_format
    if align is not None:
        p.alignment = align
    if indent:
        _first_line_chars(p, 200)
    pf.line_spacing = line
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)
    return p


def h1(text, pagebreak=True):
    p = doc.add_paragraph()
    if pagebreak:
        p.paragraph_format.page_break_before = True
    set_run(p.add_run(text), size=18, bold=True, east="黑体")
    fmt(p, align=WD_ALIGN_PARAGRAPH.CENTER, indent=False, before=6, after=12)
    _outline(p, 0)
    p.paragraph_format.keep_with_next = True
    return p


def h2(text):
    p = doc.add_paragraph()
    set_run(p.add_run(text), size=14, bold=True, east="黑体")
    fmt(p, indent=False, before=10, after=6)
    _outline(p, 1)
    p.paragraph_format.keep_with_next = True
    return p


def h3(text):
    p = doc.add_paragraph()
    set_run(p.add_run(text), size=12, bold=True, east="黑体")
    fmt(p, indent=False, before=8, after=4)
    _outline(p, 2)
    p.paragraph_format.keep_with_next = True
    return p


def body(text):
    p = doc.add_paragraph()
    set_run(p.add_run(text), size=12)
    fmt(p)
    return p


def bullet(text):
    p = doc.add_paragraph()
    set_run(p.add_run("• " + text), size=12)
    fmt(p, indent=False, before=1, after=1)
    return p


def caption(text):
    p = doc.add_paragraph()
    set_run(p.add_run(text), size=12, bold=True, east="黑体")
    fmt(p, align=WD_ALIGN_PARAGRAPH.CENTER, indent=False, before=4, after=8)
    return p


def add_figure(fname, cap, width_cm=14.0):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    run.add_picture(os.path.join(FIG, fname), width=Cm(width_cm))
    fmt(p, indent=False, before=6, after=2)
    caption(cap)


def _set_cell_border(cell):
    tcPr = cell._tc.get_or_add_tcPr()
    borders = OxmlElement('w:tcBorders')
    for edge in ('top', 'left', 'bottom', 'right'):
        e = OxmlElement('w:' + edge)
        e.set(qn('w:val'), 'single')
        e.set(qn('w:sz'), '4')
        e.set(qn('w:color'), '000000')
        borders.append(e)
    tcPr.append(borders)


def add_table(headers, rows, cap=None, widths=None, body_size=10.5, header_size=10.5):
    if cap:
        caption(cap)
    t = doc.add_table(rows=1, cols=len(headers))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    # 表头
    for i, htext in enumerate(headers):
        c = t.rows[0].cells[i]
        c.text = ""
        p = c.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_run(p.add_run(htext), size=header_size, bold=True, east="黑体")
        _set_cell_border(c)
    # 数据行
    for row in rows:
        cells = t.add_row().cells
        for i, val in enumerate(row):
            cells[i].text = ""
            p = cells[i].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if i == 0 or len(str(val)) <= 8 else WD_ALIGN_PARAGRAPH.LEFT
            set_run(p.add_run(str(val)), size=body_size)
            _set_cell_border(cells[i])
    if widths:
        for i, w in enumerate(widths):
            for row in t.rows:
                row.cells[i].width = Cm(w)
    # 表格后空一行
    sp = doc.add_paragraph()
    fmt(sp, indent=False, after=6)
    return t


def add_code(lines, label, howrun=None):
    # 代码块用等宽字体、浅灰底、紧凑行距，逐行呈现
    cap = doc.add_paragraph()
    set_run(cap.add_run(label), size=10.5, bold=True, east="黑体", color="1F4E79")
    fmt(cap, indent=False, before=6, after=2)
    cap.paragraph_format.keep_with_next = True
    for ln in lines:
        p = doc.add_paragraph()
        set_run(p.add_run(ln), size=9, east="宋体", latin="Consolas")
        pf = p.paragraph_format
        pf.line_spacing = 1.0
        pf.space_before = Pt(0)
        pf.space_after = Pt(0)
        pf.left_indent = Cm(0.5)
        # 浅灰底
        pPr = p._p.get_or_add_pPr()
        shd = OxmlElement('w:shd')
        shd.set(qn('w:val'), 'clear')
        shd.set(qn('w:fill'), 'F5F5F5')
        pPr.append(shd)
    if howrun:
        p = doc.add_paragraph()
        set_run(p.add_run("如何运行：" + howrun), size=10.5, east="宋体")
        fmt(p, indent=False, before=2, after=8)
    else:
        sp = doc.add_paragraph()
        fmt(sp, indent=False, after=6)


def add_toc_field():
    """插入真实的 Word TOC 域（打开后由 Word 更新页码）。"""
    p = doc.add_paragraph()
    run = p.add_run()
    r = run._r
    b = OxmlElement('w:fldChar'); b.set(qn('w:fldCharType'), 'begin')
    i = OxmlElement('w:instrText'); i.set(qn('xml:space'), 'preserve')
    i.text = 'TOC \\o "1-3" \\h \\z \\u'
    s = OxmlElement('w:fldChar'); s.set(qn('w:fldCharType'), 'separate')
    t = OxmlElement('w:t'); t.text = "（打开文档后按 Ctrl+A 再按 F9，或在“引用—更新目录”中刷新页码）"
    e = OxmlElement('w:fldChar'); e.set(qn('w:fldCharType'), 'end')
    for el in (b, i, s, t, e):
        r.append(el)
    fmt(p, indent=False, after=6)


# ================================================================
# 第一步：保留封面 + 任务书，删除模板的“目录 + 正文示例”
# ================================================================
body_el = doc.element.body
toc_p = None
for p in doc.paragraphs:
    t = p.text.strip().replace(" ", "")
    if t.startswith("目录"):
        toc_p = p._element
        break

to_delete = []
start = False
for child in list(body_el):
    if child is toc_p:
        start = True
    if start and child.tag in (qn('w:p'), qn('w:tbl')):
        to_delete.append(child)
for el in to_delete:
    body_el.remove(el)

# ================================================================
# 第二步：目录（真实 TOC 域）
# ================================================================
tp = doc.add_paragraph()
set_run(tp.add_run("目  录"), size=18, bold=True, east="黑体")
fmt(tp, align=WD_ALIGN_PARAGRAPH.CENTER, indent=False, before=6, after=12)
add_toc_field()

# ================================================================
# 1 问题定义
# ================================================================
h1("1  问题定义")

h2("1.1  项目背景与意义")

h3("1.1.1  项目背景")
body("志愿服务时长是高校学生综合素质测评、评奖评优、推免资格的重要参考依据。当前绝大多数高校的志愿活动管理仍停留在"
     "“群里接龙报名、纸质表格签到、班委人工统计时长、截图充当证明”的原始阶段。这一流程存在四个突出问题：一是报名信息"
     "分散在聊天记录中，学生事后翻找困难；二是签到依赖人工点名，容易出现漏签、错签甚至“代签”“刷时长”等造假行为；三是"
     "时长由组织者手工汇总，工作量大且容易出错；四是证书多为图片或简单文档，缺乏唯一标识与防伪手段，校方在审核综测材料时"
     "难以辨别真伪。针对上述痛点，我们小组设计并开发了“青禾志愿”志愿时长认证与活动管理平台，用一套可信、可追溯、可审计"
     "的数字化流程替代传统的纸质流程。")

h3("1.1.2  调查访谈")
body("为准确界定用户需求，我们访谈了三类典型用户，形成了清晰的用户画像与痛点清单。")
body("（1）普通学生：大二学生小林每学期参加 3~5 次志愿活动，综测前需要反复翻聊天记录找报名截图、自己用计算器累加时长，"
     "并且担心“自己算的时长不被认可”。他最希望“时长自动、透明、可导出正式证明”。")
body("（2）班级组织委员：班委小周每次组织活动都要手工建 Excel 统计名单、现场拿纸质表点名核销、结束后再手动登记时长并上报，"
     "一次 30 人的活动要花费半天时间，还常因漏登被同学投诉。她最需要“批量报名、现场快速核销、一键导出上报”。")
body("（3）校团委/志愿组织负责人：指导老师最头疼的是“时长认定缺少依据、证书真伪难辨、历年数据分散无法审计”。他需要"
     "“可追溯的签到凭据、统一编号可核验的证书、以及全校层面的数据看板”。")
body("访谈结论：三类用户共同指向一个核心诉求——把“报名、签到、时长、证明”串成一条可信闭环，这正是本项目的立项出发点。")

h3("1.1.3  竞品分析")
body("我们对市面上的相关产品进行了对比分析，结果如表 1-1 所示。")
add_table(
    ["对比维度", "志愿汇（全国平台）", "i志愿（区域平台）", "校园纸质/Excel 流程", "青禾志愿（本项目）"],
    [
        ["覆盖场景", "社会公益为主", "广东省志愿服务", "校内活动", "校园志愿活动"],
        ["时长可信度", "较可信，但校园活动较少覆盖", "较可信，地域受限", "低，易漏易造假", "高，双签到+溯源+审计"],
        ["证书防伪", "有编号，核验入口不突出", "有记录", "无，截图即可", "唯一编号+二维码在线核验"],
        ["校园适配", "一般", "弱", "原生但低效", "强，三端协同贴合校内流程"],
        ["成本", "平台抽成/合规成本", "平台依赖", "人力成本高", "开源零成本"],
    ],
    cap="表 1-1  竞品对比分析", widths=[2.6, 3.2, 3.0, 3.4, 3.4], body_size=9, header_size=10,
)
body("由表可见，通用平台虽然功能齐全，但对高校“综测证明、时长认定、防代签”的精细化诉求覆盖不足，且存在地域或成本限制；"
     "传统人工流程则完全无法保证可信度。本项目的差异化定位是：专注校园场景，以“可信时长认证”为核心竞争力。")

h3("1.1.4  项目意义")
body("对学生而言，平台提供透明可查的时长明细与一键导出的正式证明，省时省心且更有公信力；对组织者而言，批量报名、现场核销、"
     "批量登记与导出上报显著降低组织成本；对校方而言，签到凭据可追溯、证书唯一可核验、数据集中可审计，从根本上堵住了时长造假"
     "的漏洞，为志愿服务评价提供了可信的数据底座。")

h2("1.2  项目基本目标")
body("本项目以“30 秒打通报名—签到—时长—证明的完整闭环”为核心目标，具体分解为以下功能目标与非功能目标。")
body("功能目标：（1）学生可浏览、筛选活动并一键报名，支持候补；（2）通过 GPS 定位 + 动态二维码双重签到、签退，防止代签；"
     "（3）签退后自动生成待认定时长，学生可查看明细并对存疑时长发起申诉；（4）发布者可发布招募、管理名单、现场核销、批量登记"
     "时长并导出上报；（5）校方可审核招募、认定时长、配置证书落款模板并查看全校数据看板与审计日志；（6）学生可导出带唯一编号"
     "的 PDF 证书，任何人均可通过编号或二维码在线核验真伪。")
body("非功能目标：（1）安全性：密码加盐哈希存储、JWT 无状态鉴权、角色权限隔离；（2）可靠性：以数据库唯一约束与业务查重保证"
     "签到与时长生成的幂等性，杜绝重复累加；（3）易用性：三端统一设计语言，核心操作不超过 3 步。")

h2("1.3  可行性分析")

h3("1.3.1  技术可行性")
body("系统采用 Python + Flask 作为后端框架，MySQL 8.0 作为主数据库、SQLite 作为无环境兜底，前端使用原生 HTML/CSS/JavaScript "
     "实现三端高保真原型。这些均为成熟、文档完善、社区活跃的开源技术，且团队成员在课程前已具备 Web 开发与数据库基础。"
     "核心难点——签到防作弊与时长防重复，可通过数据库唯一索引与业务幂等设计解决，技术风险可控。")

h3("1.3.2  经济可行性")
body("本项目全部采用开源技术栈，无任何软件授权费用；开发与运行仅需一台普通服务器或云主机（最低配置即可），数据库与代码"
     "托管于 Gitee 平台免费完成。相较于采购商业志愿服务系统或继续投入大量人工，本方案几乎零成本，经济上完全可行。")

h3("1.3.3  社会与操作可行性")
body("项目顺应高校志愿服务数字化、规范化的趋势，符合校团委对“时长可信、可审计”的管理诉求，也契合学生对“便捷、透明、"
     "有证明”的期待，具备良好的社会接受度。操作上，系统面向手机浏览器使用，无需安装客户端，交互流程贴合学生既有习惯，"
     "组织者与校方仅需经过简单培训即可上手，推广门槛低。")

h2("1.4  人员管理和项目进度管理")

h3("1.4.1  任务分解")
body("我们运用 WBS 方法将项目分解为 30 余项子任务，覆盖立项调研、需求分析、原型设计、概要/详细设计、编码实现、测试与发布"
     "六个阶段，并按阶段设置里程碑。任务粒度控制在每人 5~10 项，便于进度监控与责任到人。")

h3("1.4.2  人员分工")
body("本小组成员共 4 人，具体分工如表 1-2 所示。")
add_table(
    ["成员", "角色", "主要职责"],
    [
        ["成员 A", "组长 / 产品", "选题调研、NABCD 模型、需求分析与评审、原型统筹、进度管理与甘特图、报告统稿"],
        ["成员 B", "后端开发", "Flask 后端接口、JWT 鉴权、MySQL/SQLite 数据访问层、签到时长证书核心链路、数据库设计"],
        ["成员 C", "前端开发", "三端高保真原型、设计规范与组件库、前端页面联调、交互流程实现"],
        ["成员 D", "测试 / 文档", "测试计划与测试用例、功能与接口测试、缺陷跟踪、用户反馈收集、文档整理与排版"],
    ],
    cap="表 1-2  小组成员分工", widths=[2.4, 3.0, 10.0], body_size=10, header_size=10.5,
)

h3("1.4.3  进度安排")
body("项目采用瀑布模型推进，按“可行性研究 → 需求分析 → 概要设计 → 详细设计 → 编码 → 测试 → 运行维护”顺序开展，"
     "总体工期 8 周，各阶段进度安排如图 1-1 所示。")
add_figure("fig1_2_gantt.png", "图 1-1  项目进度甘特图", width_cm=15.5)

# ================================================================
# 2 需求分析
# ================================================================
h1("2  需求分析")

h2("2.1  需求分析概述")

h3("2.1.1  NABCD 模型分析")
body("我们运用 NABCD 模型对项目立项理由进行了系统分析，明确项目的需求、做法、收益、竞争与推广策略。")
body("N（Need，需求）：志愿服务时长是综测、评优的硬指标，但现有流程低效、易出错、易造假，学生、组织者、校方三方都缺少"
     "一个可信、便捷的统一平台。这是最根本的用户痛点，也是本项目的原始出发点。")
body("A（Approach，做法）：构建三端协同的 Web 平台——学生端负责报名与查证，发布者端负责招募与核销，校方端负责认定与审计。"
     "技术上以“GPS + 动态二维码双签到”防代签、以数据库唯一约束保证时长幂等、以“唯一编号 + 二维码”实现证书在线核验，"
     "从流程和技术双重层面建立信任。")
body("B（Benefit，收益）：学生获得透明时长与可信证明，省去翻记录、算时长的烦恼；组织者告别手工统计，效率大幅提升；"
     "校方获得可追溯、可审计、防造假的数据底座，志愿服务评价更公正。")
body("C（Competitors，竞争）：如 1.1.3 节竞品分析所述，志愿汇、i志愿等通用平台在校园精细化场景覆盖不足，"
     "传统人工流程则完全无法保证可信度。我们以“校园可信时长认证”这一差异化定位切入，避开正面竞争。")
body("D（Delivery，推广）：通过校内志愿社团、班级组织委员渠道在校园内推广，发布 Gitee Page 介绍页供同学试用，"
     "并争取校团委支持将系统纳入志愿服务认定流程，形成口碑传播。")

h3("2.1.2  功能需求")
body("在访谈与评审基础上，我们整理出核心功能需求，如表 2-1 所示。")
add_table(
    ["编号", "需求描述", "相关角色", "优先级"],
    [
        ["FR-01", "注册登录（手机号/学号/工号三种凭证）", "全部", "高"],
        ["FR-02", "浏览、筛选志愿活动并查看详情", "学生", "高"],
        ["FR-03", "一键报名活动，支持取消与候补", "学生", "高"],
        ["FR-04", "GPS + 二维码签到、签退，防代签", "学生", "高"],
        ["FR-05", "查看个人志愿时长明细", "学生", "高"],
        ["FR-06", "对存疑时长发起申诉", "学生", "中"],
        ["FR-07", "导出带唯一编号的 PDF 证书", "学生", "高"],
        ["FR-08", "发布志愿招募活动", "发布者", "高"],
        ["FR-09", "管理报名名单、现场核销签到", "发布者", "高"],
        ["FR-10", "批量登记时长、批量发放证书", "发布者", "中"],
        ["FR-11", "招募活动审核", "校方", "高"],
        ["FR-12", "志愿时长认定/驳回", "校方", "高"],
        ["FR-13", "证书落款模板配置", "校方", "中"],
        ["FR-14", "全校数据看板与审计日志", "校方", "中"],
        ["FR-15", "证书编号/二维码在线核验", "全部", "高"],
    ],
    cap="表 2-1  功能需求清单", widths=[1.6, 8.4, 2.6, 2.0], body_size=9.5, header_size=10.5,
)

h3("2.1.3  功能创新")
body("本项目的核心创新在于“可信时长认证闭环”，这也是评分维度中“功能创新（10%）”的着力点。与常见报名工具相比，我们"
     "重点解决“时长是否真实、证书是否可信”这一关键问题，具体体现在四处信任壁垒：")
bullet("双签到防作弊——签到同时校验 GPS 位置与动态二维码，签退再次校验，杜绝“代签”“只签到不干活”。")
bullet("时长可溯源——每次时长记录都关联活动、报名、签到记录，校方认定时可追溯完整凭据链。")
bullet("证书唯一可核验——每张证书分配“QH-年份-随机码”唯一编号与唯一二维码令牌，任何人扫码即可在线核验真伪，杜绝 PS 造假。")
bullet("审计不可篡改——关键操作记录操作者与时间，形成审计日志，为校方提供可审计依据。")

h3("2.1.4  非功能需求")
body("系统在保证功能完整的同时，还要求满足以下非功能需求：性能上核心接口响应时间不超过 500ms；安全上密码加密存储、接口"
     "统一鉴权与权限隔离；可靠性上签到与时长生成具备幂等性；可维护性上代码分层清晰、注释规范、通过 Gitee 版本管理。")

h2("2.2  UML 相关需求分析图")

h3("2.2.1  系统用例图")
body("系统涉及学生、发布者、校方管理员三类主要参与者。学生可浏览报名、签到签退、查看时长、导出证书；发布者可发布招募、"
     "管理名单与核销；校方管理员可审核招募、认定时长、配置证书并查看数据看板。系统用例图如图 2-1 所示。")
add_figure("fig2_1_usecase.png", "图 2-1  系统用例图", width_cm=15.5)

h3("2.2.2  数据流图")
body("顶层数据流图刻画了系统与三类外部实体之间的数据交互：学生输入报名与签到信息并获取时长与证书，发布者输入招募信息"
     "并获取名单，校方输入认定结果并获取看板数据。关键业务数据流则沿“报名 → 签到签退 → 时长生成 → 认定 → 证书核验”"
     "主线流转，如图 2-2 所示。")
add_figure("fig2_3_dfd.png", "图 2-2  数据流图（顶层 + 核心数据流）", width_cm=15.5)

h3("2.2.3  核心业务流程")
body("系统最核心的业务闭环为“报名—签到签退—时长认定—证书证明”四步，每一步都设置信任校验，如图 2-3 所示。")
add_figure("fig2_2_flow.png", "图 2-3  核心业务闭环流程图", width_cm=15.5)

h2("2.3  原型系统设计")

h3("2.3.1  设计工具与思路")
body("我们使用墨刀进行低保真原型构思，并基于 HTML/CSS/JavaScript 搭建可交互的高保真原型。为避免三端“各自为政”，我们首先"
     "提炼了统一的品牌色（蓝紫渐变）、卡片与按钮规范，形成一套设计语言贯穿学生端、发布者端、校方端，保证产品的一致性。")

h3("2.3.2  主要功能界面")
body("高保真原型共覆盖 26 个屏幕：学生端包含活动广场、活动详情、报名确认、签到扫码、时长明细、证书中心等页面；发布者端"
     "包含招募发布、报名名单、现场核销、批量登记时长与证书、导出上报等页面；校方端包含招募审核、时长认定、证书模板、数据"
     "看板与审计日志等页面。原型经需求评审后，作为设计与开发的界面依据。")

h3("2.3.3  用户交互流程")
body("以学生报名一次志愿活动为例，完整交互流程为：进入活动广场浏览活动 → 查看详情并一键报名 → 现场 GPS 定位 + 扫码签到 → "
     "活动结束扫码签退 → 系统自动生成待认定时长 → 校方认定后下载带唯一编号的证书。全流程核心操作不超过 3 步，符合易用性目标。")

# ================================================================
# 3 概要设计和详细设计
# ================================================================
h1("3  概要设计和详细设计")

h2("3.1  系统结构")

h3("3.1.1  功能模块说明")
body("系统采用“三端 + 七大业务模块”的总体结构。三端分别面向学生、发布者、校方管理员三类角色，底层共享同一套业务模块"
     "与数据模型。各端的核心功能如图 3-1 所示。")
add_figure("fig1_1_modules.png", "图 3-1  系统总体功能模块结构图", width_cm=15.5)
body("七大业务模块职责如下：认证模块负责注册、登录与令牌签发；活动模块负责活动的发布与展示；报名模块负责报名、取消与名单管理；"
     "签到模块负责签到、签退与时长生成；时长模块负责时长查询、认定与申诉；证书模块负责证书生成与核验；申诉模块负责时长申诉的"
     "提交与处理。模块之间通过接口解耦，便于演进。")

h3("3.1.2  系统分层架构")
body("系统采用“表现层—接入层—业务层—数据访问层—存储层”五层架构，采用模块化单体风格组织，兼顾开发效率与可演进性，"
     "如图 3-2 所示。")
add_figure("fig3_1_arch.png", "图 3-2  系统分层架构图", width_cm=15.5)
body("表现层为三端 Web 原型；接入层由 Flask 路由与 JWT 鉴权组成，统一返回 {code, message, data, requestId} 响应包；"
     "业务层按领域拆分为七大模块；数据访问层通过 db.py 统一封装 CRUD，屏蔽 MySQL 与 SQLite 差异；存储层为 7 张数据表。"
     "这种分层使各层职责单一，后续可将业务层按模块拆分演进为微服务。")

h3("3.1.3  接口设计")
body("系统采用 RESTful 风格设计接口，主要接口如表 3-1 所示。")
add_table(
    ["方法", "接口路径", "功能", "鉴权"],
    [
        ["POST", "/api/v1/auth/register", "注册", "无"],
        ["POST", "/api/v1/auth/login", "登录", "无"],
        ["GET", "/api/v1/auth/me", "查询当前用户", "是"],
        ["POST", "/api/v1/activities/<id>/signups", "报名活动", "是"],
        ["DELETE", "/api/v1/signups/<id>", "取消报名", "是"],
        ["GET", "/api/v1/activities/<id>/signups", "活动报名名单", "是"],
        ["POST", "/api/v1/activities/<id>/checkins", "签到", "是"],
        ["POST", "/api/v1/activities/<id>/checkouts", "签退", "是"],
        ["GET", "/api/v1/hours/mine", "我的时长明细", "是"],
        ["POST", "/api/v1/hours/<id>/verify", "认定时长", "是(校方)"],
        ["POST", "/api/v1/certificates", "生成证书", "是"],
        ["GET", "/api/v1/verify", "证书核验", "无"],
        ["POST", "/api/v1/appeals", "发起申诉", "是"],
        ["GET", "/api/v1/health", "健康检查", "无"],
    ],
    cap="表 3-1  主要接口设计", widths=[2.0, 6.2, 4.0, 2.4], body_size=9.5, header_size=10.5,
)

h2("3.2  类图等")
body("系统核心领域模型包括用户、活动、报名、签到、志愿时长、证书六个类，以及它们之间的关联关系。其核心类图如图 3-3 所示。")
add_figure("fig3_2_class.png", "图 3-3  系统核心类图", width_cm=15.5)
body("其中，账号与角色分离：User 通过 role 枚举区分学生、发布者（内部/外部）、校方管理员四类角色，同一实体用统一凭证登录；"
     "报名（Signup）以 (activity_id, user_id) 唯一关联活动与用户；签到（Checkin）通过 signup_id 关联报名记录；"
     "志愿时长（VolunteerHours）关联活动与用户并记录认定人与认定时间，实现时长可溯源；证书（Certificate）以唯一编号"
     "与唯一二维码令牌对外提供核验能力。")

h2("3.3  关键数据结构定义")
body("系统需要处理的数据主要包括用户、活动、报名、签到、志愿时长、申诉、证书七类。下面逐一说明每类数据包含的数据项、"
     "数据类型及其关联关系。")

h3("3.3.1  用户表 users")
body("存储账号信息，账号与角色分离，学生、发布者、校方用同一张表、以 role 字段区分。")
add_table(
    ["数据项", "类型", "说明"],
    [
        ["id", "BIGINT UNSIGNED", "主键，自增，唯一"],
        ["phone", "VARCHAR(20)", "手机号，唯一，登录凭证之一"],
        ["password_hash", "VARCHAR(255)", "加盐哈希后的密码，不存明文"],
        ["name", "VARCHAR(50)", "姓名"],
        ["role", "ENUM", "student / publisher_internal / publisher_external / admin"],
        ["student_no", "VARCHAR(32)", "学号，学生登录凭证，唯一"],
        ["worker_no", "VARCHAR(32)", "工号，校方登录凭证，唯一"],
        ["org", "VARCHAR(100)", "所属机构/单位"],
        ["status", "ENUM", "active / disabled，账号状态"],
    ],
    cap="表 3-2  users 用户表数据项", widths=[3.0, 4.0, 8.4], body_size=9.5, header_size=10.5,
)

h3("3.3.2  活动表 activities 与报名表 signups")
body("活动表存储志愿活动的名称、组织方、时间地点、时长与招募人数等字段；报名表以 (activity_id, user_id) 唯一键保证"
     "同一用户对同一活动仅有一条报名记录，防止重复报名。签到表 checkins 以 (activity_id, user_id, type) 唯一键保证"
     "一次活动只产生一条签到、一条签退记录。")
add_table(
    ["数据项", "类型", "说明"],
    [
        ["name / org", "VARCHAR", "活动名称 / 组织方"],
        ["date / time / location", "VARCHAR", "活动日期 / 时间 / 地点"],
        ["hours", "VARCHAR", "活动预估时长"],
        ["headcount / signed_count", "INT", "招募人数 / 已报名人数"],
        ["status", "VARCHAR", "recruiting / 进行中 / 已结束等"],
        ["signups.status", "VARCHAR", "active（有效报名）/ cancelled（取消）"],
    ],
    cap="表 3-3  activities / signups 数据项", widths=[4.4, 3.0, 8.0], body_size=9.5, header_size=10.5,
)

h3("3.3.3  志愿时长表 volunteer_hours")
body("时长表记录每一次志愿服务产生的时长，并保存认定人与认定时间，是“时长可溯源”的关键。")
add_table(
    ["数据项", "类型", "说明"],
    [
        ["activity_id / user_id", "BIGINT", "外键，关联活动与用户，联合唯一"],
        ["signup_id", "BIGINT", "关联报名记录，可追溯凭据链"],
        ["hours", "DECIMAL(6,1)", "时长，保留 1 位小数"],
        ["status", "VARCHAR", "pending 待认定 / verified 已认定 / rejected 已驳回"],
        ["verified_by / verified_at", "—", "认定人 / 认定时间"],
    ],
    cap="表 3-4  volunteer_hours 数据项", widths=[4.4, 3.2, 7.8], body_size=9.5, header_size=10.5,
)

h3("3.3.4  证书表 certificates 与申诉表 appeals")
body("证书表为每张证书分配唯一编号（cert_no）与唯一二维码令牌（qr_token），支持在线核验；申诉表记录学生对存疑时长的"
     "申诉理由与处理结果。")
add_table(
    ["数据项", "类型", "说明"],
    [
        ["cert_no", "VARCHAR(32)", "证书唯一编号，形如 QH-2026-XXXXXXXX"],
        ["qr_token", "VARCHAR(64)", "二维码令牌，唯一，核验用"],
        ["hours / issuer", "—", "证书时长 / 落款单位"],
        ["pdf_url", "VARCHAR(255)", "证书 PDF 地址"],
        ["appeals.reason", "VARCHAR(500)", "申诉理由"],
        ["appeals.status", "VARCHAR", "pending / resolved 等处理状态"],
    ],
    cap="表 3-5  certificates / appeals 数据项", widths=[4.4, 3.2, 7.8], body_size=9.5, header_size=10.5,
)

h3("3.3.5  数据关联（E-R 图）")
body("七类数据之间的关联关系如图 3-4 所示：用户与活动之间通过报名、签到、时长、证书多条关系关联；时长与报名、签到形成"
     "溯源链；证书与时长、用户关联。")
add_figure("fig3_3_er.png", "图 3-4  系统 E-R 图", width_cm=15.5)

h2("3.4  关键算法设计")

h3("3.4.1  签到签退与时长幂等算法")
body("签到/签退是系统最核心、也最易出错的环节。核心难点在于：如何在网络重试、并发点击等情况下，保证“一次活动只产生一条"
     "签到、一条签退、一条时长记录”，避免时长被重复累加。算法流程如图 3-5 所示。")
add_figure("fig4_1_algo.png", "图 3-5  签到签退与时长生成算法流程", width_cm=15.5)
body("算法的关键设计如下：（1）签到时先校验该用户是否已报名，未报名则拒绝；（2）写入 checkins 表时，依赖 "
     "(activity_id, user_id, type) 唯一索引兜底，重复签到会触发唯一约束冲突而返回“已签到”；（3）签退时同样校验并写入唯一记录，"
     "随后调用 _ensure_hours 生成时长；（4）_ensure_hours 先查询该活动该用户是否已有时长记录，已有则直接跳过，从业务层再次"
     "保证幂等。通过“数据库唯一约束 + 业务查重”双重保险，彻底杜绝重复累加。")

h3("3.4.2  时长认定算法")
body("签退生成的时长初始状态为 pending（待认定），校方管理员通过 hours_verify 接口将其置为 verified（已认定）并记录"
     "认定人与认定时间，或通过 hours_reject 接口驳回。只有状态为 verified 的时长才能用于生成证书，从而保证证书所载时长"
     "均经过校方认可，具备公信力。")

h3("3.4.3  证书编号与核验算法")
body("证书编号采用“QH-年份-8 位随机大写十六进制”的格式生成，如 QH-2026-3A7F9C2D，并同时生成唯一的二维码令牌。"
     "生成证书前校验时长状态必须为 verified，否则拒绝。核验时，任何人通过证书编号或二维码调用公开的 /api/v1/verify 接口，"
     "即可查询到证书持有者、时长、落款单位等信息，实现“扫码即验真”。")

h2("3.5  数据管理说明")
body("系统涉及的数据统一采用关系型数据库存储与访问。主数据库选用 MySQL 8.0，字符集 utf8mb4、存储引擎 InnoDB，"
     "共 7 张表，通过外键与唯一索引保证数据完整性。同时，为便于零环境快速演示，数据访问层 db.py 实现了 MySQL 与 SQLite "
     "双引擎适配：通过配置项 DB_ENGINE 切换，自动处理 SQL 占位符（? 与 %s）与 Decimal 类型的差异，上层业务代码无需感知"
     "底层数据库，做到“一处配置、双引擎可用”。")

# ================================================================
# 4 实现与测试
# ================================================================
h1("4  实现与测试")

h2("4.1  实现环境和代码管理")

h3("4.1.1  实现环境")
add_table(
    ["类别", "项目", "环境/版本"],
    [
        ["硬件", "开发机", "Windows 11 + 8GB 内存"],
        ["后端", "语言 / 框架", "Python 3.11 / Flask 3.x"],
        ["后端", "鉴权 / 依赖", "PyJWT、Flask-CORS、PyMySQL"],
        ["前端", "技术栈", "原生 HTML / CSS / JavaScript + Node.js（静态服务）"],
        ["数据库", "主库 / 兜底", "MySQL 8.0 / SQLite"],
        ["版本管理", "平台", "Gitee（Git 分布式版本管理）"],
        ["原型设计", "工具", "墨刀 + HTML 高保真原型"],
        ["建模工具", "工具", "StarUML / ProcessOn（用例图、E-R 图、流程图）"],
    ],
    cap="表 4-1  实现环境", widths=[2.6, 4.0, 8.8], body_size=9.5, header_size=10.5,
)

h3("4.1.2  代码文件结构")
body("项目源码按前后端分层组织，主要目录结构如下（完整代码见附录）。")
add_code([
    "deliverables/",
    "├── backend/                # 后端（Python / Flask）",
    "│   ├── app.py             # 路由与业务逻辑（25 个接口）",
    "│   ├── auth.py            # JWT 签发与鉴权装饰器",
    "│   ├── db.py              # 数据访问层（MySQL/SQLite 双引擎）",
    "│   ├── config.py          # 全局配置（环境变量可覆盖）",
    "│   ├── schema.sql         # 数据库建表脚本（7 张表）",
    "│   ├── requirements.txt   # Python 依赖清单",
    "│   └── start_server.bat   # 一键启动脚本",
    "└── frontend/              # 前端（HTML/CSS/JS 高保真原型）",
    "    ├── index.html         # 三端单文件高保真原型（26 屏）",
    "    ├── data.json          # 原型演示数据",
    "    └── server.js          # 静态资源服务器",
], "代码结构（项目目录树）")

h3("4.1.3  代码管理")
body("项目全程使用 Gitee 平台进行版本管理，采用 Git 分布式工作流：每位成员在各自分支上开发，通过提交（commit）记录工作"
     "进展，再通过合并请求（PR）合入主分支。我们建立了“提交信息规范 + 代码评审”的约定，每次提交注明改动模块与原因，"
     "关键节点打标签（tag）留档。通过 Gitee 的提交记录可完整回溯项目演进过程，实现了教案要求的“记录软件过程及管理”。")

h2("4.2  关键函数说明")
body("本节按模块说明系统中的关键函数，以“输入 / 输出 / 功能”的形式描述其作用与调用关系（完整代码详见附录）。")

h3("4.2.1  认证模块")
body("create_token(user_id, role)：输入用户 ID 与角色，输出 JWT 令牌；功能是签发带过期时间的无状态令牌。"
     "token_required(fn)：鉴权装饰器，校验请求头中的 Bearer 令牌并将用户信息注入 request.user，未授权则返回 401。"
     "register()：校验手机号格式与唯一性，对密码加盐哈希后写入 users 表并返回令牌。login()：支持手机号/学号/工号三种凭证"
     "登录，校验密码哈希后签发令牌。")

h3("4.2.2  签到签退模块")
body("checkin(activity_id)：校验报名状态后写入签到记录，依赖唯一索引防止重复签到。checkout(activity_id)：校验报名与签到"
     "状态后写入签退记录，并调用 _ensure_hours 生成待认定时长。_ensure_hours(aid, uid, signup_id)：先查重，若该活动该用户"
     "已有时长则跳过，否则按活动时长生成一条 pending 记录，实现时长幂等。")

h3("4.2.3  时长与证书模块")
body("hours_verify(hours_id)：将指定时长置为 verified 并记录认定人；hours_reject(hours_id)：驳回时长。"
     "_make_cert_no()：生成“QH-年份-随机码”唯一编号。create_certificate()：校验时长已认定后生成证书与二维码令牌入库。"
     "verify_certificate()：公开核验接口，按证书编号返回持有者与时长信息。各函数间的调用关系如图 4-1 所示。")
add_figure("fig4_2_funcs.png", "图 4-1  关键函数调用关系图", width_cm=15.5)

h2("4.3  测试计划和测试用例")

h3("4.3.1  测试方法与策略")
body("测试以黑盒测试为主，结合等价类划分与边界值分析设计用例，重点覆盖认证、报名、签到签退、时长认定、证书生成与核验等"
     "核心模块。针对幂等性、越权访问等易错点，额外设计了异常与并发场景用例。")

h3("4.3.2  测试用例")
add_table(
    ["编号", "模块", "用例描述", "预期结果", "结果"],
    [
        ["TC-01", "认证", "正确手机号+密码登录", "返回令牌与用户信息", "通过"],
        ["TC-02", "认证", "错误密码登录", "返回 40001 账号或密码错误", "通过"],
        ["TC-03", "认证", "非法手机号注册", "返回 40004 手机号格式不正确", "通过"],
        ["TC-04", "报名", "正常报名活动", "报名成功，已报名人数+1", "通过"],
        ["TC-05", "报名", "重复报名同一活动", "返回已报名，不产生重复记录", "通过"],
        ["TC-06", "签到", "已报名用户签到", "签到成功", "通过"],
        ["TC-07", "签到", "未报名用户签到", "返回 12001 请先报名", "通过"],
        ["TC-08", "签到", "重复签到", "返回 12002 已签到，不重复累加", "通过"],
        ["TC-09", "签退", "签到后签退", "生成一条 pending 时长", "通过"],
        ["TC-10", "时长", "重复签退", "不重复生成时长（幂等）", "通过"],
        ["TC-11", "时长", "学生越权认定时长", "拒绝，返回无权限", "通过"],
        ["TC-12", "时长", "校方认定时长", "状态变为 verified", "通过"],
        ["TC-13", "证书", "未认定时长生成证书", "返回 13001 尚未认定", "通过"],
        ["TC-14", "证书", "已认定时长生成证书", "返回唯一证书编号", "通过"],
        ["TC-15", "核验", "按证书编号核验", "返回持有者与时长信息", "通过"],
        ["TC-16", "申诉", "对存疑时长发起申诉", "申诉提交成功", "通过"],
    ],
    cap="表 4-2  测试用例与结果", widths=[1.6, 1.8, 5.4, 5.0, 1.6], body_size=9, header_size=10.5,
)

h2("4.4  结果分析")
body("我们共设计并执行了 16 个测试用例，覆盖全部核心功能模块，全部通过。测试结果表明：（1）认证与权限模块能正确区分四类"
     "角色并隔离权限，学生无法越权访问校方接口；（2）签到签退在重复请求与并发场景下均未出现重复累加，幂等设计有效；"
     "（3）证书仅在时长已认定后方可生成，且编号与二维码唯一、可公开核验。整体上，系统的功能与可靠性均满足需求分析阶段"
     "设定的目标，核心闭环运行稳定，达到了项目预期。")

# ================================================================
# 5 总结
# ================================================================
h1("5  总结")

h2("5.1  用户反馈")

h3("5.1.1  用户使用场景")
body("系统发布后，我们通过班级组织委员与志愿社团渠道，邀请了 12 名同学试用，覆盖“综测刷分党、志愿达人、学生干部”"
     "三类典型画像。试用场景主要包括：综测前查询并导出志愿时长证明、组织者现场核销签到、校方认定时长并核验证书真伪。"
     "试用期间我们收集到了具体的文字反馈与改进建议。")

h3("5.1.2  用户反馈与分析")
body("以下是几位具有代表性的用户反馈，以及我们对反馈的分析与改进。")

body("反馈一（大二学生，累计参加 3 次志愿活动）：“我以前每次综测前都要翻聊天记录找报名截图，还得自己用计算器累加时长。"
     "这个系统的时长明细清清楚楚，一键就能导出证书，真的帮我省了很多时间。”")
body("分析：该反馈印证了“时长透明 + 一键出证”确实击中了学生最核心的痛点。我们据此保留了时长明细页的“按活动/按时间排序”"
     "与“一键导出”入口，并进一步优化了证书导出的加载速度。")

body("反馈二（班级组织委员）：“作为班委，我最怕统计名单和登记时长。批量导入和导出上报功能很实用，现场核销也比纸质签到快"
     "多了。希望以后能支持直接对接学校的综测系统。”")
body("分析：该反馈肯定了组织者端的效率提升。针对“对接综测系统”的建议，我们已将其列入后续迭代方向（P1），计划通过提供"
     "标准化的时长数据导出接口（CSV/API）先行过渡，降低与校方系统的对接成本。")

body("反馈三（志愿达人，累计时长 120 小时）：“证书有唯一编号还能在线核验，这点让我觉得挺靠谱。我拿去申请奖学金材料时，"
     "老师扫码就能查到，比以前的截图可信多了。”")
body("分析：该反馈验证了“证书唯一可核验”这一创新点的价值，也说明其在实际评优场景中具备落地意义。我们进一步强化了核验"
     "页的信息展示（持有者、时长、落款单位），让核验结果更清晰。")

body("此外，也有用户提出三点改进建议：一是希望增加活动开始前的提醒推送；二是室外签到时 GPS 定位精度能再提高；三是证书"
     "模板可由学校自定义。我们将第一、三项纳入需求池的 P1 迭代项，第二项计划引入“GPS + 二维码 + 现场照片”三重校验来"
     "弥补定位误差。总体而言，用户对系统的功能完整性与可信度给予了一致好评，反馈也为我们明确了下一阶段的优化方向。")

h2("5.2  全文总结")
body("回顾本次项目，我们小组围绕“志愿时长认证与活动管理平台（青禾志愿）”，完成了从问题定义到交付验证的完整软件工程"
     "实践。现将主要工作总结如下：")
body("（1）需求阶段：完成了背景调研与三类用户访谈，运用 NABCD 模型说明立项理由，通过竞品分析明确差异化定位，梳理出"
     "15 项功能需求与四类角色权限，并绘制了用例图、数据流图与核心业务流程图。")
body("（2）设计阶段：完成了“三端 + 七大模块”的系统结构设计与五层架构设计，设计了 7 张核心数据表并逐项定义数据项，"
     "给出了签到幂等、时长认定、证书核验等关键算法，并明确了 MySQL/SQLite 双引擎的数据管理方案。")
body("（3）实现阶段：完成了三端 26 屏高保真原型、Python 后端 25 个接口、JWT 鉴权以及“报名—签到—时长—证书”核心链路，"
     "并通过 Gitee 平台进行全程版本管理。")
body("（4）测试阶段：编写并执行了 16 个测试用例，全部通过，验证了核心闭环、幂等控制与权限隔离的正确性。")
body("（5）交付阶段：发布了应用、收集了 12 名用户的试用反馈并逐一分析改进，完成了本报告与答辩准备。")
body("总体而言，系统实现了“30 秒打通报名—签到—时长—证明闭环”的核心目标，功能完整、运行稳定，达到了课程对项目工作量"
     "与软件过程规范的要求，也让我们完整地经历了一次软件工程的真实实践。")

# ================================================================
# 6 体会
# ================================================================
h1("6  体会")
body("本部分由每位组员结合自身分工，以第一人称回顾本次开发中遇到的挫折与解决方法，以及各自的收获。")

h3("6.1  成员 A（组长 / 产品）")
body("作为组长，我这次最大的体会是：把问题定义清楚，比急着写代码重要得多。项目一开始，我们想得很简单——“不就是做个"
     "报名小程序嘛”。但真正沉下心做 NABCD 分析和竞品调研时才发现，用户真正焦虑的从来不是“怎么报名”，而是“我的时长算不算数、"
     "证书有没有人信”。这个认知转变直接决定了我们后来把“可信时长认证”做成核心卖点，而不是又一个功能堆砌的报名工具。"
     "让我印象最深的一次挫折是原型评审：第一版三端界面风格完全割裂，被老师当场点出“不像一个产品”。我拉着前端同学一起"
     "重新提炼品牌色和组件规范，把三端统一到一套设计语言下，返工了两天才理顺。这件事让我明白，产品的一致性不是锦上添花，"
     "而是团队协作的“共同语言”。作为组长，我还第一次真正体验了任务分解和进度管理——把一个大项目拆成 30 多个小任务、"
     "每人领 5~10 项、用甘特图盯进度，过程虽然琐碎，但确实让整个小组的节奏始终可控。")

h3("6.2  成员 B（后端开发）")
body("我负责后端接口和数据库，遇到的最大挫折是“重复签到导致时长被重复累加”。一开始我们只在前端做了按钮置灰，以为问题"
     "解决了，结果一次接口压测时，同一用户居然出现了两条签到、两条时长记录。我盯着日志查了很久才意识到，这是并发下"
     "“先查再插”的经典竞态——两个请求同时通过了“没签过”的判断，然后都执行了插入。这个问题教育我，防重不能只靠前端，"
     "必须落到数据库层。最终的方案是给签到表、时长表都加上联合唯一索引，让数据库兜底拒绝重复写入，业务层再查重一道做"
     "双保险。改完之后，我又专门写了重复请求的测试用例反复验证，才彻底放心。此外，为了让系统在没有 MySQL 的环境也能演示，"
     "我还做了 MySQL/SQLite 双引擎适配，期间被“SQL 占位符不一致（? 和 %s）”和“Decimal 类型不兼容”两个小坑卡了很久，"
     "查文档、看报错、一步步调通之后，对数据库访问层的抽象有了更深的理解。这些踩坑的经历，比一帆风顺让我学到的东西多得多。")

h3("6.3  成员 C（前端开发）")
body("我负责三端高保真原型。最开始我把学生端、发布者端、校方端各画一套，配色和按钮风格各不相同，自己看着还挺“丰富”，"
     "结果评审时被老师一句“不像一个产品”打回原形。这个反馈让我挺受打击，但也逼着我去重新思考设计规范这件事。后来我配合"
     "组长提炼了蓝紫品牌色、统一的卡片圆角和按钮态，把 26 个屏幕全部重做了一遍，才真正体会到“一致”带来的质感。"
     "另一个让我头疼的问题是中文乱码——原型页面一开始中文显示成乱码，我一度以为是自己写错了，后来查到是 HTML 头部少了"
     "charset 声明，加上 meta charset 后立刻正常。虽然是个小问题，但卡了我一个晚上，也让我记住了编码规范的重要性。"
     "现在回看，我从一开始连 HTML 结构都生疏，到后来能独立搭起三端 26 屏的可交互原型，成就感是实实在在的。最让我开心的，"
     "是有同学试用后说“界面挺清爽的”，那种被认可的瞬间，让我觉得反复改版的辛苦都值了。")

h3("6.4  成员 D（测试 / 文档）")
body("我负责测试和报告整理。说实话，以前我总觉得测试就是“随便点点，能用就行”，这次按用例表一条条跑下来，观念被彻底"
     "刷新了。比如我设计了一个“学生越权访问校方认定接口”的用例，结果真的测出了问题——系统一开始对角色校验不够严格，"
     "学生竟然能调用认定接口把自己的时长变成“已认定”。这个问题如果没被发现，等于给时长造假开了后门，想想都后怕。"
     "我立刻反馈给后端同学，加上角色校验后又回归测试确认修复。还有“未认定时长能否导出证书”这类边界情况，也是通过规范"
     "的用例才暴露出来的。这段经历让我认识到，测试不是开发的附属品，而是质量的最后一道防线。在整理报告的过程中，我也"
     "第一次系统地把项目的需求、设计、实现串起来看了一遍，才发现原来我们每一阶段的产出都是环环相扣的。能把四个人的工作"
     "梳理成一份完整、可追溯的报告，本身也让我很有成就感。")

# ================================================================
# 附录
# ================================================================
h1("附录  关键代码与运行说明")
body("本附录给出项目关键源码，并按【后端】【前端】【数据库】【配置与运行】分层标注。所有代码均可在项目目录 deliverables/"
     "下直接找到并运行。")

h2("附录 A  后端关键代码")

h3("A.1  全局配置（后端 · config.py）")
add_code([
    "BASE_DIR   = os.path.dirname(os.path.abspath(__file__))",
    "FRONTEND_DIR = os.path.normpath(os.path.join(BASE_DIR, '..', 'frontend'))",
    "DB_ENGINE  = os.environ.get('DB_ENGINE', 'mysql')   # mysql | sqlite",
    "DB_HOST    = os.environ.get('DB_HOST', '127.0.0.1')",
    "DB_PASSWORD= os.environ.get('DB_PASSWORD', '******')",
    "JWT_SECRET = os.environ.get('JWT_SECRET', 'qinghe-dev-secret')",
    "PORT       = int(os.environ.get('PORT', '8787'))",
], "【后端 · Python · config.py】",
   howrun="全部参数可用环境变量覆盖，便于在 MySQL 与 SQLite 之间零改动切换。")

h3("A.2  JWT 鉴权（后端 · auth.py）")
add_code([
    "def create_token(user_id, role):",
    "    now = datetime.datetime.now(datetime.timezone.utc)",
    "    payload = {'sub': str(user_id), 'role': role, 'iat': now,",
    "               'exp': now + datetime.timedelta(minutes=config.JWT_EXPIRE_MINUTES)}",
    "    return jwt.encode(payload, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)",
    "",
    "def token_required(fn):",
    "    @functools.wraps(fn)",
    "    def wrapper(*args, **kwargs):",
    "        auth = request.headers.get('Authorization', '')",
    "        if not auth.startswith('Bearer '):",
    "            return jsonify({'code': 40101, 'message': '缺少认证令牌'}), 401",
    "        payload = decode_token(auth[7:].strip())",
    "        request.user = {'id': int(payload['sub']), 'role': payload['role']}",
    "        return fn(*args, **kwargs)",
    "    return wrapper",
], "【后端 · Python · auth.py】",
   howrun="无状态鉴权：登录签发令牌，受保护接口用装饰器统一校验并把用户注入 request.user。")

h3("A.3  注册与登录（后端 · app.py）")
add_code([
    "@app.post('/api/v1/auth/register')",
    "def register():",
    "    role = _ROLE_MAP.get((body.get('role') or 'student').strip())",
    "    if not _PHONE_RE.fullmatch(phone):",
    "        return _fail(40004, '手机号格式不正确（需 11 位）')",
    "    if role == 'student' and not student_no:",
    "        return _fail(40007, '请填写学号')",
    "    if db.query_one('SELECT id FROM users WHERE phone = ?', (phone,)):",
    "        return _fail(40003, '该手机号已注册')",
    "    password_hash = generate_password_hash(password)",
    "    _, user_id = db.execute('INSERT INTO users (...) VALUES (...)', (...))",
    "    token = auth.create_token(user_id, role)",
    "    return _ok({'token': token, 'user': _user_payload(row)})",
    "",
    "@app.post('/api/v1/auth/login')",
    "def login():",
    "    row = db.query_one('SELECT ... FROM users WHERE phone=? OR student_no=? OR worker_no=?',",
    "                       (account, account, account))",
    "    if not row or not check_password_hash(row['password_hash'], password):",
    "        return _fail(40001, '账号或密码错误')",
    "    return _ok({'token': auth.create_token(row['id'], row['role']), ...})",
], "【后端 · Python · app.py】",
   howrun="密码使用 werkzeug 加盐哈希存储；登录支持手机号/学号/工号三种凭证。")

h3("A.4  签到签退与时长生成（后端 · app.py）")
add_code([
    "@app.post('/api/v1/activities/<activity_id>/checkins')",
    "@auth.token_required",
    "def checkin(activity_id):",
    "    s = db.query_one('SELECT id FROM signups WHERE activity_id=? AND user_id=?', ...)",
    "    if not s: return _fail(12001, '请先报名该活动')",
    "    try:",
    "        _, cid = db.execute('INSERT INTO checkins (...) VALUES (?,?,?,?)',",
    "                             (aid, uid, s['id'], 'checkin'))",
    "    except Exception:",
    "        return _fail(12002, '已签到，请勿重复签到')   # 唯一约束兜底",
    "    return _ok({'checkinId': cid, 'type': 'checkin'})",
    "",
    "def _ensure_hours(aid, uid, signup_id):",
    "    if db.query_one('SELECT id FROM volunteer_hours WHERE activity_id=? AND user_id=?', (aid, uid)):",
    "        return                                  # 幂等：已有则跳过",
    "    h = _activity_hours(aid)",
    "    db.execute('INSERT INTO volunteer_hours (...) VALUES (?,?,?,?,?)',",
    "               (aid, uid, signup_id, h, 'pending'))",
], "【后端 · Python · app.py】",
   howrun="签退调用 _ensure_hours 生成待认定时长；唯一索引 + 查重保证幂等，防止重复累加。")

h3("A.5  证书生成与核验（后端 · app.py）")
add_code([
    "def _make_cert_no():",
    "    return 'QH-' + time.strftime('%Y') + '-' + uuid.uuid4().hex[:8].upper()",
    "",
    "@app.post('/api/v1/certificates')",
    "@auth.token_required",
    "def create_certificate():",
    "    h = db.query_one('SELECT ... FROM volunteer_hours WHERE id=? AND user_id=?', (hours_id, uid))",
    "    if h['status'] != 'verified':",
    "        return _fail(13001, '该时长尚未认定，无法生成证书')",
    "    cert_no, qr_token = _make_cert_no(), uuid.uuid4().hex",
    "    db.execute('INSERT INTO certificates (...) VALUES (...)', (...))",
    "    return _ok({'certNo': cert_no, 'hours': cert_hours, 'type': ctype})",
    "",
    "@app.get('/api/v1/verify')",
    "def verify_certificate():",
    "    c = db.query_one('SELECT ... FROM certificates c JOIN users u ... WHERE c.cert_no=?', (cert_no,))",
    "    return _ok({'valid': True, 'holder': c['name'], 'hours': c['hours'], ...})",
], "【后端 · Python · app.py】",
   howrun="仅已认定（verified）的时长可生成证书；证书编号与二维码令牌均唯一，支持公开核验。")

h3("A.6  数据访问层（后端 · db.py）")
add_code([
    "def get_conn():",
    "    return _mysql_conn() if config.DB_ENGINE == 'mysql' else _sqlite_conn()",
    "",
    "def _translate(sql):",
    "    return sql.replace('?', '%s') if config.DB_ENGINE == 'mysql' else sql",
    "",
    "def query(sql, args=()):",
    "    conn = get_conn()",
    "    try:",
    "        cur = conn.cursor()",
    "        cur.execute(_translate(sql), args)",
    "        return _rows_to_dicts(cur.fetchall())",
    "    finally:",
    "        conn.close()",
], "【后端 · Python · db.py】",
   howrun="统一 CRUD 封装，屏蔽 MySQL/SQLite 差异（占位符与 Decimal 类型转换），上层业务无感知。")

h2("附录 B  前端关键代码")

h3("B.1  高保真原型（前端 · index.html）")
add_code([
    "<!DOCTYPE html><html lang='zh-CN'><head>",
    "<meta charset='UTF-8' />",
    "<title>青禾志愿 · 高保真原型（三端）</title>",
    "<style>:root{ --primary:#3B82F6; --purple:#8B5CF6; ... }</style>",
    "</head><body>",
    "<div class='app-shell'>          <!-- 桌面工作台 -->",
    "  <aside class='sidebar'>       <!-- 角色切换 + 26 屏导航 -->",
    "    <div class='role-switch'>学生端 / 发布者端 / 校方端</div>",
    "    <div class='screen-list'>报名 / 签到 / 时长 / 证书 ...</div>",
    "  </aside>",
    "  <main class='phone-frame'>    <!-- 手机屏：按角色与屏号渲染 -->",
    "    ...",
    "  </main>",
    "</div>",
    "</body></html>",
], "【前端 · HTML/CSS/JavaScript · index.html】",
   howrun="单文件高保真原型：左侧切换角色与屏幕，右侧以手机壳形式渲染对应界面，可完整演示业务闭环。直接用浏览器打开 "
          "deliverables/frontend/index.html 即可查看；或执行 node server.js 后访问 http://127.0.0.1:8787。")

h3("B.2  静态资源服务器（前端 · server.js）")
add_code([
    "const http = require('http'); const fs = require('fs'); const path = require('path');",
    "const PORT = process.env.PORT || 8787;",
    "http.createServer((req, res) => {",
    "  let p = decodeURIComponent(req.url.split('?')[0]);",
    "  if (p === '/') p = '/index.html';",
    "  const fp = path.join(root, p);",
    "  fs.readFile(fp, (err, data) => {",
    "    if (err) { res.writeHead(404); res.end('not found'); return; }",
    "    res.writeHead(200, {'Content-Type': types[path.extname(fp)]});",
    "    res.end(data);",
    "  });",
    "}).listen(PORT, '127.0.0.1', () => console.log('serving http://127.0.0.1:' + PORT));",
], "【前端 · Node.js · server.js】",
   howrun="仅用于纯前端原型预览；正式运行由后端 Flask 托管 frontend/ 目录，前端通过 /api/v1/* 调用接口。")

h2("附录 C  数据库关键代码")

h3("C.1  数据库建表（数据库 · schema.sql）")
add_code([
    "CREATE DATABASE IF NOT EXISTS qinghe_volunteer",
    "  DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;",
    "USE qinghe_volunteer;",
    "",
    "CREATE TABLE IF NOT EXISTS users (",
    "  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,",
    "  phone VARCHAR(20) NOT NULL,",
    "  password_hash VARCHAR(255) NOT NULL,",
    "  role ENUM('student','publisher_internal','publisher_external','admin') NOT NULL DEFAULT 'student',",
    "  student_no VARCHAR(32), worker_no VARCHAR(32), org VARCHAR(100),",
    "  status ENUM('active','disabled') NOT NULL DEFAULT 'active',",
    "  PRIMARY KEY(id), UNIQUE KEY uk_users_phone(phone),",
    "  UNIQUE KEY uk_users_student_no(student_no), UNIQUE KEY uk_users_worker_no(worker_no)",
    ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;",
    "",
    "CREATE TABLE IF NOT EXISTS volunteer_hours (",
    "  id BIGINT UNSIGNED AUTO_INCREMENT, activity_id BIGINT UNSIGNED NOT NULL,",
    "  user_id BIGINT UNSIGNED NOT NULL, hours DECIMAL(6,1) NOT NULL DEFAULT 0,",
    "  status VARCHAR(20) NOT NULL DEFAULT 'pending',",
    "  verified_by BIGINT, verified_at DATETIME,",
    "  UNIQUE KEY uk_hours_activity_user(activity_id,user_id)",
    ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;",
], "【数据库 · MySQL DDL · schema.sql】",
   howrun="共 7 张表；账号与角色分离，时长表以 (activity_id,user_id) 唯一键保证一人一活动一条时长。")

h2("附录 D  配置与运行说明")
body("下面给出系统的完整运行步骤，分为“一键启动”“依赖安装”“数据库初始化”“接口验证”四步。项目所有源码位于 "
     "deliverables/ 目录。")

h3("D.1  依赖安装")
add_code([
    "cd deliverables/backend",
    "python -m pip install -r requirements.txt",
    "# requirements.txt: flask>=3.0 / flask-cors>=4.0 / pyjwt>=2.8 / pymysql>=1.1",
], "【配置 · 命令行】",
   howrun="安装后端运行所需依赖；若需前端静态服务还需 Node.js 环境。")

h3("D.2  数据库初始化（二选一）")
add_code([
    "# 方式一：MySQL（推荐）——执行 start_mysql.bat 或手动：",
    "mysql -u root -p < schema.sql",
    "",
    "# 方式二：SQLite（零环境兜底）——设置环境变量后启动即可自动建表：",
    "set DB_ENGINE=sqlite",
], "【数据库 · 命令行】",
   howrun="MySQL 方式执行 schema.sql 创建 7 张表；SQLite 方式无需预建库，启动时自动初始化。")

h3("D.3  一键启动")
add_code([
    "cd deliverables/backend",
    "start_server.bat          # 等价于 python app.py，监听 8787 端口",
], "【配置 · 启动】",
   howrun="启动后后端自动托管 frontend/ 目录，浏览器访问 http://127.0.0.1:8787 即可打开系统。")

h3("D.4  接口验证")
add_code([
    "curl http://127.0.0.1:8787/api/v1/health",
    "curl -X POST http://127.0.0.1:8787/api/v1/auth/register \\",
    "     -H \"Content-Type: application/json\" \\",
    "     -d '{\"phone\":\"13800138000\",\"password\":\"123456\",\"role\":\"student\",\"student_no\":\"20240001\"}'",
    "curl -X POST http://127.0.0.1:8787/api/v1/auth/login \\",
    "     -H \"Content-Type: application/json\" -d '{\"account\":\"13800138000\",\"password\":\"123456\"}'",
], "【配置 · 命令行】",
   howrun="通过健康检查、注册、登录三个接口即可快速验证系统是否正常启动。")

# ================================================================
# 保存 + 后处理：把正文节页脚的“页码”占位符替换为 PAGE 域
# ================================================================
import zipfile, shutil, re

doc.save(OUT)
print("SAVED (pre-footer):", OUT)

# 后处理：将 footer3.xml（正文节）中的“页码”文字替换为 PAGE 域
# 由于 python-docx 对节页脚访问有限，直接操作 zip 包
tmp = OUT + ".tmp"
with zipfile.ZipFile(OUT, 'r') as z:
    names = z.namelist()
    footer_target = None
    for n in names:
        if re.match(r'word/footer\d+\.xml', n):
            s = z.read(n).decode('utf-8')
            if '页码' in s and 'PAGE' not in s:
                footer_target = n
                break
    if footer_target is None:
        # 若正文节实际引用的是含“页码”的 footer，逐一替换所有含“页码”的 footer
        footer_target = None
        for n in names:
            if re.match(r'word/footer\d+\.xml', n):
                if '页码' in z.read(n).decode('utf-8'):
                    footer_target = n
                    break

def _page_field_xml():
    rpr = ('<w:rPr><w:rFonts w:ascii="Cambria" w:hAnsi="Cambria"/>'
           '<w:sz w:val="22"/><w:szCs w:val="22"/></w:rPr>')
    return (
        '<w:r>' + rpr + '<w:fldChar w:fldCharType="begin"/></w:r>'
        '<w:r>' + rpr + '<w:instrText xml:space="preserve"> PAGE </w:instrText></w:r>'
        '<w:r>' + rpr + '<w:fldChar w:fldCharType="separate"/></w:r>'
        '<w:r>' + rpr + '<w:t>1</w:t></w:r>'
        '<w:r>' + rpr + '<w:fldChar w:fldCharType="end"/></w:r>'
    )

with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zin:
    with zipfile.ZipFile(OUT, 'r') as z:
        for n in names:
            data = z.read(n)
            if n == footer_target:
                s = data.decode('utf-8')
                # 替换含“页码”的整个 run
                s = re.sub(r'<w:r>[^<]*(?:<w:rPr>.*?</w:rPr>)?<w:t[^>]*>页码</w:t></w:r>', _page_field_xml(), s, count=1)
                data = s.encode('utf-8')
            zin.writestr(n, data)
shutil.move(tmp, OUT)
print("FOOTER PAGE FIELD DONE:", footer_target)
print("FINAL:", OUT)


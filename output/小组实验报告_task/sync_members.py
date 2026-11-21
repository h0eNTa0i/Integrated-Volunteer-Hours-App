# -*- coding: utf-8 -*-
"""根据用户修改的 3 人组，同步更新体会标题与分工表，使全文自洽。"""
from docx import Document

DOCX = "E:/AI-Agent/project/volunteer/小组实验报告.docx"
d = Document(DOCX)
paras = d.paragraphs


def set_para_text(p, text):
    """保留第一个 run 的格式，改写整段文本。"""
    runs = p.runs
    if runs:
        runs[0].text = text
        for r in runs[1:]:
            r._element.getparent().remove(r._element)
    else:
        p.add_run(text)


def set_cell_text(cell, text):
    """保留单元格第一个 run 的格式，改写单元格文本。"""
    p = cell.paragraphs[0]
    runs = p.runs
    if runs:
        runs[0].text = text
        for r in runs[1:]:
            r._element.getparent().remove(r._element)
    else:
        p.add_run(text)


# 1) 体会标题（3 人自洽版，与正文真实分工一致）
set_para_text(paras[343], "6.1  成员 A（组长 / 产品）")
set_para_text(paras[345], "6.2  成员 B（后端开发 / 测试）")
set_para_text(paras[347], "6.3  成员 C（前端开发 / 测试 / 文档）")

# 2) 分工表（表 1-2）角色与职责理顺
tbl = d.tables[1]
# 成员 A
set_cell_text(tbl.rows[1].cells[1], "组长 / 产品")
set_cell_text(tbl.rows[1].cells[2],
              "选题调研、NABCD 模型、需求分析与评审、原型统筹、进度管理与甘特图、报告统稿")
# 成员 B
set_cell_text(tbl.rows[2].cells[1], "后端开发 / 测试")
set_cell_text(tbl.rows[2].cells[2],
              "Flask 后端接口、JWT 鉴权、MySQL/SQLite 数据访问层、签到时长证书核心链路、"
              "数据库设计、测试计划与测试用例、功能与接口测试、缺陷跟踪")
# 成员 C
set_cell_text(tbl.rows[3].cells[1], "前端开发 / 测试 / 文档")
set_cell_text(tbl.rows[3].cells[2],
              "三端高保真原型、设计规范与组件库、前端页面联调、交互流程实现、"
              "用户反馈收集、文档整理与排版")

d.save(DOCX)
print("已同步修改：体会标题 x3、分工表 x6 单元格")

# -*- coding: utf-8 -*-
"""用 Word COM 打开 docx：更新目录与全部域，保存。"""
import os, sys, time
import win32com.client as wc

docx = os.path.abspath(sys.argv[1])

app = wc.DispatchEx("Word.Application")
app.Visible = False
app.DisplayAlerts = 0
try:
    d = app.Documents.Open(docx, ReadOnly=False, AddToRecentFiles=False)
    time.sleep(1)
    # 更新目录（TablesOfContents）
    for toc in d.TablesOfContents:
        toc.Update()
    # 更新其余域（页脚页码等）
    for s in d.StoryRanges:
        try:
            s.Fields.Update()
        except Exception:
            pass
    d.Fields.Update()
    d.Repaginate()
    d.Save()
    print("pages:", d.ComputeStatistics(2))
    d.Close(SaveChanges=True)
finally:
    app.Quit()

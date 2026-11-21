# -*- coding: utf-8 -*-
"""用 Word COM 打开 docx：更新全部域（含目录）、导出 PDF。"""
import os, sys, time
import win32com.client as wc

def main():
    docx = os.path.abspath(sys.argv[1])
    outdir = os.path.abspath(sys.argv[2])
    os.makedirs(outdir, exist_ok=True)
    pdf = os.path.join(outdir, "report.pdf")

    app = wc.DispatchEx("Word.Application")
    app.Visible = False
    app.DisplayAlerts = 0
    try:
        d = app.Documents.Open(docx, ReadOnly=False, AddToRecentFiles=False)
        time.sleep(1)
        # 更新正文全部域
        for s in d.StoryRanges:
            try:
                s.Fields.Update()
            except Exception:
                pass
        d.Fields.Update()
        d.Repaginate()
        d.Save()
        d.ExportAsFixedFormat(pdf, 17)  # wdExportFormatPDF
        pages = d.ComputeStatistics(2)
        print("PAGES:", pages)
        print("PDF:", pdf)
        d.Close(SaveChanges=True)
    finally:
        app.Quit()

if __name__ == "__main__":
    main()

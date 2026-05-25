import os


def export_loss_time_record(header, produksi, catatan, manpower, absen, inhouse_claim) -> str:
    """Export loss time record ke Excel sesuai format referensi MKM. Returns filepath."""
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        from openpyxl.utils import get_column_letter as gcl
    except ImportError:
        raise ImportError("openpyxl tidak terinstall. Jalankan: pip install openpyxl")

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Loss Time Record"

    # ── Border ────────────────────────────────────────────────────────────────
    _t  = Side(style="thin",   color="AAAAAA")
    _m  = Side(style="medium", color="000000")
    BD      = Border(left=_t, right=_t, top=_t, bottom=_t)
    BD_MED  = Border(left=_m, right=_m, top=_m, bottom=_m)

    # ── Fill ──────────────────────────────────────────────────────────────────
    F_WHITE = PatternFill("solid", fgColor="FFFFFF")
    F_TEAL  = PatternFill("solid", fgColor="00B0F0")   # column headers
    F_GROUP = PatternFill("solid", fgColor="1F7391")   # TIME / LOSS TIME group
    F_GRAY  = PatternFill("solid", fgColor="F2F2F2")   # even rows
    F_TOTAL = PatternFill("solid", fgColor="D9D9D9")   # total row
    F_SHOP  = PatternFill("solid", fgColor="D9E1F2")   # shop label

    # ── Font ──────────────────────────────────────────────────────────────────
    FN_LOGO  = Font(name="Arial", size=18, bold=True, color="CC0000")
    FN_TITLE = Font(name="Arial", size=13, bold=True, color="000000")
    FN_COMP  = Font(name="Arial", size=8,  color="595959")
    FN_SHOP  = Font(name="Arial", size=10, bold=True, color="000000")
    FN_SIGN_L = Font(name="Arial", size=9, bold=True, color="000000")
    FN_SIGN_V = Font(name="Arial", size=9,            color="000000")
    FN_GRP   = Font(name="Arial", size=9,  bold=True, color="FFFFFF")
    FN_HDR   = Font(name="Arial", size=9,  bold=True, color="FFFFFF")
    FN_DATA  = Font(name="Arial", size=9,             color="000000")
    FN_TOT   = Font(name="Arial", size=9,  bold=True, color="000000")

    # ── Alignment ─────────────────────────────────────────────────────────────
    ALC  = Alignment(horizontal="center", vertical="center")
    ALL  = Alignment(horizontal="left",   vertical="center", wrap_text=True)
    ALCW = Alignment(horizontal="center", vertical="center", wrap_text=True)

    # ── Column constants ──────────────────────────────────────────────────────
    # A=spacer | B=NO | C=DATE | D=SHIFT | E=Category
    # F-K=COUNTER MEASURE (6 cols) | L-M=Remarks (2 cols)
    # N=Start | O=Finish | P=HOUR
    # Q=M/C | R=LINE STOP(HOUR) | S=M/C STOP(HOUR) | T=MAN | U=MAN HOUR
    NCOLS   = 21
    C_SPC   =  1
    C_NO    =  2
    C_DT    =  3
    C_SH    =  4
    C_CAT   =  5
    C_CMS   =  6   # COUNTER MEASURE start
    C_CME   = 11   # COUNTER MEASURE end
    C_RMS   = 12   # Remarks start
    C_RME   = 13   # Remarks end
    C_ST    = 14   # Start
    C_FN    = 15   # Finish
    C_HR    = 16   # HOUR
    C_MC    = 17   # M/C
    C_LS    = 18   # LINE STOP
    C_MS    = 19   # M/C STOP
    C_MAN   = 20   # MAN
    C_MH    = 21   # MAN HOUR

    DATA_ROW = 9   # first data row

    # ── Column widths ─────────────────────────────────────────────────────────
    col_w = {
        C_SPC: 1.5, C_NO: 5,   C_DT: 11,  C_SH: 9,   C_CAT: 13,
        C_CMS: 14,  7: 14, 8: 14, 9: 14, 10: 14, C_CME: 14,
        C_RMS: 11,  C_RME: 11,
        C_ST: 7,   C_FN: 7,   C_HR: 7,
        C_MC: 7,   C_LS: 10,  C_MS: 10,  C_MAN: 7, C_MH: 8,
    }
    for ci, w in col_w.items():
        ws.column_dimensions[gcl(ci)].width = w

    # ── Helpers ───────────────────────────────────────────────────────────────
    def mrg(r1, c1, r2, c2):
        if r1 == r2 and c1 == c2:
            return
        ws.merge_cells(start_row=r1, start_column=c1, end_row=r2, end_column=c2)

    def wc(r, col, val="", fn=None, fl=None, al=None, bd=None):
        cl = ws.cell(row=r, column=col, value=val)
        if fn: cl.font      = fn
        if fl: cl.fill      = fl
        if al: cl.alignment = al
        if bd: cl.border    = bd
        return cl

    def fill_range(r, c1, c2, fl=F_WHITE, fn=FN_DATA, bd=BD):
        for c in range(c1, c2 + 1):
            cl = ws.cell(r, c)
            if fl: cl.fill   = fl
            if fn: cl.font   = fn
            if bd: cl.border = bd

    # ── Row heights ───────────────────────────────────────────────────────────
    for r, h in {1: 16, 2: 30, 3: 14, 4: 22, 5: 8, 6: 8, 7: 18, 8: 32}.items():
        ws.row_dimensions[r].height = h

    # =========================================================================
    # HEADER AREA  (rows 1–6)
    # =========================================================================

    # Row 1 — "Approve / Checked / Prepared" labels
    mrg(1, C_MC, 1, C_LS)
    wc(1, C_MC,  "Approve",  FN_SIGN_L, F_WHITE, ALC, BD)
    wc(1, C_MS,  "Checked",  FN_SIGN_L, F_WHITE, ALC, BD)
    mrg(1, C_MAN, 1, C_MH)
    wc(1, C_MAN, "Prepared", FN_SIGN_L, F_WHITE, ALC, BD)

    # Row 2 — Logo | Title | Names
    mrg(2, C_SPC, 2, C_SH)
    wc(2, C_SPC, "MKM", FN_LOGO, F_WHITE, ALC)

    mrg(2, C_CAT, 2, C_RME)
    wc(2, C_CAT,
       f"LOSS TIME RECORD   {header.get('section', '').upper()}",
       FN_TITLE, F_WHITE, ALL)

    mrg(2, C_MC, 2, C_LS)
    wc(2, C_MC,  header.get("approved_by", "—"), FN_SIGN_V, F_WHITE, ALC, BD)
    wc(2, C_MS,  header.get("checked_by",  "—"), FN_SIGN_V, F_WHITE, ALC, BD)
    mrg(2, C_MAN, 2, C_MH)
    wc(2, C_MAN, header.get("coordinator", "—"), FN_SIGN_V, F_WHITE, ALC, BD)

    # Row 3 — Company name
    mrg(3, C_SPC, 3, C_RME)
    wc(3, C_SPC, "PT. MITSUBISHI KRAMAYUDHA MOTORS & MFG", FN_COMP, F_WHITE, ALC)

    # Row 4 — SHOP + date/shift info
    mrg(4, C_DT, 4, C_FN)
    wc(4, C_DT,
       f"SHOP  :  {header.get('section', '')}",
       FN_SHOP, F_SHOP, ALC, BD_MED)

    mrg(4, C_HR, 4, C_MH)
    wc(4, C_HR,
       f"Tanggal : {header.get('date','')}     Shift : {header.get('shift','')}",
       FN_DATA, F_WHITE, ALC)

    # =========================================================================
    # TABLE HEADERS  (rows 7–8)
    # =========================================================================

    # Row 7 — Group headers: TIME  and  LOSS TIME
    fill_range(7, C_NO, NCOLS, fl=F_TEAL, fn=FN_HDR, bd=BD)

    mrg(7, C_ST, 7, C_HR)
    wc(7, C_ST,  "TIME",      FN_GRP, F_GROUP, ALC, BD)

    mrg(7, C_MC, 7, C_MH)
    wc(7, C_MC, "LOSS TIME",  FN_GRP, F_GROUP, ALC, BD)

    # Row 8 — Column labels
    fill_range(8, C_NO, NCOLS, fl=F_TEAL, fn=FN_HDR, bd=BD)
    mrg(8, C_CMS, 8, C_CME)
    mrg(8, C_RMS, 8, C_RME)

    lbl = {
        C_NO:  "NO.",
        C_DT:  "DATE",
        C_SH:  "SHIFT",
        C_CAT: "Category",
        C_CMS: "COUNTER MEASURE",
        C_RMS: "Remarks",
        C_ST:  "Start",
        C_FN:  "Finish",
        C_HR:  "HOUR",
        C_MC:  "M/C",
        C_LS:  "LINE STOP\n(HOUR)",
        C_MS:  "M/C STOP\n(HOUR)",
        C_MAN: "MAN",
        C_MH:  "MAN\nHOUR",
    }
    for ci, text in lbl.items():
        wc(8, ci, text, FN_HDR, F_TEAL, ALCW, BD)

    # =========================================================================
    # DATA ROWS
    # =========================================================================

    for i, item in enumerate(catatan, 1):
        r = DATA_ROW + i - 1
        ws.row_dimensions[r].height = 20

        fl = F_WHITE if i % 2 == 1 else F_GRAY
        fill_range(r, C_NO, NCOLS, fl=fl, fn=FN_DATA, bd=BD)

        mrg(r, C_CMS, r, C_CME)
        mrg(r, C_RMS, r, C_RME)

        # COUNTER MEASURE = description + counter action
        desc = item.get("description", "") or ""
        ca   = item.get("corrective_action", "") or ""
        cm_text = desc + ("\n→ " + ca if desc and ca else ca if ca else "")

        wc(r, C_NO,  i,                          al=ALC)
        wc(r, C_DT,  header.get("date",  ""),    al=ALC)
        wc(r, C_SH,  header.get("shift", ""),    al=ALC)
        wc(r, C_CAT, item.get("category", ""),   al=ALC)
        wc(r, C_CMS, cm_text,                    al=ALL)
        wc(r, C_RMS, item.get("cause", "") or "", al=ALL)
        wc(r, C_ST,  item.get("start_time", ""), al=ALC)
        wc(r, C_FN,  item.get("end_time",   ""), al=ALC)

        down = float(item.get("down_time",  0) or 0)
        loss = float(item.get("loss_time",  0) or 0)

        num_vals = [
            (C_HR,  down),
            (C_MC,  0.0),
            (C_LS,  loss),
            (C_MS,  0.0),
            (C_MAN, 0.0),
            (C_MH,  0.0),
        ]
        for ci, val in num_vals:
            cl = wc(r, ci, val, al=ALC)
            cl.number_format = "0.00"

    # =========================================================================
    # TOTAL ROW
    # =========================================================================

    if catatan:
        r_tot = DATA_ROW + len(catatan)
        ws.row_dimensions[r_tot].height = 20

        fill_range(r_tot, C_NO, NCOLS, fl=F_TOTAL, fn=FN_TOT, bd=BD)
        mrg(r_tot, C_NO, r_tot, C_RME)
        wc(r_tot, C_NO, "TOTAL", FN_TOT, F_TOTAL, ALC, BD)

        t_down = sum(float(x.get("down_time") or 0) for x in catatan)
        t_loss = sum(float(x.get("loss_time") or 0) for x in catatan)

        tot_vals = [
            (C_HR, t_down), (C_MC, 0.0), (C_LS, t_loss),
            (C_MS, 0.0), (C_MAN, 0.0), (C_MH, 0.0),
        ]
        for ci, val in tot_vals:
            cl = wc(r_tot, ci, val, FN_TOT, F_TOTAL, ALC, BD)
            cl.number_format = "0.00"

    # Freeze header rows
    ws.freeze_panes = ws.cell(DATA_ROW, C_NO)

    # =========================================================================
    # SAVE
    # =========================================================================
    downloads   = os.path.join(os.path.expanduser("~"), "Downloads")
    date_str    = str(header.get("date", "")).replace("-", "")
    section_str = str(header.get("section", "unknown")).replace(" ", "_")
    filename    = f"LTR_{section_str}_{date_str}.xlsx"
    filepath    = os.path.join(downloads, filename)
    wb.save(filepath)
    return filepath

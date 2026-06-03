        # Header info
        hdr_frame = QFrame()
        hdr_frame.setStyleSheet("QFrame { background-color: #2e2e2e; border-radius: 0px; }")
        hdr_lyt = QGridLayout(hdr_frame)
        hdr_lyt.setContentsMargins(14, 10, 14, 10)
        hdr_lyt.setSpacing(6)
        hdr_lyt.setColumnStretch(1, 1)
        hdr_lyt.setColumnStretch(3, 1)

        fmt_w = lambda v: f"{v:.2f} H" if v is not None else "—"
        fmt_d = lambda v: f"{v:.0f} H" if v is not None else "—"
        plan_wh   = sum(p.get("plan_whour", 0) or 0   for p in produksi) if produksi else None
        actual_wh = sum(p.get("actual_whour", 0) or 0 for p in produksi) if produksi else None
        shift_dur = header.get("shift_duration", 0.0)
        overtime  = header.get("overtime", "-")
        
        pairs = [
            ("Tanggal",       header.get("date", "")),
            ("Shift",         header.get("shift", "")),
            ("Shop",          header.get("section", "")),
            ("Koordinator",   header.get("coordinator", "")),
            ("Disetujui",     header.get("approved_by", "")),
            ("Diperiksa",     header.get("checked_by", "")),
            ("Plan W/Hour",   fmt_w(plan_wh)),
            ("Actual W/Hour", fmt_w(actual_wh)),
            ("Duration",      fmt_d(shift_dur)),
            ("Overtime",      overtime),
        ]
        for idx, (lbl_text, val_text) in enumerate(pairs):
            r, c = divmod(idx, 2)
            lbl = QLabel(lbl_text + ":")
            lbl.setStyleSheet("color: #969696; font-size: 11px;")
            val = QLabel(str(val_text))
            val.setStyleSheet("color: #ffffff; font-size: 11px; font-weight: bold;")
            hdr_lyt.addWidget(lbl, r, c * 2)
            hdr_lyt.addWidget(val, r, c * 2 + 1)
        lyt.addWidget(hdr_frame)

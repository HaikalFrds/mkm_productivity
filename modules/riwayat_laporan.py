import os

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QComboBox, QPushButton, QDateEdit,
    QScrollArea, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QDialog, QDialogButtonBox, QAbstractItemView,
    QTabWidget, QLineEdit,
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor

from modules.db_auth import get_connection
from modules.db_laporan import (
    get_all_sections, get_riwayat_laporan,
    get_detail_laporan, hapus_laporan,
)


# ── Shared styles ─────────────────────────────────────────────────────────────

_DATE_STYLE = """
    QDateEdit {
        background-color: rgb(33, 37, 43);
        border: 1px solid rgb(60, 65, 75);
        border-radius: 5px; padding-left: 8px;
        color: rgb(220, 220, 220); font-size: 11px;
    }
    QDateEdit:focus { border: 1px solid rgb(150, 150, 150); }
    QDateEdit::drop-down {
        border: none; width: 22px;
        subcontrol-origin: padding; subcontrol-position: top right;
    }
"""

_COMBO_STYLE = """
    QComboBox {
        background-color: rgb(33, 37, 43);
        border: 1px solid rgb(60, 65, 75);
        border-radius: 5px; padding-left: 8px;
        color: rgb(220, 220, 220); font-size: 11px;
    }
    QComboBox:focus { border: 1px solid rgb(150, 150, 150); }
    QComboBox::drop-down { border: none; width: 24px; }
    QComboBox QAbstractItemView {
        background-color: rgb(33, 37, 43); color: rgb(220, 220, 220);
        selection-background-color: rgb(60, 65, 75);
        border: 1px solid rgb(60, 65, 75);
    }
"""

_TABLE_STYLE = """
    QTableWidget {
        background-color: rgb(33, 37, 43);
        border: 1px solid rgb(60, 65, 75); border-radius: 5px;
        gridline-color: rgb(55, 60, 70);
    }
    QTableWidget::item {
        color: rgb(230, 230, 230); padding: 4px 8px;
        background-color: rgb(38, 42, 50);
        border-bottom: 1px solid rgb(55, 60, 70);
    }
    QTableWidget::item:selected { background-color: rgb(100, 110, 125); color: white; }
    QHeaderView::section {
        background-color: rgb(28, 32, 40); color: rgb(150, 150, 150);
        border: none; border-bottom: 1px solid rgb(60, 65, 75);
        border-right: 1px solid rgb(60, 65, 75);
        padding: 6px; font-weight: bold; font-size: 10px;
    }
"""

_TAB_STYLE = """
    QTabWidget::pane { background-color: transparent; border: none; }
    QTabBar::tab {
        background-color: rgb(40, 44, 52); color: rgb(150, 150, 150);
        padding: 8px 22px; margin-right: 3px;
        border-top-left-radius: 6px; border-top-right-radius: 6px;
        font-size: 11px; font-weight: bold;
    }
    QTabBar::tab:selected {
        background-color: rgb(55, 60, 70); color: #ffffff;
        border-bottom: 2px solid rgb(180, 30, 30);
    }
    QTabBar::tab:hover:!selected {
        background-color: rgb(50, 55, 65); color: rgb(200, 200, 200);
    }
"""

_INPUT_STYLE = """
    QLineEdit {
        background-color: rgb(33, 37, 43);
        border: 1px solid rgb(60, 65, 75); border-radius: 5px;
        padding-left: 8px; color: rgb(220, 220, 220); font-size: 11px;
    }
    QLineEdit:focus { border: 1px solid rgb(150, 150, 150); }
"""

_CARD_STYLE = "QFrame { background-color: rgb(40, 44, 52); border-radius: 10px; }"

_BTN_CARI = """
    QPushButton {
        background-color: rgb(100, 60, 160); color: rgb(220, 200, 255);
        border: none; border-radius: 5px; font-size: 11px; padding: 0 12px;
    }
    QPushButton:hover { background-color: rgb(120, 75, 185); }
"""

_BTN_RESET = """
    QPushButton {
        background-color: rgb(60, 65, 75); color: rgb(200, 200, 200);
        border: none; border-radius: 5px; font-size: 11px; padding: 0 12px;
    }
    QPushButton:hover { background-color: rgb(75, 80, 90); }
"""

_BTN_EXPORT = """
    QPushButton {
        background-color: rgb(25, 90, 50); color: rgb(130, 220, 140);
        border: none; border-radius: 5px; font-size: 11px; padding: 0 12px;
    }
    QPushButton:hover { background-color: rgb(35, 110, 65); }
"""


# ── DB helpers ────────────────────────────────────────────────────────────────

def _db_rekap_bulanan(section_id, bulan, tahun):
    conn = get_connection()
    try:
        cur = conn.cursor()
        sec = " AND dr.section_id = %s" if section_id is not None else ""
        p1 = [bulan, tahun] + ([section_id] if section_id else [])
        cur.execute(f"""
            SELECT COALESCE(pc.name, 'Lainnya') AS kategori,
                   COALESCE(SUM(pr.loss_time), 0) AS total_loss
            FROM problem_record pr
            LEFT JOIN problem_category pc ON pc.id = pr.category_id
            JOIN daily_report dr ON dr.id = pr.report_id
            WHERE EXTRACT(MONTH FROM dr.date) = %s
              AND EXTRACT(YEAR  FROM dr.date) = %s {sec}
            GROUP BY COALESCE(pc.name, 'Lainnya')
            ORDER BY total_loss DESC
        """, p1)
        rows = [(r[0], float(r[1])) for r in cur.fetchall()]

        p2 = [bulan, tahun] + ([section_id] if section_id else [])
        cur.execute(f"""
            SELECT COALESCE(SUM(dp.actual_whour), 0)
            FROM daily_production dp
            JOIN daily_report dr ON dr.id = dp.report_id
            WHERE EXTRACT(MONTH FROM dr.date) = %s
              AND EXTRACT(YEAR  FROM dr.date) = %s {sec}
        """, p2)
        row = cur.fetchone()
        total_hour = float(row[0]) if row and row[0] else 0.0
        cur.close()
        return rows, total_hour
    except Exception:
        raise
    finally:
        conn.close()


def _db_ng_pending(section_id, date_from, date_to):
    conn = get_connection()
    try:
        cur = conn.cursor()
        sec = " AND dr.section_id = %s" if section_id is not None else ""

        inhouse_ng = []
        try:
            p = [date_from, date_to] + ([section_id] if section_id else [])
            cur.execute(f"""
                SELECT ic.tanggal, ic.model, ic.op_no_st, ic.item, ic.qty,
                       ic.penyebab, ic.tindakan, ic.faktor, ic.stop_hr, ic.lost_hr, ic.status
                FROM inhouse_claim ic
                JOIN daily_report dr ON dr.id = ic.report_id
                WHERE dr.date BETWEEN %s AND %s AND ic.status = 'NG' {sec}
                ORDER BY ic.tanggal DESC, ic.id DESC
            """, p)
            inhouse_ng = cur.fetchall()
        except Exception:
            conn.rollback()

        inhouse_pending = []
        try:
            p = [date_from, date_to] + ([section_id] if section_id else [])
            cur.execute(f"""
                SELECT ic.tanggal, ic.model, ic.op_no_st, ic.item, ic.qty,
                       ic.penyebab, ic.tindakan, ic.faktor, ic.stop_hr, ic.lost_hr
                FROM inhouse_claim ic
                JOIN daily_report dr ON dr.id = ic.report_id
                WHERE dr.date BETWEEN %s AND %s AND ic.status = 'PENDING' {sec}
                ORDER BY ic.tanggal DESC, ic.id DESC
            """, p)
            inhouse_pending = cur.fetchall()
        except Exception:
            conn.rollback()

        cur.close()
        return inhouse_ng, inhouse_pending
    finally:
        conn.close()


# ── Widget ────────────────────────────────────────────────────────────────────

class RiwayatLaporanWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._sections_loaded = False
        self._tab2_loaded = False
        self._tab3_loaded = False
        self._setup_ui()

    def showEvent(self, event):
        super().showEvent(event)
        self._load_sections_once()
        self.load_data_harian()

    def _load_sections_once(self):
        if self._sections_loaded:
            return
        try:
            sections = get_all_sections()
            for combo in (self.combo_section, self.combo_section_rekap, self.combo_section_ng):
                combo.blockSignals(True)
                for sid, sname in sections:
                    combo.addItem(sname, sid)
                combo.blockSignals(False)
            self._sections_loaded = True
        except Exception:
            pass

    def _on_tab_changed(self, idx):
        if idx == 1 and not self._tab2_loaded:
            self.load_rekap_bulanan()
            self._tab2_loaded = True
        elif idx == 2 and not self._tab3_loaded:
            self.load_ng_pending()
            self._tab3_loaded = True

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(_TAB_STYLE)
        self.tabs.currentChanged.connect(self._on_tab_changed)
        self.tabs.addTab(self._build_tab_harian(), "Riwayat Harian")
        self.tabs.addTab(self._build_tab_rekap(), "Rekap Bulanan")
        self.tabs.addTab(self._build_tab_ng_pending(), "NG & Pending")
        outer.addWidget(self.tabs)

    # ── Tab 1: Riwayat Harian ────────────────────────────────────────────────

    def _build_tab_harian(self):
        tab = QWidget()
        tab.setStyleSheet("background: transparent;")
        outer = QVBoxLayout(tab)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        main = QVBoxLayout(container)
        main.setContentsMargins(15, 15, 15, 15)
        main.setSpacing(12)

        # Filter card
        card_f = QFrame()
        card_f.setStyleSheet(_CARD_STYLE)
        fl = QHBoxLayout(card_f)
        fl.setContentsMargins(16, 12, 16, 12)
        fl.setSpacing(10)

        fl.addWidget(self._flabel("Section"))
        self.combo_section = QComboBox()
        self.combo_section.setMinimumHeight(30)
        self.combo_section.setMinimumWidth(155)
        self.combo_section.setStyleSheet(_COMBO_STYLE)
        self.combo_section.addItem("Semua", None)
        fl.addWidget(self.combo_section)

        fl.addWidget(self._flabel("Shift"))
        self.combo_shift = QComboBox()
        self.combo_shift.setMinimumHeight(30)
        self.combo_shift.setMinimumWidth(110)
        self.combo_shift.setStyleSheet(_COMBO_STYLE)
        self.combo_shift.addItems(["Semua", "Day Shift", "Night Shift"])
        fl.addWidget(self.combo_shift)

        fl.addWidget(self._flabel("Dari"))
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setMinimumHeight(30)
        self.date_from.setStyleSheet(_DATE_STYLE)
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        fl.addWidget(self.date_from)

        fl.addWidget(self._flabel("Sampai"))
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setMinimumHeight(30)
        self.date_to.setStyleSheet(_DATE_STYLE)
        self.date_to.setDate(QDate.currentDate())
        fl.addWidget(self.date_to)

        fl.addStretch()

        btn_cari = QPushButton("Cari")
        btn_cari.setMinimumSize(76, 32)
        btn_cari.setStyleSheet(_BTN_CARI)
        btn_cari.clicked.connect(self.load_data_harian)
        fl.addWidget(btn_cari)

        btn_reset_f = QPushButton("Reset Filter")
        btn_reset_f.setMinimumSize(90, 32)
        btn_reset_f.setStyleSheet(_BTN_RESET)
        btn_reset_f.clicked.connect(self._reset_filter_harian)
        fl.addWidget(btn_reset_f)

        main.addWidget(card_f)

        # Table card
        card_t = QFrame()
        card_t.setStyleSheet(_CARD_STYLE)
        tl = QVBoxLayout(card_t)
        tl.setContentsMargins(16, 16, 16, 16)
        tl.setSpacing(8)

        hdr_row = QHBoxLayout()
        self.lbl_info_h = QLabel("Memuat data...")
        self.lbl_info_h.setStyleSheet("color: rgb(130, 140, 165); font-size: 10px;")
        hdr_row.addWidget(self.lbl_info_h)
        hdr_row.addStretch()
        btn_export_rah = QPushButton("Export RAH")
        btn_export_rah.setMinimumSize(100, 30)
        btn_export_rah.setStyleSheet(_BTN_EXPORT)
        btn_export_rah.clicked.connect(self._export_rah)
        hdr_row.addWidget(btn_export_rah)
        tl.addLayout(hdr_row)

        self.tabel_harian = QTableWidget()
        self.tabel_harian.setColumnCount(7)
        self.tabel_harian.setHorizontalHeaderLabels([
            "No", "Tanggal", "Section", "Shift", "Koordinator", "Jml Masalah", "Aksi",
        ])
        self.tabel_harian.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.tabel_harian.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.tabel_harian.horizontalHeader().setStretchLastSection(False)
        self.tabel_harian.verticalHeader().setVisible(False)
        self.tabel_harian.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabel_harian.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabel_harian.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tabel_harian.setStyleSheet(_TABLE_STYLE)
        self.tabel_harian.setColumnWidth(0, 40)
        self.tabel_harian.setColumnWidth(1, 92)
        self.tabel_harian.setColumnWidth(3, 92)
        self.tabel_harian.setColumnWidth(4, 135)
        self.tabel_harian.setColumnWidth(5, 90)
        self.tabel_harian.setColumnWidth(6, 180)
        tl.addWidget(self.tabel_harian)

        main.addWidget(card_t)
        main.addStretch()
        scroll.setWidget(container)
        outer.addWidget(scroll)
        return tab

    def load_data_harian(self):
        section_id = self.combo_section.currentData()
        shift_text = self.combo_shift.currentText()
        shift_name = None if shift_text == "Semua" else shift_text
        date_from = self.date_from.date().toString("yyyy-MM-dd")
        date_to = self.date_to.date().toString("yyyy-MM-dd")

        try:
            rows = get_riwayat_laporan(
                section_id=section_id,
                shift_name=shift_name,
                date_from=date_from,
                date_to=date_to,
            )
        except Exception as e:
            self.lbl_info_h.setText(f"Gagal memuat data: {e}")
            self.tabel_harian.setRowCount(0)
            return

        self.tabel_harian.setRowCount(0)
        self.lbl_info_h.setText(f"{len(rows)} data ditemukan")

        def _item(text, align=Qt.AlignCenter):
            it = QTableWidgetItem(str(text) if text is not None else "")
            it.setTextAlignment(align)
            return it

        for i, row in enumerate(rows):
            self.tabel_harian.insertRow(i)
            self.tabel_harian.setItem(i, 0, _item(i + 1))
            self.tabel_harian.setItem(i, 1, _item(row["date"]))
            self.tabel_harian.setItem(i, 2, _item(row["section"], Qt.AlignLeft | Qt.AlignVCenter))
            self.tabel_harian.setItem(i, 3, _item(row["shift"]))
            self.tabel_harian.setItem(i, 4, _item(row["coordinator"], Qt.AlignLeft | Qt.AlignVCenter))
            self.tabel_harian.setItem(i, 5, _item(str(row["jml_masalah"])))

            report_id = row["id"]
            aksi_w = QWidget()
            aksi_w.setStyleSheet("background-color: rgb(38, 42, 50);")
            al = QHBoxLayout(aksi_w)
            al.setContentsMargins(4, 3, 4, 3)
            al.setSpacing(4)

            btn_lihat = QPushButton("Lihat")
            btn_lihat.setFixedSize(52, 26)
            btn_lihat.setStyleSheet("""
                QPushButton { background-color: rgb(30, 75, 145); color: rgb(130, 185, 255);
                    border: none; border-radius: 4px; font-size: 10px; }
                QPushButton:hover { background-color: rgb(45, 95, 170); }
            """)
            btn_lihat.clicked.connect(lambda _, rid=report_id: self._lihat(rid))

            btn_edit = QPushButton("Edit")
            btn_edit.setFixedSize(44, 26)
            btn_edit.setStyleSheet("""
                QPushButton { background-color: rgb(75, 60, 20); color: rgb(220, 195, 90);
                    border: none; border-radius: 4px; font-size: 10px; }
                QPushButton:hover { background-color: rgb(95, 80, 30); }
            """)
            btn_edit.clicked.connect(lambda _, rid=report_id: self._edit(rid))

            btn_hapus = QPushButton("Hapus")
            btn_hapus.setFixedSize(52, 26)
            btn_hapus.setStyleSheet("""
                QPushButton { background-color: rgb(100, 30, 30); color: rgb(220, 120, 120);
                    border: none; border-radius: 4px; font-size: 10px; }
                QPushButton:hover { background-color: rgb(130, 40, 40); }
            """)
            btn_hapus.clicked.connect(lambda _, rid=report_id: self._hapus(rid))

            al.addWidget(btn_lihat)
            al.addWidget(btn_edit)
            al.addWidget(btn_hapus)
            al.addStretch()
            self.tabel_harian.setCellWidget(i, 6, aksi_w)
            self.tabel_harian.setRowHeight(i, 36)

    def _reset_filter_harian(self):
        self.combo_section.setCurrentIndex(0)
        self.combo_shift.setCurrentIndex(0)
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        self.date_to.setDate(QDate.currentDate())
        self.load_data_harian()

    def _lihat(self, report_id):
        try:
            header, produksi, catatan, manpower, absen, inhouse_claim = get_detail_laporan(report_id)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Gagal memuat detail: {e}")
            return
        if header is None:
            QMessageBox.warning(self, "Tidak Ditemukan", f"Laporan #{report_id} tidak ditemukan.")
            return

        dlg = QDialog(self)
        dlg.setWindowTitle(f"Detail Laporan — #{report_id}")
        dlg.setMinimumWidth(980)
        dlg.setMinimumHeight(700)
        dlg.setStyleSheet("QDialog { background-color: rgb(33, 37, 43); color: rgb(220,220,220); }")

        outer_lyt = QVBoxLayout(dlg)
        outer_lyt.setContentsMargins(16, 16, 16, 16)
        outer_lyt.setSpacing(10)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        lyt = QVBoxLayout(container)
        lyt.setContentsMargins(0, 0, 0, 0)
        lyt.setSpacing(10)

        def _cell(val, align=Qt.AlignLeft | Qt.AlignVCenter):
            it = QTableWidgetItem(str(val) if val else "")
            it.setTextAlignment(align)
            return it

        def _sec_lbl(text):
            lbl = QLabel(text)
            lbl.setStyleSheet(
                "color: rgb(189, 147, 249); font-size: 12px; font-weight: bold; padding: 4px 0;"
            )
            return lbl

        # ── Header info ──────────────────────────────────────────────────────
        hdr_frame = QFrame()
        hdr_frame.setStyleSheet("QFrame { background-color: rgb(40, 44, 52); border-radius: 8px; }")
        hdr_lyt = QGridLayout(hdr_frame)
        hdr_lyt.setContentsMargins(14, 10, 14, 10)
        hdr_lyt.setSpacing(6)
        hdr_lyt.setColumnStretch(1, 1)
        hdr_lyt.setColumnStretch(3, 1)

        fmt_w = lambda v: f"{v:.2f} H" if v is not None else "—"
        plan_wh   = produksi[0].get("plan_whour")   if produksi else None
        actual_wh = produksi[0].get("actual_whour") if produksi else None
        pairs = [
            ("Tanggal",       header.get("date", "")),
            ("Shift",         header.get("shift", "")),
            ("Section",       header.get("section", "")),
            ("Koordinator",   header.get("coordinator", "")),
            ("Disetujui",     header.get("approved_by", "")),
            ("Diperiksa",     header.get("checked_by", "")),
            ("Plan W/Hour",   fmt_w(plan_wh)),
            ("Actual W/Hour", fmt_w(actual_wh)),
            ("Status",        header.get("status", "")),
        ]
        for idx, (lbl_text, val_text) in enumerate(pairs):
            r, c = divmod(idx, 2)
            lbl = QLabel(lbl_text + ":")
            lbl.setStyleSheet("color: rgb(140, 150, 165); font-size: 11px;")
            val = QLabel(str(val_text))
            val.setStyleSheet("color: rgb(210, 215, 225); font-size: 11px; font-weight: bold;")
            hdr_lyt.addWidget(lbl, r, c * 2)
            hdr_lyt.addWidget(val, r, c * 2 + 1)
        lyt.addWidget(hdr_frame)

        # ── Data Produksi ────────────────────────────────────────────────────
        if produksi:
            lyt.addWidget(_sec_lbl("Data Produksi"))
            tbl_prod = QTableWidget()
            tbl_prod.setColumnCount(7)
            tbl_prod.setHorizontalHeaderLabels(
                ["Model", "Plan", "Reg", "2H OT", "3H OT", "11H OT", "Balance"]
            )
            tbl_prod.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            tbl_prod.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
            tbl_prod.verticalHeader().setVisible(False)
            tbl_prod.setEditTriggers(QAbstractItemView.NoEditTriggers)
            tbl_prod.setFixedHeight(min(len(produksi) * 32 + 32, 160))
            tbl_prod.setStyleSheet(_TABLE_STYLE)
            for i, p in enumerate(produksi):
                tbl_prod.insertRow(i)
                plan  = p.get("plan_unit", 0.0)
                reg   = p.get("actual_unit", 0.0)
                ot2h  = p.get("ot_2h", 0.0)
                ot3h  = p.get("ot_3h", 0.0)
                ot11h = p.get("ot_11h", 0.0)
                bal   = (reg + ot2h + ot3h + ot11h) - plan
                tbl_prod.setItem(i, 0, _cell(p.get("model", "")))
                tbl_prod.setItem(i, 1, _cell(f"{plan:.0f}", Qt.AlignCenter))
                tbl_prod.setItem(i, 2, _cell(f"{reg:.0f}", Qt.AlignCenter))
                tbl_prod.setItem(i, 3, _cell(f"{ot2h:.0f}", Qt.AlignCenter))
                tbl_prod.setItem(i, 4, _cell(f"{ot3h:.0f}", Qt.AlignCenter))
                tbl_prod.setItem(i, 5, _cell(f"{ot11h:.0f}", Qt.AlignCenter))
                bal_cell = _cell(f"{bal:.0f}", Qt.AlignCenter)
                bal_cell.setForeground(QColor(220, 80, 80) if bal < 0 else QColor(80, 200, 100))
                tbl_prod.setItem(i, 6, bal_cell)
            lyt.addWidget(tbl_prod)

        # ── Catatan Masalah ──────────────────────────────────────────────────
        lyt.addWidget(_sec_lbl("Catatan Masalah"))
        tbl_cat = QTableWidget()
        tbl_cat.setColumnCount(9)
        tbl_cat.setHorizontalHeaderLabels([
            "No. RA", "Kategori", "Deskripsi", "Penyebab",
            "Tindakan", "PIC", "Start", "End", "Loss Time (H)",
        ])
        tbl_cat.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        for fc in (0, 1, 5, 6, 7, 8):
            tbl_cat.horizontalHeader().setSectionResizeMode(fc, QHeaderView.ResizeToContents)
        tbl_cat.verticalHeader().setVisible(False)
        tbl_cat.setEditTriggers(QAbstractItemView.NoEditTriggers)
        tbl_cat.setWordWrap(True)
        tbl_cat.setFixedHeight(3 * 32 + 32 + 4)
        tbl_cat.setStyleSheet(_TABLE_STYLE)
        for i, c in enumerate(catatan):
            tbl_cat.insertRow(i)
            tbl_cat.setItem(i, 0, _cell(c.get("ra_number", ""), Qt.AlignCenter))
            tbl_cat.setItem(i, 1, _cell(c.get("category", "")))
            tbl_cat.setItem(i, 2, _cell(c.get("description", "")))
            tbl_cat.setItem(i, 3, _cell(c.get("cause", "")))
            tbl_cat.setItem(i, 4, _cell(c.get("corrective_action", "")))
            tbl_cat.setItem(i, 5, _cell(c.get("pic", ""), Qt.AlignCenter))
            tbl_cat.setItem(i, 6, _cell(c.get("start_time", ""), Qt.AlignCenter))
            tbl_cat.setItem(i, 7, _cell(c.get("end_time", ""), Qt.AlignCenter))
            tbl_cat.setItem(i, 8, _cell(f"{c.get('loss_time', 0):.2f}", Qt.AlignCenter))
            tbl_cat.resizeRowToContents(i)
        lyt.addWidget(tbl_cat)

        # ── Manpower ─────────────────────────────────────────────────────────
        if manpower:
            lyt.addWidget(_sec_lbl("Manpower"))
            tbl_mp = QTableWidget()
            tbl_mp.setColumnCount(4)
            tbl_mp.setHorizontalHeaderLabels(["Deskripsi", "Plan", "Actual", "Balance"])
            tbl_mp.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
            for fc in (1, 2, 3):
                tbl_mp.horizontalHeader().setSectionResizeMode(fc, QHeaderView.Fixed)
                tbl_mp.setColumnWidth(fc, 80)
            tbl_mp.verticalHeader().setVisible(False)
            tbl_mp.setEditTriggers(QAbstractItemView.NoEditTriggers)
            tbl_mp.setFixedHeight(len(manpower) * 32 + 32 + 4)
            tbl_mp.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            tbl_mp.setStyleSheet(_TABLE_STYLE)
            for i, m in enumerate(manpower):
                tbl_mp.insertRow(i)
                plan_mp = m.get("plan", 0)
                act_mp  = m.get("act", 0)
                bal_mp  = act_mp - plan_mp
                tbl_mp.setItem(i, 0, _cell(m.get("role", "")))
                tbl_mp.setItem(i, 1, _cell(str(plan_mp), Qt.AlignCenter))
                tbl_mp.setItem(i, 2, _cell(str(act_mp),  Qt.AlignCenter))
                bal_cell = _cell(str(bal_mp), Qt.AlignCenter)
                bal_cell.setForeground(QColor(220, 80, 80) if bal_mp < 0 else QColor(80, 200, 100))
                tbl_mp.setItem(i, 3, bal_cell)
            lyt.addWidget(tbl_mp)

        # ── Absen ────────────────────────────────────────────────────────────
        if absen:
            lyt.addWidget(_sec_lbl("Absen"))
            tbl_absen = QTableWidget()
            tbl_absen.setColumnCount(5)
            tbl_absen.setHorizontalHeaderLabels(["No", "Nama", "NIK", "Shop", "Keterangan"])
            tbl_absen.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            tbl_absen.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
            tbl_absen.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
            tbl_absen.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
            tbl_absen.setColumnWidth(0, 40)
            tbl_absen.setColumnWidth(2, 80)
            tbl_absen.setColumnWidth(3, 60)
            tbl_absen.verticalHeader().setVisible(False)
            tbl_absen.setEditTriggers(QAbstractItemView.NoEditTriggers)
            tbl_absen.setFixedHeight(min(len(absen) * 32 + 32, 200))
            tbl_absen.setStyleSheet(_TABLE_STYLE)
            for i, a in enumerate(absen):
                tbl_absen.insertRow(i)
                tbl_absen.setItem(i, 0, _cell(str(a.get("no", i + 1)), Qt.AlignCenter))
                tbl_absen.setItem(i, 1, _cell(a.get("nama", "")))
                tbl_absen.setItem(i, 2, _cell(a.get("nik", ""),  Qt.AlignCenter))
                tbl_absen.setItem(i, 3, _cell(a.get("shop", ""), Qt.AlignCenter))
                tbl_absen.setItem(i, 4, _cell(a.get("keterangan", "")))
            lyt.addWidget(tbl_absen)

        # ── Inhouse Claim ────────────────────────────────────────────────────
        if inhouse_claim:
            lyt.addWidget(_sec_lbl("Inhouse Claim"))
            tbl_ic = QTableWidget()
            tbl_ic.setColumnCount(11)
            tbl_ic.setHorizontalHeaderLabels([
                "Model", "OP/St", "Item", "Qty", "Satuan",
                "Penyebab", "Tindakan", "Faktor", "Stop (H)", "Lost (H)", "Status",
            ])
            tbl_ic.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            for fc in (0, 1, 3, 4, 7, 8, 9, 10):
                tbl_ic.horizontalHeader().setSectionResizeMode(fc, QHeaderView.ResizeToContents)
            tbl_ic.verticalHeader().setVisible(False)
            tbl_ic.setEditTriggers(QAbstractItemView.NoEditTriggers)
            tbl_ic.setFixedHeight(2 * 32 + 32 + 4)
            tbl_ic.setStyleSheet(_TABLE_STYLE)
            for i, ic in enumerate(inhouse_claim):
                tbl_ic.insertRow(i)
                tbl_ic.setItem(i, 0, _cell(ic.get("model", "")))
                tbl_ic.setItem(i, 1, _cell(ic.get("op_no_st", ""), Qt.AlignCenter))
                tbl_ic.setItem(i, 2, _cell(ic.get("item", "")))
                tbl_ic.setItem(i, 3, _cell(f"{ic.get('qty', 0):.0f}", Qt.AlignCenter))
                tbl_ic.setItem(i, 4, _cell(ic.get("satuan", ""), Qt.AlignCenter))
                tbl_ic.setItem(i, 5, _cell(ic.get("penyebab", "")))
                tbl_ic.setItem(i, 6, _cell(ic.get("tindakan", "")))
                tbl_ic.setItem(i, 7, _cell(ic.get("faktor", ""), Qt.AlignCenter))
                tbl_ic.setItem(i, 8, _cell(f"{ic.get('stop_hr', 0):.2f}", Qt.AlignCenter))
                tbl_ic.setItem(i, 9, _cell(f"{ic.get('lost_hr', 0):.2f}", Qt.AlignCenter))
                it_status = _cell(ic.get("status", ""), Qt.AlignCenter)
                s = ic.get("status", "")
                if s == "NG":
                    it_status.setForeground(QColor(220, 100, 100))
                elif s == "PENDING":
                    it_status.setForeground(QColor(220, 170, 80))
                elif s == "OK":
                    it_status.setForeground(QColor(80, 200, 100))
                tbl_ic.setItem(i, 10, it_status)
            lyt.addWidget(tbl_ic)

        lyt.addStretch()
        scroll.setWidget(container)
        outer_lyt.addWidget(scroll)

        btn_box = QDialogButtonBox(QDialogButtonBox.Close)
        btn_box.setStyleSheet("""
            QPushButton { background-color: rgb(60, 65, 75); color: rgb(200, 200, 200);
                border: none; border-radius: 5px; padding: 6px 18px; font-size: 11px; }
            QPushButton:hover { background-color: rgb(75, 80, 90); }
        """)
        btn_box.rejected.connect(dlg.close)
        outer_lyt.addWidget(btn_box)
        dlg.exec()

    def _edit(self, report_id):
        QMessageBox.information(self, "Edit", f"Fitur edit laporan #{report_id} akan segera tersedia.")

    def _hapus(self, report_id):
        reply = QMessageBox.question(
            self, "Konfirmasi Hapus",
            f"Hapus laporan #{report_id}?\nSemua catatan masalah terkait juga akan dihapus.\nTindakan ini tidak dapat dibatalkan.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            ok, msg = hapus_laporan(report_id)
            if ok:
                QMessageBox.information(self, "Berhasil", msg)
                self.load_data_harian()
            else:
                QMessageBox.critical(self, "Gagal", msg)

    def _export_rah(self):
        try:
            import openpyxl
            from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        except ImportError:
            QMessageBox.critical(self, "Error", "openpyxl tidak terinstall.\nJalankan: pip install openpyxl")
            return

        row_count = self.tabel_harian.rowCount()
        if row_count == 0:
            QMessageBox.warning(self, "Peringatan", "Tidak ada data untuk diekspor.")
            return

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Riwayat Harian"

        thin = Side(style="thin", color="3C4147")
        border = Border(left=thin, right=thin, top=thin, bottom=thin)
        hdr_fill = PatternFill("solid", fgColor="1C2028")
        hdr_font = Font(color="9696A0", bold=True, size=10)

        col_headers = ["No", "Tanggal", "Section", "Shift", "Koordinator", "Jml Masalah"]
        for ci, h in enumerate(col_headers, 1):
            cell = ws.cell(row=1, column=ci, value=h)
            cell.fill = hdr_fill
            cell.font = hdr_font
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = border

        center_cols = {0, 1, 3, 5}
        for ri in range(row_count):
            for ci in range(6):
                item = self.tabel_harian.item(ri, ci)
                val = item.text() if item else ""
                cell = ws.cell(row=ri + 2, column=ci + 1, value=val)
                cell.alignment = Alignment(
                    horizontal="center" if ci in center_cols else "left",
                    vertical="center",
                )
                cell.border = border

        for ci, w in enumerate([6, 12, 30, 12, 22, 14], 1):
            ws.column_dimensions[openpyxl.utils.get_column_letter(ci)].width = w
        ws.row_dimensions[1].height = 20

        downloads = os.path.join(os.path.expanduser("~"), "Downloads")
        filepath = os.path.join(downloads, f"riwayat_harian_{QDate.currentDate().toString('yyyyMMdd')}.xlsx")
        try:
            wb.save(filepath)
            QMessageBox.information(self, "Export Berhasil", f"File disimpan di:\n{filepath}")
        except Exception as e:
            QMessageBox.critical(self, "Gagal Export", f"Gagal menyimpan file:\n{e}")

    # ── Tab 2: Rekap Bulanan ─────────────────────────────────────────────────

    def _build_tab_rekap(self):
        tab = QWidget()
        tab.setStyleSheet("background: transparent;")
        outer = QVBoxLayout(tab)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        main = QVBoxLayout(container)
        main.setContentsMargins(15, 15, 15, 15)
        main.setSpacing(12)

        # Filter card
        card_f = QFrame()
        card_f.setStyleSheet(_CARD_STYLE)
        fl = QHBoxLayout(card_f)
        fl.setContentsMargins(16, 12, 16, 12)
        fl.setSpacing(10)

        fl.addWidget(self._flabel("Section"))
        self.combo_section_rekap = QComboBox()
        self.combo_section_rekap.setMinimumHeight(30)
        self.combo_section_rekap.setMinimumWidth(155)
        self.combo_section_rekap.setStyleSheet(_COMBO_STYLE)
        self.combo_section_rekap.addItem("Semua", None)
        fl.addWidget(self.combo_section_rekap)

        fl.addWidget(self._flabel("Bulan"))
        self.combo_bulan = QComboBox()
        self.combo_bulan.setMinimumHeight(30)
        self.combo_bulan.setMinimumWidth(115)
        self.combo_bulan.setStyleSheet(_COMBO_STYLE)
        bulan_names = [
            "Januari", "Februari", "Maret", "April", "Mei", "Juni",
            "Juli", "Agustus", "September", "Oktober", "November", "Desember",
        ]
        for i, name in enumerate(bulan_names, 1):
            self.combo_bulan.addItem(name, i)
        self.combo_bulan.setCurrentIndex(QDate.currentDate().month() - 1)
        fl.addWidget(self.combo_bulan)

        fl.addWidget(self._flabel("Tahun"))
        self.input_tahun = QLineEdit()
        self.input_tahun.setMinimumHeight(30)
        self.input_tahun.setFixedWidth(70)
        self.input_tahun.setStyleSheet(_INPUT_STYLE)
        self.input_tahun.setText(str(QDate.currentDate().year()))
        fl.addWidget(self.input_tahun)

        fl.addStretch()

        btn_tampil = QPushButton("Tampilkan")
        btn_tampil.setMinimumSize(90, 32)
        btn_tampil.setStyleSheet(_BTN_CARI)
        btn_tampil.clicked.connect(self.load_rekap_bulanan)
        fl.addWidget(btn_tampil)

        main.addWidget(card_f)

        # Table card
        card_t = QFrame()
        card_t.setStyleSheet(_CARD_STYLE)
        tl = QVBoxLayout(card_t)
        tl.setContentsMargins(16, 16, 16, 16)
        tl.setSpacing(8)

        hdr_row = QHBoxLayout()
        self.lbl_info_r = QLabel("Pilih filter dan klik Tampilkan.")
        self.lbl_info_r.setStyleSheet("color: rgb(130, 140, 165); font-size: 10px;")
        hdr_row.addWidget(self.lbl_info_r)
        hdr_row.addStretch()
        btn_export_r = QPushButton("Export Excel")
        btn_export_r.setMinimumSize(100, 30)
        btn_export_r.setStyleSheet(_BTN_EXPORT)
        btn_export_r.clicked.connect(self._export_rekap)
        hdr_row.addWidget(btn_export_r)
        tl.addLayout(hdr_row)

        self.tabel_rekap = QTableWidget()
        self.tabel_rekap.setColumnCount(3)
        self.tabel_rekap.setHorizontalHeaderLabels(
            ["Kategori", "Total Loss Time (H)", "Persentase (%)"]
        )
        self.tabel_rekap.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tabel_rekap.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.tabel_rekap.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.tabel_rekap.setColumnWidth(1, 165)
        self.tabel_rekap.setColumnWidth(2, 130)
        self.tabel_rekap.verticalHeader().setVisible(False)
        self.tabel_rekap.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabel_rekap.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabel_rekap.setStyleSheet(_TABLE_STYLE)
        tl.addWidget(self.tabel_rekap)

        # Summary bar
        sum_frame = QFrame()
        sum_frame.setStyleSheet(
            "QFrame { background-color: rgb(33, 37, 43); border-radius: 6px; }"
        )
        sum_lyt = QHBoxLayout(sum_frame)
        sum_lyt.setContentsMargins(16, 10, 16, 10)
        sum_lyt.setSpacing(30)

        self.lbl_total_hour = QLabel("Total Working Hour: —")
        self.lbl_total_hour.setStyleSheet(
            "color: rgb(200, 200, 200); font-size: 12px; font-weight: bold;"
        )
        self.lbl_ratio = QLabel("Ratio Produktivitas: —")
        self.lbl_ratio.setStyleSheet(
            "color: rgb(130, 140, 165); font-size: 12px; font-weight: bold;"
        )
        sum_lyt.addWidget(self.lbl_total_hour)
        sum_lyt.addWidget(self.lbl_ratio)
        sum_lyt.addStretch()
        tl.addWidget(sum_frame)

        main.addWidget(card_t)
        main.addStretch()
        scroll.setWidget(container)
        outer.addWidget(scroll)
        return tab

    def load_rekap_bulanan(self):
        section_id = self.combo_section_rekap.currentData()
        bulan = self.combo_bulan.currentData()
        try:
            tahun = int(self.input_tahun.text().strip())
        except ValueError:
            QMessageBox.warning(self, "Peringatan", "Tahun tidak valid.")
            return

        try:
            rows, total_hour = _db_rekap_bulanan(section_id, bulan, tahun)
        except Exception as e:
            self.lbl_info_r.setText(f"Gagal memuat data: {e}")
            self.tabel_rekap.setRowCount(0)
            return

        total_loss = sum(r[1] for r in rows)
        self.tabel_rekap.setRowCount(0)
        self.lbl_info_r.setText(
            f"{len(rows)} kategori — {self.combo_bulan.currentText()} {tahun}"
        )

        for i, (kategori, loss) in enumerate(rows):
            self.tabel_rekap.insertRow(i)
            pct = (loss / total_loss * 100) if total_loss > 0 else 0.0

            it_kat = QTableWidgetItem(kategori)
            it_kat.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            it_loss = QTableWidgetItem(f"{loss:.2f}")
            it_loss.setTextAlignment(Qt.AlignCenter)
            it_pct = QTableWidgetItem(f"{pct:.1f}%")
            it_pct.setTextAlignment(Qt.AlignCenter)

            self.tabel_rekap.setItem(i, 0, it_kat)
            self.tabel_rekap.setItem(i, 1, it_loss)
            self.tabel_rekap.setItem(i, 2, it_pct)
            self.tabel_rekap.setRowHeight(i, 32)

        self.lbl_total_hour.setText(f"Total Working Hour: {total_hour:.2f} H")
        if total_hour > 0:
            ratio = max(0.0, (total_hour - total_loss) / total_hour * 100)
            color = (
                "rgb(130, 220, 140)" if ratio >= 80
                else "rgb(220, 170, 80)" if ratio >= 60
                else "rgb(220, 100, 100)"
            )
            self.lbl_ratio.setText(f"Ratio Produktivitas: {ratio:.1f}%")
            self.lbl_ratio.setStyleSheet(
                f"color: {color}; font-size: 12px; font-weight: bold;"
            )
        else:
            self.lbl_ratio.setText("Ratio Produktivitas: —")
            self.lbl_ratio.setStyleSheet(
                "color: rgb(130, 140, 165); font-size: 12px; font-weight: bold;"
            )

    def _export_rekap(self):
        try:
            import openpyxl
            from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        except ImportError:
            QMessageBox.critical(self, "Error", "openpyxl tidak terinstall.\nJalankan: pip install openpyxl")
            return

        row_count = self.tabel_rekap.rowCount()
        if row_count == 0:
            QMessageBox.warning(self, "Peringatan", "Tidak ada data untuk diekspor.")
            return

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Rekap Bulanan"

        thin = Side(style="thin", color="3C4147")
        border = Border(left=thin, right=thin, top=thin, bottom=thin)
        hdr_fill = PatternFill("solid", fgColor="1C2028")

        for ci, h in enumerate(["Kategori", "Total Loss Time (H)", "Persentase (%)"], 1):
            cell = ws.cell(row=1, column=ci, value=h)
            cell.fill = hdr_fill
            cell.font = Font(color="9696A0", bold=True, size=10)
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = border

        for ri in range(row_count):
            for ci in range(3):
                item = self.tabel_rekap.item(ri, ci)
                val = item.text() if item else ""
                cell = ws.cell(row=ri + 2, column=ci + 1, value=val)
                cell.alignment = Alignment(
                    horizontal="left" if ci == 0 else "center", vertical="center"
                )
                cell.border = border

        sum_row = row_count + 3
        ws.cell(row=sum_row, column=1, value=self.lbl_total_hour.text()).font = Font(
            bold=True, color="C8C8C8"
        )
        ws.cell(row=sum_row + 1, column=1, value=self.lbl_ratio.text()).font = Font(
            bold=True, color="82DC8C"
        )

        for ci, w in enumerate([30, 22, 16], 1):
            ws.column_dimensions[openpyxl.utils.get_column_letter(ci)].width = w

        downloads = os.path.join(os.path.expanduser("~"), "Downloads")
        filepath = os.path.join(
            downloads, f"rekap_bulanan_{QDate.currentDate().toString('yyyyMMdd')}.xlsx"
        )
        try:
            wb.save(filepath)
            QMessageBox.information(self, "Export Berhasil", f"File disimpan di:\n{filepath}")
        except Exception as e:
            QMessageBox.critical(self, "Gagal Export", f"Gagal menyimpan file:\n{e}")

    # ── Tab 3: NG & Pending ──────────────────────────────────────────────────

    def _build_tab_ng_pending(self):
        tab = QWidget()
        tab.setStyleSheet("background: transparent;")
        outer = QVBoxLayout(tab)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        main = QVBoxLayout(container)
        main.setContentsMargins(15, 15, 15, 15)
        main.setSpacing(12)

        # Filter card
        card_f = QFrame()
        card_f.setStyleSheet(_CARD_STYLE)
        fl = QHBoxLayout(card_f)
        fl.setContentsMargins(16, 12, 16, 12)
        fl.setSpacing(10)

        fl.addWidget(self._flabel("Section"))
        self.combo_section_ng = QComboBox()
        self.combo_section_ng.setMinimumHeight(30)
        self.combo_section_ng.setMinimumWidth(155)
        self.combo_section_ng.setStyleSheet(_COMBO_STYLE)
        self.combo_section_ng.addItem("Semua", None)
        fl.addWidget(self.combo_section_ng)

        fl.addWidget(self._flabel("Dari"))
        self.date_ng_from = QDateEdit()
        self.date_ng_from.setCalendarPopup(True)
        self.date_ng_from.setMinimumHeight(30)
        self.date_ng_from.setStyleSheet(_DATE_STYLE)
        self.date_ng_from.setDate(QDate.currentDate().addMonths(-1))
        fl.addWidget(self.date_ng_from)

        fl.addWidget(self._flabel("Sampai"))
        self.date_ng_to = QDateEdit()
        self.date_ng_to.setCalendarPopup(True)
        self.date_ng_to.setMinimumHeight(30)
        self.date_ng_to.setStyleSheet(_DATE_STYLE)
        self.date_ng_to.setDate(QDate.currentDate())
        fl.addWidget(self.date_ng_to)

        fl.addStretch()

        btn_cari_ng = QPushButton("Cari")
        btn_cari_ng.setMinimumSize(76, 32)
        btn_cari_ng.setStyleSheet(_BTN_CARI)
        btn_cari_ng.clicked.connect(self.load_ng_pending)
        fl.addWidget(btn_cari_ng)

        btn_export_ng = QPushButton("Export Excel")
        btn_export_ng.setMinimumSize(100, 32)
        btn_export_ng.setStyleSheet(_BTN_EXPORT)
        btn_export_ng.clicked.connect(self._export_ng_pending)
        fl.addWidget(btn_export_ng)

        main.addWidget(card_f)

        # Inhouse Claim card
        card_ic = QFrame()
        card_ic.setStyleSheet(_CARD_STYLE)
        ic_lyt = QVBoxLayout(card_ic)
        ic_lyt.setContentsMargins(16, 16, 16, 16)
        ic_lyt.setSpacing(8)

        ic_hdr = QHBoxLayout()
        lbl_ic = QLabel("Inhouse Claim (NG)")
        lbl_ic.setStyleSheet("color: #ffffff; font-size: 12px; font-weight: bold;")
        self.lbl_info_ic = QLabel("")
        self.lbl_info_ic.setStyleSheet("color: rgb(130, 140, 165); font-size: 10px;")
        ic_hdr.addWidget(lbl_ic)
        ic_hdr.addWidget(self.lbl_info_ic)
        ic_hdr.addStretch()
        ic_lyt.addLayout(ic_hdr)

        self.tabel_ic = QTableWidget()
        self.tabel_ic.setColumnCount(12)
        self.tabel_ic.setHorizontalHeaderLabels([
            "No", "Tanggal", "Model", "OP/St", "Item", "Qty",
            "Penyebab", "Tindakan", "Faktor", "Stop (H)", "Lost (H)", "Status",
        ])
        self.tabel_ic.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        for fc in (0, 1, 2, 3, 5, 9, 10, 11):
            self.tabel_ic.horizontalHeader().setSectionResizeMode(
                fc, QHeaderView.ResizeToContents
            )
        self.tabel_ic.verticalHeader().setVisible(False)
        self.tabel_ic.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabel_ic.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabel_ic.setMinimumHeight(200)
        self.tabel_ic.setStyleSheet(_TABLE_STYLE)
        ic_lyt.addWidget(self.tabel_ic)

        main.addWidget(card_ic)

        # Part Pending card
        card_pp = QFrame()
        card_pp.setStyleSheet(_CARD_STYLE)
        pp_lyt = QVBoxLayout(card_pp)
        pp_lyt.setContentsMargins(16, 16, 16, 16)
        pp_lyt.setSpacing(8)

        pp_hdr = QHBoxLayout()
        lbl_pp = QLabel("Part Pending")
        lbl_pp.setStyleSheet("color: #ffffff; font-size: 12px; font-weight: bold;")
        self.lbl_info_pp = QLabel("")
        self.lbl_info_pp.setStyleSheet("color: rgb(130, 140, 165); font-size: 10px;")
        pp_hdr.addWidget(lbl_pp)
        pp_hdr.addWidget(self.lbl_info_pp)
        pp_hdr.addStretch()
        pp_lyt.addLayout(pp_hdr)

        self.tabel_pp = QTableWidget()
        self.tabel_pp.setColumnCount(11)
        self.tabel_pp.setHorizontalHeaderLabels([
            "No", "Tanggal", "Model", "OP/St", "Item", "Qty",
            "Penyebab", "Tindakan", "Faktor", "Stop (H)", "Lost (H)",
        ])
        self.tabel_pp.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        for fc in (0, 1, 2, 3, 5, 9, 10):
            self.tabel_pp.horizontalHeader().setSectionResizeMode(
                fc, QHeaderView.ResizeToContents
            )
        self.tabel_pp.verticalHeader().setVisible(False)
        self.tabel_pp.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabel_pp.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabel_pp.setMinimumHeight(180)
        self.tabel_pp.setStyleSheet(_TABLE_STYLE)
        pp_lyt.addWidget(self.tabel_pp)

        main.addWidget(card_pp)
        main.addStretch()
        scroll.setWidget(container)
        outer.addWidget(scroll)
        return tab

    def load_ng_pending(self):
        section_id = self.combo_section_ng.currentData()
        date_from = self.date_ng_from.date().toString("yyyy-MM-dd")
        date_to = self.date_ng_to.date().toString("yyyy-MM-dd")

        try:
            inhouse_ng, inhouse_pending = _db_ng_pending(section_id, date_from, date_to)
        except Exception as e:
            self.lbl_info_ic.setText(f"Gagal memuat data: {e}")
            self.tabel_ic.setRowCount(0)
            self.tabel_pp.setRowCount(0)
            return

        def _item(text, align=Qt.AlignCenter):
            it = QTableWidgetItem(str(text) if text is not None else "")
            it.setTextAlignment(align)
            return it

        self.tabel_ic.setRowCount(0)
        self.lbl_info_ic.setText(f"— {len(inhouse_ng)} data")
        for i, row in enumerate(inhouse_ng):
            tanggal, model, op_no_st, item, qty, penyebab, tindakan, faktor, stop_hr, lost_hr, status = row
            self.tabel_ic.insertRow(i)
            self.tabel_ic.setItem(i, 0,  _item(i + 1))
            self.tabel_ic.setItem(i, 1,  _item(str(tanggal) if tanggal else ""))
            self.tabel_ic.setItem(i, 2,  _item(model or ""))
            self.tabel_ic.setItem(i, 3,  _item(op_no_st or ""))
            self.tabel_ic.setItem(i, 4,  _item(item or "", Qt.AlignLeft | Qt.AlignVCenter))
            self.tabel_ic.setItem(i, 5,  _item(f"{float(qty):.0f}" if qty is not None else ""))
            self.tabel_ic.setItem(i, 6,  _item(penyebab or "", Qt.AlignLeft | Qt.AlignVCenter))
            self.tabel_ic.setItem(i, 7,  _item(tindakan or "", Qt.AlignLeft | Qt.AlignVCenter))
            self.tabel_ic.setItem(i, 8,  _item(faktor or ""))
            self.tabel_ic.setItem(i, 9,  _item(f"{float(stop_hr):.2f}" if stop_hr is not None else "0.00"))
            self.tabel_ic.setItem(i, 10, _item(f"{float(lost_hr):.2f}" if lost_hr is not None else "0.00"))
            it_status = _item(status or "")
            it_status.setForeground(QColor(220, 100, 100))
            self.tabel_ic.setItem(i, 11, it_status)
            self.tabel_ic.setRowHeight(i, 32)

        self.tabel_pp.setRowCount(0)
        self.lbl_info_pp.setText(f"— {len(inhouse_pending)} data")
        for i, row in enumerate(inhouse_pending):
            tanggal, model, op_no_st, item, qty, penyebab, tindakan, faktor, stop_hr, lost_hr = row
            self.tabel_pp.insertRow(i)
            self.tabel_pp.setItem(i, 0,  _item(i + 1))
            self.tabel_pp.setItem(i, 1,  _item(str(tanggal) if tanggal else ""))
            self.tabel_pp.setItem(i, 2,  _item(model or ""))
            self.tabel_pp.setItem(i, 3,  _item(op_no_st or ""))
            self.tabel_pp.setItem(i, 4,  _item(item or "", Qt.AlignLeft | Qt.AlignVCenter))
            self.tabel_pp.setItem(i, 5,  _item(f"{float(qty):.0f}" if qty is not None else ""))
            self.tabel_pp.setItem(i, 6,  _item(penyebab or "", Qt.AlignLeft | Qt.AlignVCenter))
            self.tabel_pp.setItem(i, 7,  _item(tindakan or "", Qt.AlignLeft | Qt.AlignVCenter))
            self.tabel_pp.setItem(i, 8,  _item(faktor or ""))
            self.tabel_pp.setItem(i, 9,  _item(f"{float(stop_hr):.2f}" if stop_hr is not None else "0.00"))
            self.tabel_pp.setItem(i, 10, _item(f"{float(lost_hr):.2f}" if lost_hr is not None else "0.00"))
            self.tabel_pp.setRowHeight(i, 32)

    def _export_ng_pending(self):
        try:
            import openpyxl
            from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        except ImportError:
            QMessageBox.critical(self, "Error", "openpyxl tidak terinstall.\nJalankan: pip install openpyxl")
            return

        ic_count = self.tabel_ic.rowCount()
        pp_count = self.tabel_pp.rowCount()
        if ic_count == 0 and pp_count == 0:
            QMessageBox.warning(self, "Peringatan", "Tidak ada data untuk diekspor.")
            return

        wb = openpyxl.Workbook()
        thin = Side(style="thin", color="3C4147")
        border = Border(left=thin, right=thin, top=thin, bottom=thin)
        hdr_fill = PatternFill("solid", fgColor="1C2028")
        hdr_font = Font(color="9696A0", bold=True, size=10)

        ws_ic = wb.active
        ws_ic.title = "Inhouse Claim"
        ic_cols = [
            "No", "Tanggal", "Model", "OP/St", "Item", "Qty",
            "Penyebab", "Tindakan", "Faktor", "Stop (H)", "Lost (H)", "Status",
        ]
        for ci, h in enumerate(ic_cols, 1):
            c = ws_ic.cell(row=1, column=ci, value=h)
            c.fill = hdr_fill
            c.font = hdr_font
            c.alignment = Alignment(horizontal="center", vertical="center")
            c.border = border
        center_ic = {0, 1, 2, 3, 5, 8, 9, 10, 11}
        for ri in range(ic_count):
            for ci in range(12):
                item = self.tabel_ic.item(ri, ci)
                val = item.text() if item else ""
                cell = ws_ic.cell(row=ri + 2, column=ci + 1, value=val)
                cell.alignment = Alignment(
                    horizontal="center" if ci in center_ic else "left", vertical="center"
                )
                cell.border = border
        for ci, w in enumerate([5, 12, 12, 10, 20, 6, 22, 22, 10, 8, 8, 8], 1):
            ws_ic.column_dimensions[openpyxl.utils.get_column_letter(ci)].width = w

        ws_pp = wb.create_sheet("Part Pending")
        pp_cols = [
            "No", "Tanggal", "Model", "OP/St", "Item", "Qty",
            "Penyebab", "Tindakan", "Faktor", "Stop (H)", "Lost (H)",
        ]
        for ci, h in enumerate(pp_cols, 1):
            c = ws_pp.cell(row=1, column=ci, value=h)
            c.fill = hdr_fill
            c.font = hdr_font
            c.alignment = Alignment(horizontal="center", vertical="center")
            c.border = border
        center_pp = {0, 1, 2, 3, 5, 8, 9, 10}
        for ri in range(pp_count):
            for ci in range(11):
                item = self.tabel_pp.item(ri, ci)
                val = item.text() if item else ""
                cell = ws_pp.cell(row=ri + 2, column=ci + 1, value=val)
                cell.alignment = Alignment(
                    horizontal="center" if ci in center_pp else "left", vertical="center"
                )
                cell.border = border
        for ci, w in enumerate([5, 12, 12, 10, 20, 6, 22, 22, 10, 8, 8], 1):
            ws_pp.column_dimensions[openpyxl.utils.get_column_letter(ci)].width = w

        downloads = os.path.join(os.path.expanduser("~"), "Downloads")
        filepath = os.path.join(
            downloads, f"ng_pending_{QDate.currentDate().toString('yyyyMMdd')}.xlsx"
        )
        try:
            wb.save(filepath)
            QMessageBox.information(self, "Export Berhasil", f"File disimpan di:\n{filepath}")
        except Exception as e:
            QMessageBox.critical(self, "Gagal Export", f"Gagal menyimpan file:\n{e}")

    @staticmethod
    def _flabel(text):
        lbl = QLabel(text)
        lbl.setStyleSheet("color: rgb(150, 150, 150); font-size: 11px;")
        return lbl

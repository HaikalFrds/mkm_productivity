import os

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QComboBox, QPushButton, QDateEdit,
    QScrollArea, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QDialog, QDialogButtonBox, QAbstractItemView,
    QTabWidget, QLineEdit,
)
from PySide6.QtCore import Qt, QDate, QThread, Signal
from PySide6.QtGui import QColor

from modules.db_auth import get_connection, release_connection
from modules.db_laporan import (
    get_all_sections, get_all_shifts, get_all_category_names,
    get_detail_laporan, hapus_laporan, get_monthly_productivity,
    get_production_volume,
)
from modules.export_excel import export_loss_time_record, export_inhouse_ng_pending


# Shared styles

# (prev: #1e1e1e bg, #303030 border, #252525 card, #969696 text-sec)

_DATE_STYLE = """
    QDateEdit {
        background-color: #2a2a2a;
        border: 1px solid #2e2e2e;
        border-radius: 0px; padding-left: 8px;
        color: #f0f0f0; font-size: 11px;
    }
    QDateEdit:focus { border: 1px solid #da291c; }
    QDateEdit::drop-down {
        border: none; width: 22px;
        subcontrol-origin: padding; subcontrol-position: top right;
    }
"""

_COMBO_STYLE = """
    QComboBox {
        background-color: #2a2a2a;
        border: 1px solid #2e2e2e;
        border-radius: 0px; padding-left: 8px;
        color: #f0f0f0; font-size: 11px;
    }
    QComboBox:focus { border: 1px solid #da291c; }
    QComboBox::drop-down { border: none; width: 24px; }
    QComboBox QAbstractItemView {
        background-color: #1a1a1a; color: #f0f0f0;
        selection-background-color: #2a2a2a;
        border: 1px solid #2e2e2e;
    }
"""

_TABLE_STYLE = """
    QTableWidget {
        background-color: #1a1a1a;
        border: 1px solid #2e2e2e; border-radius: 0px;
        gridline-color: #2e2e2e;
    }
    QTableWidget::item {
        color: #f0f0f0; padding: 4px 8px;
        background-color: #222222;
        border-bottom: 1px solid #2e2e2e;
    }
    QTableWidget::item:alternate { background-color: #1e1e1e; }
    QTableWidget::item:selected { background-color: #2a2a2a; color: #ffffff; }
    QHeaderView::section {
        background-color: #111111; color: #888888;
        border: none; border-bottom: 1px solid #2e2e2e;
        border-right: 1px solid #2e2e2e;
        padding: 5px 8px; font-weight: bold; font-size: 10px;
        text-transform: uppercase; letter-spacing: 1px;
    }
"""

_TAB_STYLE = """
    QTabWidget::pane { background-color: transparent; border: none; }
    QTabBar::tab {
        background-color: #1a1a1a; color: #555555;
        padding: 8px 22px; margin-right: 2px;
        border-radius: 0px; font-size: 10px; font-weight: bold;
        letter-spacing: 1px; text-transform: uppercase;
    }
    QTabBar::tab:selected {
        background-color: #222222; color: #f0f0f0;
        border-bottom: 2px solid #da291c;
    }
    QTabBar::tab:hover:!selected {
        background-color: #222222; color: #f0f0f0;
    }
"""

_INPUT_STYLE = """
    QLineEdit {
        background-color: #2a2a2a;
        border: 1px solid #2e2e2e; border-radius: 0px;
        padding-left: 8px; color: #f0f0f0; font-size: 11px;
    }
    QLineEdit:focus { border: 1px solid #da291c; }
"""

_CARD_STYLE = "QFrame { background-color: #222222; border-radius: 0px; }"

_BTN_CARI = """
    QPushButton {
        background-color: #da291c; color: #ffffff;
        border: none; border-radius: 0px; font-size: 11px; padding: 0 12px;
        text-transform: uppercase; letter-spacing: 1px;
    }
    QPushButton:hover { background-color: #b01e0a; }
"""

_BTN_RESET = """
    QPushButton {
        background-color: #2a2a2a; color: #888888;
        border: 1px solid #3a3a3a; border-radius: 0px; font-size: 11px; padding: 0 12px;
    }
    QPushButton:hover { background-color: #333333; color: #f0f0f0; }
"""

_BTN_EXPORT = """
    QPushButton {
        background-color: #1a2a1a; color: #22863a;
        border: 1px solid #1a4a1a; border-radius: 0px; font-size: 11px; padding: 0 12px;
    }
    QPushButton:hover { background-color: #1e341e; }
"""


#  DB helpers

def _db_display_line_stop(section_id, bulan, tahun, factor=None):
    conn = get_connection()
    try:
        cur = conn.cursor()
        sec = " AND dr.section_id = %s" if section_id is not None else ""
        p = [bulan, tahun] + ([section_id] if section_id else [])

        cur.execute(f"""
            SELECT
                COALESCE(SUM(s.total_hours), 0) +
                COALESCE(SUM(
                    CASE WHEN dp.ot_2h  THEN 2.0  ELSE 0 END +
                    CASE WHEN dp.ot_3h  THEN 3.0  ELSE 0 END +
                    CASE WHEN dp.ot_11h THEN 11.0 ELSE 0 END
                ), 0)
            FROM daily_report dr
            JOIN shift s ON s.id = dr.shift_id
            LEFT JOIN daily_production dp ON dp.report_id = dr.id
            WHERE EXTRACT(MONTH FROM dr.date) = %s
              AND EXTRACT(YEAR  FROM dr.date) = %s {sec}
        """, p)
        total_hour = float((cur.fetchone() or [0])[0] or 0)

        extra = ""
        p2 = list(p)
        if factor and factor != "Semua":
            extra += " AND pc.name = %s"
            p2.append(factor)

        cur.execute(f"""
            SELECT
                dr.date,
                pr.ra_number,
                pr.description,
                pr.cause,
                pr.corrective_action,
                COALESCE(pc.name, 'Others') AS factor,
                COALESCE(pr.loss_time, 0),
                COALESCE(pr.down_time, 0)
            FROM problem_record pr
            JOIN daily_report dr ON dr.id = pr.report_id
            LEFT JOIN problem_category pc ON pc.id = pr.category_id
            WHERE EXTRACT(MONTH FROM dr.date) = %s
              AND EXTRACT(YEAR  FROM dr.date) = %s {sec} {extra}
            ORDER BY dr.date ASC, pr.id ASC
        """, p2)
        rows = cur.fetchall()
        cur.close()
        return rows, total_hour
    except Exception:
        raise
    finally:
        release_connection(conn)


def _db_ng_pending(section_id, date_from, date_to):
    conn = get_connection()
    try:
        cur = conn.cursor()
        sec = " AND dr.section_id = %s" if section_id is not None else ""

        p = [date_from, date_to] + ([section_id] if section_id else [])
        cur.execute(f"""
            SELECT ic.tanggal, ic.model, ic.op_no_st, ic.item, ic.qty,
                   ic.penyebab, ic.tindakan, ic.faktor, ic.stop_hr, ic.lost_hr, ic.status
            FROM inhouse_claim ic
            JOIN daily_report dr ON dr.id = ic.report_id
            WHERE dr.date BETWEEN %s AND %s AND UPPER(ic.status) = 'NG' {sec}
            ORDER BY ic.tanggal DESC, ic.id DESC
        """, p)
        inhouse_ng = cur.fetchall()

        cur.execute(f"""
            SELECT ic.tanggal, ic.model, ic.op_no_st, ic.item, ic.qty,
                   ic.penyebab, ic.tindakan, ic.faktor, ic.stop_hr, ic.lost_hr
            FROM inhouse_claim ic
            JOIN daily_report dr ON dr.id = ic.report_id
            WHERE dr.date BETWEEN %s AND %s AND UPPER(ic.status) = 'PENDING' {sec}
            ORDER BY ic.tanggal DESC, ic.id DESC
        """, p)
        inhouse_pending = cur.fetchall()

        cur.close()
        return inhouse_ng, inhouse_pending
    except Exception:
        raise
    finally:
        release_connection(conn)


# Background worker

class _RiwayatWorker(QThread):
    finished = Signal(list)
    error    = Signal(str)

    def __init__(self, section_id, shift_name, date_from, date_to):
        super().__init__()
        self.section_id = section_id
        self.shift_name = shift_name
        self.date_from  = date_from
        self.date_to    = date_to

    def run(self):
        try:
            from modules.db_laporan import get_riwayat_laporan
            rows = get_riwayat_laporan(
                section_id=self.section_id,
                shift_name=self.shift_name,
                date_from=self.date_from,
                date_to=self.date_to,
            )
            self.finished.emit(rows)
        except Exception as e:
            self.error.emit(str(e))


# Widget

class RiwayatLaporanWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._sections_loaded = False
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
            # combo_section (Riwayat Harian) — tanpa item "Semua", shop wajib dipilih
            self.combo_section.blockSignals(True)
            for sid, sname in sections:
                self.combo_section.addItem(sname, sid)
            self.combo_section.blockSignals(False)
            # combo lain — dengan item "Semua"
            for combo in (self.combo_section_rekap, self.combo_section_ng, self.combo_prod_section):
                combo.blockSignals(True)
                for sid, sname in sections:
                    combo.addItem(sname, sid)
                combo.blockSignals(False)
            # combo volume produksi — tanpa "Semua", shop wajib dipilih
            self.combo_vol_section.blockSignals(True)
            for sid, sname in sections:
                self.combo_vol_section.addItem(sname, sid)
            self.combo_vol_section.blockSignals(False)
        except Exception as e:
            QMessageBox.warning(self, "Peringatan", f"Gagal memuat daftar shop: {e}")
        try:
            shifts = get_all_shifts()
            self.combo_shift.blockSignals(True)
            self.combo_shift.clear()
            self.combo_shift.addItem("Semua", None)
            for s in shifts:
                self.combo_shift.addItem(s["name"])
            self.combo_shift.blockSignals(False)
        except Exception as e:
            QMessageBox.warning(self, "Peringatan", f"Gagal memuat daftar shift: {e}")
        self._sections_loaded = True

    def _on_tab_changed(self, idx):
        if idx == 1:
            self.load_rekap_bulanan()
        elif idx == 2:
            self.load_ng_pending()
        elif idx == 3:
            self.load_produktivitas()
        elif idx == 4:
            pass  # tidak auto-load, user harus pilih shop dulu

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(_TAB_STYLE)
        self.tabs.currentChanged.connect(self._on_tab_changed)
        self.tabs.addTab(self._build_tab_harian(), "Riwayat Harian")
        self.tabs.addTab(self._build_tab_rekap(), "Rekap Bulanan")
        self.tabs.addTab(self._build_tab_ng_pending(), "NG & Pending")
        self.tabs.addTab(self._build_tab_produktivitas(), "Produktivitas")
        self.tabs.addTab(self._build_tab_volume(),       "Volume Produksi")
        outer.addWidget(self.tabs)

    # Tab 1: Riwayat Harian

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

        fl.addWidget(self._flabel("Shop"))
        self.combo_section = QComboBox()
        self.combo_section.setMinimumHeight(30)
        self.combo_section.setMinimumWidth(155)
        self.combo_section.setStyleSheet(_COMBO_STYLE)
        fl.addWidget(self.combo_section)

        fl.addWidget(self._flabel("Shift"))
        self.combo_shift = QComboBox()
        self.combo_shift.setMinimumHeight(30)
        self.combo_shift.setMinimumWidth(110)
        self.combo_shift.setStyleSheet(_COMBO_STYLE)
        self.combo_shift.addItem("Semua", None)
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
        self.lbl_info_h.setStyleSheet("color: #969696; font-size: 10px;")
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
            "No", "Tanggal", "Shop", "Shift", "Koordinator", "Jml Masalah", "Aksi",
        ])
        self.tabel_harian.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.tabel_harian.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.tabel_harian.horizontalHeader().setSectionResizeMode(6, QHeaderView.Fixed)
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
        self.tabel_harian.setColumnWidth(6, 290)
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
        date_from  = self.date_from.date().toString("yyyy-MM-dd")
        date_to    = self.date_to.date().toString("yyyy-MM-dd")

        self.lbl_info_h.setText("Memuat data...")
        self.tabel_harian.setRowCount(0)

        self._worker = _RiwayatWorker(section_id, shift_name, date_from, date_to)
        self._worker.finished.connect(self._on_harian_loaded)
        self._worker.error.connect(lambda e: self.lbl_info_h.setText(f"Gagal: {e}"))
        self._worker.start()

    def _on_harian_loaded(self, rows: list):
        self._loaded_rows = rows
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
            aksi_w.setStyleSheet("background-color: #252525;")
            al = QHBoxLayout(aksi_w)
            al.setContentsMargins(8, 0, 8, 0)
            al.setSpacing(8)
            al.setAlignment(Qt.AlignVCenter | Qt.AlignCenter)

            btn_lihat = QPushButton("Lihat")
            btn_lihat.setMinimumWidth(52); btn_lihat.setFixedHeight(26)
            btn_lihat.setStyleSheet(
                "QPushButton { background-color: #1a2a3a; color: #4a9fd4;"
                " border: 1px solid #1a4a6a; border-radius: 0px; padding: 0 8px; font-size: 10px; }"
                "QPushButton:hover { background-color: #1e344a; }"
            )
            btn_lihat.clicked.connect(lambda _, rid=report_id: self._lihat(rid))

            btn_edit = QPushButton("Edit")
            btn_edit.setMinimumWidth(44); btn_edit.setFixedHeight(26)
            btn_edit.setStyleSheet(
                "QPushButton { background-color: #2a2a1a; color: #b08800;"
                " border: 1px solid #4a4a1a; border-radius: 0px; padding: 0 8px; font-size: 10px; }"
                "QPushButton:hover { background-color: #34341e; }"
            )
            btn_edit.clicked.connect(lambda _, rid=report_id: self._edit(rid))

            btn_hapus = QPushButton("Hapus")
            btn_hapus.setMinimumWidth(52); btn_hapus.setFixedHeight(26)
            btn_hapus.setStyleSheet(
                "QPushButton { background-color: #2a1a1a; color: #da291c;"
                " border: 1px solid #4a1a1a; border-radius: 0px; padding: 0 8px; font-size: 10px; }"
                "QPushButton:hover { background-color: #341e1e; }"
            )
            btn_hapus.clicked.connect(lambda _, rid=report_id: self._hapus(rid))

            al.addWidget(btn_lihat)
            al.addWidget(btn_edit)
            al.addWidget(btn_hapus)
            self.tabel_harian.setCellWidget(i, 6, aksi_w)
            self.tabel_harian.setRowHeight(i, 40)

    def _reset_filter_harian(self):
        self.combo_section.setCurrentIndex(0)
        self.combo_shift.setCurrentIndex(0)
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        self.date_to.setDate(QDate.currentDate())
        self.load_data_harian()

    def _lihat(self, report_id):
        try:
            header, produksi, catatan, manpower, absen, inhouse_claim, materials = get_detail_laporan(report_id)
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
        dlg.setStyleSheet("QDialog { background-color: #252525; color: #ffffff; }")

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
                "color: #da291c; font-size: 12px; font-weight: bold; padding: 4px 0;"
            )
            return lbl

        # Header info
        hdr_frame = QFrame()
        hdr_frame.setStyleSheet("QFrame { background-color: #2e2e2e; border-radius: 0px; }")
        hdr_lyt = QGridLayout(hdr_frame)
        hdr_lyt.setContentsMargins(14, 10, 14, 10)
        hdr_lyt.setSpacing(6)
        hdr_lyt.setColumnStretch(1, 1)
        hdr_lyt.setColumnStretch(3, 1)

        fmt_w = lambda v: f"{v:.2f} H" if v is not None else "—"
        plan_wh   = sum(p.get("plan_whour", 0) or 0   for p in produksi) if produksi else None
        actual_wh = sum(p.get("actual_whour", 0) or 0 for p in produksi) if produksi else None
        pairs = [
            ("Tanggal",       header.get("date", "")),
            ("Shift",         header.get("shift", "")),
            ("Shop",          header.get("section", "")),
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
            lbl.setStyleSheet("color: #969696; font-size: 11px;")
            val = QLabel(str(val_text))
            val.setStyleSheet("color: #ffffff; font-size: 11px; font-weight: bold;")
            hdr_lyt.addWidget(lbl, r, c * 2)
            hdr_lyt.addWidget(val, r, c * 2 + 1)
        lyt.addWidget(hdr_frame)

        # Data Produksi
        if produksi:
            lyt.addWidget(_sec_lbl("Data Produksi"))
            tbl_prod = QTableWidget()
            tbl_prod.setColumnCount(6)
            tbl_prod.setHorizontalHeaderLabels(
                ["Model", "Plan Qty", "Act Qty", "Plan H", "Act H", "Bal Qty"]
            )
            tbl_prod.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            tbl_prod.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
            tbl_prod.verticalHeader().setVisible(False)
            tbl_prod.setEditTriggers(QAbstractItemView.NoEditTriggers)
            tbl_prod.setFixedHeight(min(len(produksi) * 32 + 32, 160))
            tbl_prod.setStyleSheet(_TABLE_STYLE)
            for i, p in enumerate(produksi):
                tbl_prod.insertRow(i)
                plan_u = p.get("plan_unit", 0.0) or 0.0
                act_u  = p.get("actual_unit", 0.0) or 0.0
                plan_h = p.get("plan_whour", 0.0) or 0.0
                act_h  = p.get("actual_whour", 0.0) or 0.0
                bal    = act_u - plan_u
                tbl_prod.setItem(i, 0, _cell(p.get("model", "")))
                tbl_prod.setItem(i, 1, _cell(f"{plan_u:.0f}", Qt.AlignCenter))
                tbl_prod.setItem(i, 2, _cell(f"{act_u:.0f}", Qt.AlignCenter))
                tbl_prod.setItem(i, 3, _cell(f"{plan_h:.4f}", Qt.AlignCenter))
                tbl_prod.setItem(i, 4, _cell(f"{act_h:.4f}", Qt.AlignCenter))
                bal_cell = _cell(f"{bal:+.0f}", Qt.AlignCenter)
                bal_cell.setForeground(QColor(220, 80, 80) if bal < 0 else QColor(80, 200, 100))
                tbl_prod.setItem(i, 5, bal_cell)
            lyt.addWidget(tbl_prod)

        # Catatan Masalah
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
        row_count = max(len(catatan), 1)
        tbl_cat.setFixedHeight(min(row_count * 32 + 36, 400))
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

        # Manpower
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

        # Absen
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

        # Inhouse Claim
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
            claim_count = max(len(inhouse_claim), 1)
            tbl_ic.setFixedHeight(min(claim_count * 32 + 36, 300))
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

        # Material Used
        if materials:
            lyt.addWidget(_sec_lbl("Material Used"))
            tbl_mat = QTableWidget()
            tbl_mat.setColumnCount(5)
            tbl_mat.setHorizontalHeaderLabels(
                ["Material Name", "Mat. No", "Qty", "Satuan", "Keterangan"]
            )
            tbl_mat.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            for fc in (1, 2, 3):
                tbl_mat.horizontalHeader().setSectionResizeMode(fc, QHeaderView.ResizeToContents)
            tbl_mat.verticalHeader().setVisible(False)
            tbl_mat.setEditTriggers(QAbstractItemView.NoEditTriggers)
            tbl_mat.setFixedHeight(min(len(materials) * 32 + 32, 200))
            tbl_mat.setStyleSheet(_TABLE_STYLE)
            for i, m in enumerate(materials):
                tbl_mat.insertRow(i)
                tbl_mat.setItem(i, 0, _cell(m.get("material_name", "")))
                tbl_mat.setItem(i, 1, _cell(m.get("material_no", ""), Qt.AlignCenter))
                tbl_mat.setItem(i, 2, _cell(f"{m.get('qty', 0):.0f}", Qt.AlignCenter))
                tbl_mat.setItem(i, 3, _cell(m.get("satuan", ""), Qt.AlignCenter))
                tbl_mat.setItem(i, 4, _cell(m.get("keterangan", "")))
            lyt.addWidget(tbl_mat)

        lyt.addStretch()
        scroll.setWidget(container)
        outer_lyt.addWidget(scroll)

        btn_box = QDialogButtonBox(QDialogButtonBox.Close)
        btn_box.setStyleSheet("""
            QPushButton { background-color: #252525; color: #969696;
                border: none; border-radius: 0px; padding: 6px 18px; font-size: 11px; }
            QPushButton:hover { background-color: #303030; color: #ffffff; }
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

    def _export_laporan(self, report_id):
        try:
            header, produksi, catatan, manpower, absen, inhouse_claim, _ = get_detail_laporan(report_id)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Gagal memuat detail: {e}")
            return
        if header is None:
            QMessageBox.warning(self, "Tidak Ditemukan", f"Laporan #{report_id} tidak ditemukan.")
            return
        try:
            filepath = export_loss_time_record(header, produksi, catatan, manpower, absen, inhouse_claim)
            QMessageBox.information(self, "Export Berhasil", f"File disimpan di:\n{filepath}")
        except Exception as e:
            QMessageBox.critical(self, "Gagal Export", f"Gagal mengekspor laporan: {e}")

    def _export_rah(self):
        if self.combo_section.currentData() is None:
            QMessageBox.warning(self, "Peringatan", "Pilih Shop terlebih dahulu sebelum export.")
            return
        if self.tabel_harian.rowCount() == 0:
            QMessageBox.warning(self, "Peringatan", "Tidak ada data untuk diekspor.")
            return

        all_catatan  = []
        all_manpower = []
        section_name = ""
        shift_name   = ""
        coordinator  = ""

        try:
            for row in getattr(self, "_loaded_rows", []):
                _, _, catatan, manpower, _, _, _ = get_detail_laporan(row["id"])
                all_catatan.extend(catatan)
                all_manpower.extend(manpower)
                if not section_name:
                    section_name = row.get("section", "")
                if not shift_name:
                    shift_name = row.get("shift", "")
                if not coordinator:
                    coordinator = row.get("coordinator", "")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Gagal memuat detail laporan: {e}")
            return

        header_info = {
            "date":        self.date_from.date().toString("yyyy-MM-dd"),
            "section":     section_name,
            "shift":       shift_name,
            "coordinator": coordinator,
            "approved_by": "",
            "checked_by":  "",
        }

        if not all_catatan:
            QMessageBox.warning(self, "Peringatan", "Tidak ada catatan masalah untuk diekspor.")
            return

        try:
            from modules.export_excel import export_loss_time_record
            filepath = export_loss_time_record(
                header=header_info,
                catatan=all_catatan,
                produksi=[],
                manpower=all_manpower,
                absen=[],
                inhouse_claim=[],
            )
            QMessageBox.information(self, "Export Berhasil", f"File disimpan di:\n{filepath}")
        except Exception as e:
            QMessageBox.critical(self, "Gagal Export", f"Gagal mengekspor: {e}")

    # Tab 2: Rekap Bulanan

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

        fl.addWidget(self._flabel("Shop"))
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
        for i, name in enumerate([
            "Januari", "Februari", "Maret", "April", "Mei", "Juni",
            "Juli", "Agustus", "September", "Oktober", "November", "Desember",
        ], 1):
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

        fl.addWidget(self._flabel("Factor"))
        self.combo_factor = QComboBox()
        self.combo_factor.setMinimumHeight(30)
        self.combo_factor.setMinimumWidth(140)
        self.combo_factor.setStyleSheet(_COMBO_STYLE)
        self.combo_factor.addItem("Semua")
        try:
            for name in get_all_category_names():
                self.combo_factor.addItem(name)
        except Exception:
            pass
        fl.addWidget(self.combo_factor)

        fl.addStretch()

        btn_tampil = QPushButton("Tampilkan")
        btn_tampil.setMinimumSize(90, 32)
        btn_tampil.setStyleSheet(_BTN_CARI)
        btn_tampil.clicked.connect(self.load_rekap_bulanan)
        fl.addWidget(btn_tampil)

        btn_export_r = QPushButton("Export Excel")
        btn_export_r.setMinimumSize(100, 32)
        btn_export_r.setStyleSheet(_BTN_EXPORT)
        btn_export_r.clicked.connect(self._export_rekap)
        fl.addWidget(btn_export_r)

        main.addWidget(card_f)

        # Table card
        card_t = QFrame()
        card_t.setStyleSheet(_CARD_STYLE)
        tl = QVBoxLayout(card_t)
        tl.setContentsMargins(16, 16, 16, 16)
        tl.setSpacing(8)

        self.lbl_info_r = QLabel("Pilih filter dan klik Tampilkan.")
        self.lbl_info_r.setStyleSheet("color: #969696; font-size: 10px;")
        tl.addWidget(self.lbl_info_r)

        self.tabel_rekap = QTableWidget()
        self.tabel_rekap.setColumnCount(9)
        self.tabel_rekap.setHorizontalHeaderLabels([
            "No", "Date", "OPNo/St", "Problem/Masalah", "Cause/Penyebab",
            "Action/Perbaikan", "Factor", "Lost (H)", "Stop (H)",
        ])
        hh = self.tabel_rekap.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.Interactive)
        for col in (3, 4, 5):
            hh.setSectionResizeMode(col, QHeaderView.Stretch)
        for col in (6, 7, 8):
            hh.setSectionResizeMode(col, QHeaderView.Fixed)
        self.tabel_rekap.verticalHeader().setVisible(False)
        self.tabel_rekap.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabel_rekap.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabel_rekap.setStyleSheet(_TABLE_STYLE)
        self.tabel_rekap.setMinimumHeight(400)
        self.tabel_rekap.setColumnWidth(0, 40)
        self.tabel_rekap.setColumnWidth(1, 92)
        self.tabel_rekap.setColumnWidth(2, 80)
        self.tabel_rekap.setColumnWidth(6, 110)
        self.tabel_rekap.setColumnWidth(7, 80)
        self.tabel_rekap.setColumnWidth(8, 80)
        tl.addWidget(self.tabel_rekap)

        # Summary bar
        sum_frame = QFrame()
        sum_frame.setStyleSheet("QFrame { background-color: #2e2e2e; border-radius: 0px; }")
        sum_lyt = QHBoxLayout(sum_frame)
        sum_lyt.setContentsMargins(16, 10, 16, 10)
        sum_lyt.setSpacing(30)

        self.lbl_total_hour = QLabel("Total Working Hour: —")
        self.lbl_total_hour.setStyleSheet("color: #ffffff; font-size: 12px; font-weight: bold;")
        self.lbl_total_lost = QLabel("Total Lost: —")
        self.lbl_total_lost.setStyleSheet("color: #ffffff; font-size: 12px; font-weight: bold;")
        self.lbl_ratio = QLabel("Ratio Loss: —")
        self.lbl_ratio.setStyleSheet("color: #969696; font-size: 12px; font-weight: bold;")
        sum_lyt.addWidget(self.lbl_total_hour)
        sum_lyt.addWidget(self.lbl_total_lost)
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
        bulan      = self.combo_bulan.currentData()
        factor     = self.combo_factor.currentText()
        try:
            tahun = int(self.input_tahun.text().strip())
        except ValueError:
            QMessageBox.warning(self, "Peringatan", "Tahun tidak valid.")
            return

        try:
            rows, total_hour = _db_display_line_stop(section_id, bulan, tahun, factor)
        except Exception as e:
            self.lbl_info_r.setText(f"Gagal memuat data: {e}")
            self.tabel_rekap.setRowCount(0)
            return

        total_lost = sum(float(r[6]) for r in rows)
        ratio_loss = (total_lost / total_hour * 100) if total_hour > 0 else 0.0

        self.tabel_rekap.setRowCount(0)
        self.lbl_info_r.setText(
            f"{len(rows)} catatan — {self.combo_bulan.currentText()} {tahun}"
        )

        def _it(text, align=Qt.AlignLeft | Qt.AlignVCenter):
            it = QTableWidgetItem(str(text) if text is not None else "")
            it.setTextAlignment(align)
            return it

        for i, r in enumerate(rows):
            self.tabel_rekap.insertRow(i)
            self.tabel_rekap.setItem(i, 0, _it(i + 1, Qt.AlignCenter))
            self.tabel_rekap.setItem(i, 1, _it(str(r[0]) if r[0] else "", Qt.AlignCenter))
            self.tabel_rekap.setItem(i, 2, _it(r[1] or ""))
            self.tabel_rekap.setItem(i, 3, _it(r[2] or ""))
            self.tabel_rekap.setItem(i, 4, _it(r[3] or ""))
            self.tabel_rekap.setItem(i, 5, _it(r[4] or ""))
            self.tabel_rekap.setItem(i, 6, _it(r[5] or ""))
            self.tabel_rekap.setItem(i, 7, _it(f"{float(r[6]):.2f}", Qt.AlignCenter))
            self.tabel_rekap.setItem(i, 8, _it(f"{float(r[7]):.2f}", Qt.AlignCenter))
            self.tabel_rekap.setRowHeight(i, 32)

        self.lbl_total_hour.setText(f"Total Working Hour: {total_hour:.2f} H")
        self.lbl_total_lost.setText(f"Total Lost: {total_lost:.2f} H")
        ratio_color = "#27ae60" if ratio_loss < 20 else "#f39c12" if ratio_loss < 40 else "#da291c"
        self.lbl_ratio.setText(f"Ratio Loss: {ratio_loss:.2f}%")
        self.lbl_ratio.setStyleSheet(
            f"color: {ratio_color}; font-size: 12px; font-weight: bold;"
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
        ws.title = "Display Line Stop"

        thin = Side(style="thin", color="3C4147")
        border = Border(left=thin, right=thin, top=thin, bottom=thin)
        hdr_fill = PatternFill("solid", fgColor="1C2028")

        col_headers = [
            "No", "Date", "OPNo/St", "Problem/Masalah",
            "Cause/Penyebab", "Action/Perbaikan", "Factor", "Lost (H)", "Stop (H)",
        ]
        center_cols = {0, 1, 6, 7, 8}
        for ci, h in enumerate(col_headers, 1):
            cell = ws.cell(row=1, column=ci, value=h)
            cell.fill = hdr_fill
            cell.font = Font(color="9696A0", bold=True, size=10)
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = border

        for ri in range(row_count):
            for ci in range(9):
                item = self.tabel_rekap.item(ri, ci)
                val = item.text() if item else ""
                cell = ws.cell(row=ri + 2, column=ci + 1, value=val)
                cell.alignment = Alignment(
                    horizontal="center" if ci in center_cols else "left",
                    vertical="center",
                )
                cell.border = border

        sum_row = row_count + 3
        for col_offset, lbl in enumerate([self.lbl_total_hour, self.lbl_total_lost, self.lbl_ratio]):
            ws.cell(row=sum_row, column=col_offset + 1, value=lbl.text()).font = Font(
                bold=True, color="C8C8C8"
            )

        for ci, w in enumerate([6, 12, 10, 30, 30, 30, 16, 10, 10], 1):
            ws.column_dimensions[openpyxl.utils.get_column_letter(ci)].width = w
        ws.row_dimensions[1].height = 20

        downloads = os.path.join(os.path.expanduser("~"), "Downloads")
        filepath = os.path.join(
            downloads, f"display_line_stop_{QDate.currentDate().toString('yyyyMMdd')}.xlsx"
        )
        try:
            wb.save(filepath)
            QMessageBox.information(self, "Export Berhasil", f"File disimpan di:\n{filepath}")
        except Exception as e:
            QMessageBox.critical(self, "Gagal Export", f"Gagal menyimpan file:\n{e}")

    # Tab 3: NG & Pending

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

        fl.addWidget(self._flabel("Shop"))
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
        lbl_ic.setStyleSheet(
            "color: #ffffff; font-size: 12px; font-weight: bold;"
            " border-left: 3px solid #da291c; padding-left: 8px;"
        )
        self.lbl_info_ic = QLabel("")
        self.lbl_info_ic.setStyleSheet("color: #969696; font-size: 10px;")
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
        lbl_pp.setStyleSheet(
            "color: #ffffff; font-size: 12px; font-weight: bold;"
            " border-left: 3px solid #da291c; padding-left: 8px;"
        )
        self.lbl_info_pp = QLabel("")
        self.lbl_info_pp.setStyleSheet("color: #969696; font-size: 10px;")
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
        ic_count = self.tabel_ic.rowCount()
        pp_count = self.tabel_pp.rowCount()
        if ic_count == 0 and pp_count == 0:
            QMessageBox.warning(self, "Peringatan", "Tidak ada data untuk diekspor.")
            return

        # Section name
        sec_text     = self.combo_section_ng.currentText()
        section_name = sec_text if sec_text != "Semua" else ""

        # Period string
        d_from = self.date_ng_from.date()
        d_to   = self.date_ng_to.date()
        _bln   = ["JAN", "FEB", "MAR", "APR", "MEI", "JUN",
                  "JUL", "AGU", "SEP", "OKT", "NOV", "DES"]
        if d_from.month() == d_to.month() and d_from.year() == d_to.year():
            period_str = f"{_bln[d_from.month() - 1]} {d_from.year()}"
        else:
            period_str = (
                f"{d_from.toString('dd/MM/yy')} - {d_to.toString('dd/MM/yy')}"
            )

        # Extract table data 
        def _read_table(tbl, ncols):
            """
            Baca ncols kolom dari QTableWidget.
            Sisipkan kolom Satuan (kosong) setelah Qty (index 5 → insert at 6).
            """
            rows = []
            for r in range(tbl.rowCount()):
                row = [
                    (tbl.item(r, c).text() if tbl.item(r, c) else "")
                    for c in range(ncols)
                ]
                row.insert(6, "")   # Satuan
                rows.append(row)
            return rows

        ng_rows      = _read_table(self.tabel_ic, 12)   # 12 cols → 13 setelah insert
        pending_rows = _read_table(self.tabel_pp, 11)   # 11 cols → 12 setelah insert

        try:
            filepath = export_inhouse_ng_pending(
                ng_rows, pending_rows, section_name, period_str
            )
            QMessageBox.information(self, "Export Berhasil", f"File disimpan di:\n{filepath}")
        except Exception as e:
            QMessageBox.critical(self, "Gagal Export", f"Gagal mengekspor: {e}")

    # Tab 4: Produktivitas Bulanan

    def _build_tab_produktivitas(self):
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
        card_f = QFrame(); card_f.setStyleSheet(_CARD_STYLE)
        fl = QHBoxLayout(card_f); fl.setContentsMargins(16, 12, 16, 12); fl.setSpacing(10)

        fl.addWidget(self._flabel("Shop"))
        self.combo_prod_section = QComboBox()
        self.combo_prod_section.setMinimumHeight(30)
        self.combo_prod_section.setMinimumWidth(155)
        self.combo_prod_section.setStyleSheet(_COMBO_STYLE)
        self.combo_prod_section.addItem("Semua", None)
        fl.addWidget(self.combo_prod_section)

        fl.addWidget(self._flabel("Bulan"))
        self.combo_prod_bulan = QComboBox()
        self.combo_prod_bulan.setMinimumHeight(30)
        self.combo_prod_bulan.setMinimumWidth(115)
        self.combo_prod_bulan.setStyleSheet(_COMBO_STYLE)
        for i, name in enumerate(
            ["Januari","Februari","Maret","April","Mei","Juni",
             "Juli","Agustus","September","Oktober","November","Desember"], 1
        ):
            self.combo_prod_bulan.addItem(name, i)
        self.combo_prod_bulan.setCurrentIndex(QDate.currentDate().month() - 1)
        fl.addWidget(self.combo_prod_bulan)

        fl.addWidget(self._flabel("Tahun"))
        self.input_prod_tahun = QLineEdit()
        self.input_prod_tahun.setMinimumHeight(30)
        self.input_prod_tahun.setFixedWidth(70)
        self.input_prod_tahun.setStyleSheet(_INPUT_STYLE)
        self.input_prod_tahun.setText(str(QDate.currentDate().year()))
        fl.addWidget(self.input_prod_tahun)

        fl.addStretch()
        btn_tampil = QPushButton("Tampilkan")
        btn_tampil.setMinimumSize(90, 32)
        btn_tampil.setStyleSheet(_BTN_CARI)
        btn_tampil.clicked.connect(self.load_produktivitas)
        fl.addWidget(btn_tampil)
        main.addWidget(card_f)

        # Content row
        content = QHBoxLayout(); content.setSpacing(12)

        # Left: breakdown table
        card_left = QFrame(); card_left.setStyleSheet(_CARD_STYLE)
        ll = QVBoxLayout(card_left); ll.setContentsMargins(16, 14, 16, 16); ll.setSpacing(8)
        lbl_bkdn = QLabel("Breakdown Jam Kerja")
        lbl_bkdn.setStyleSheet(
            "color: #ffffff; font-size: 12px; font-weight: bold;"
            " border-left: 3px solid #da291c; padding-left: 8px;"
        )
        ll.addWidget(lbl_bkdn)

        self.tabel_prod_bkdn = QTableWidget()
        self.tabel_prod_bkdn.setColumnCount(2)
        self.tabel_prod_bkdn.setHorizontalHeaderLabels(["Kategori", "Jam (H)"])
        self.tabel_prod_bkdn.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tabel_prod_bkdn.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.tabel_prod_bkdn.setColumnWidth(1, 90)
        self.tabel_prod_bkdn.verticalHeader().setVisible(False)
        self.tabel_prod_bkdn.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabel_prod_bkdn.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabel_prod_bkdn.setMinimumHeight(300)
        self.tabel_prod_bkdn.setStyleSheet(_TABLE_STYLE)
        ll.addWidget(self.tabel_prod_bkdn)
        content.addWidget(card_left, 3)

        # Right: ratio + summary
        card_right = QFrame(); card_right.setStyleSheet(_CARD_STYLE)
        rl = QVBoxLayout(card_right); rl.setContentsMargins(16, 14, 16, 16); rl.setSpacing(12)

        lbl_rt = QLabel("Ratio Produktivitas")
        lbl_rt.setStyleSheet("color: #969696; font-size: 11px; font-weight: bold;")
        lbl_rt.setAlignment(Qt.AlignCenter)
        rl.addWidget(lbl_rt)

        ratio_frame = QFrame()
        ratio_frame.setObjectName("ratioFrame")
        ratio_frame.setStyleSheet(
            "#ratioFrame { background-color: #1e1e1e; border: 2px solid #303030; }"
        )
        rfl = QVBoxLayout(ratio_frame); rfl.setContentsMargins(16, 24, 16, 24)
        self._lbl_ratio_big = QLabel("—")
        self._lbl_ratio_big.setStyleSheet(
            "color: #27ae60; font-size: 40px; font-weight: bold;"
        )
        self._lbl_ratio_big.setAlignment(Qt.AlignCenter)
        rfl.addWidget(self._lbl_ratio_big)
        rl.addWidget(ratio_frame)

        sum_frame = QFrame()
        sum_frame.setStyleSheet(
            "QFrame { background-color: #1e1e1e; border: 1px solid #303030; }"
        )
        sg = QGridLayout(sum_frame); sg.setContentsMargins(12, 10, 12, 10); sg.setSpacing(6)
        sg.setColumnStretch(1, 1)

        def _srow(row, label, attr):
            l = QLabel(label); l.setStyleSheet("color: #969696; font-size: 11px;")
            v = QLabel("—")
            v.setStyleSheet("color: #ffffff; font-size: 11px; font-weight: bold;")
            v.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            sg.addWidget(l, row, 0); sg.addWidget(v, row, 1)
            setattr(self, attr, v)

        _srow(0, "Total Hour",   "_lbl_prod_total")
        _srow(1, "Loss Time",    "_lbl_prod_bal")
        _srow(2, "Laporan",      "_lbl_prod_count")
        rl.addWidget(sum_frame)
        rl.addStretch()
        content.addWidget(card_right, 2)

        main.addLayout(content)
        main.addStretch()
        scroll.setWidget(container)
        outer.addWidget(scroll)
        return tab

    def load_produktivitas(self):
        section_id = self.combo_prod_section.currentData()
        bulan = self.combo_prod_bulan.currentData()
        try:
            tahun = int(self.input_prod_tahun.text().strip())
        except ValueError:
            QMessageBox.warning(self, "Peringatan", "Tahun tidak valid.")
            return

        try:
            data = get_monthly_productivity(section_id, bulan, tahun)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Gagal memuat data: {e}")
            return

        tbl = self.tabel_prod_bkdn
        tbl.setRowCount(0)

        loss_hour  = sum(c["hours"] for c in data["categories"])
        total_hour = data["total_hour"]

        def _grp_row(text):
            r = tbl.rowCount()
            tbl.insertRow(r)
            it = QTableWidgetItem(text)
            it.setFlags(Qt.ItemIsEnabled)
            it.setBackground(QColor("#111111"))
            it.setForeground(QColor("#da291c"))
            f = it.font(); f.setBold(True); it.setFont(f)
            tbl.setItem(r, 0, it)
            it2 = QTableWidgetItem("")
            it2.setFlags(Qt.ItemIsEnabled)
            it2.setBackground(QColor("#111111"))
            tbl.setItem(r, 1, it2)
            tbl.setRowHeight(r, 26)

        def _subgrp_row(text):
            r = tbl.rowCount()
            tbl.insertRow(r)
            it = QTableWidgetItem(f"  {text}")
            it.setFlags(Qt.ItemIsEnabled)
            it.setForeground(QColor("#606060"))
            f = it.font(); f.setItalic(True); it.setFont(f)
            tbl.setItem(r, 0, it)
            it2 = QTableWidgetItem("")
            it2.setFlags(Qt.ItemIsEnabled)
            tbl.setItem(r, 1, it2)
            tbl.setRowHeight(r, 20)

        def _data_row(name, hours, fg=None):
            r = tbl.rowCount()
            tbl.insertRow(r)
            it_n = QTableWidgetItem(f"    {name}")
            it_n.setFlags(Qt.ItemIsEnabled)
            it_h = QTableWidgetItem(f"{hours:.4f}")
            it_h.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            it_h.setFlags(Qt.ItemIsEnabled)
            if fg:
                it_n.setForeground(QColor(fg))
                it_h.setForeground(QColor(fg))
            tbl.setItem(r, 0, it_n)
            tbl.setItem(r, 1, it_h)
            tbl.setRowHeight(r, 28)

        # Produktif 
        _grp_row("PRODUKTIF")
        _data_row("Process", data["process_hour"], "#80c880")

        # Non-Produktif (line stop by category/group)

        groups: dict[str, list] = {}
        for cat in data["categories"]:
            groups.setdefault(cat["group"], []).append(cat)

        if groups:
            _grp_row("NON-PRODUKTIF (Line Stop)")
            for grp_name, cats in groups.items():
                _subgrp_row(grp_name)
                for cat in cats:
                    _data_row(cat["name"], cat["hours"])

        # Waktu Tetap 
        _grp_row("WAKTU TETAP")
        _data_row("Preparation", data["prep_hour"])
        _data_row("Sholat",      data["sholat_hour"])

        # Ketidakhadiran
        _grp_row("KETIDAKHADIRAN")
        _data_row("Absence", data["absence_hour"])

        # Divider + TOTAL
        r = tbl.rowCount()
        tbl.insertRow(r)
        for c in range(2):
            it = QTableWidgetItem()
            it.setFlags(Qt.ItemIsEnabled)
            it.setBackground(QColor("#404040"))
            tbl.setItem(r, c, it)
        tbl.setRowHeight(r, 2)

        r = tbl.rowCount()
        tbl.insertRow(r)
        it_n = QTableWidgetItem("TOTAL")
        it_n.setFlags(Qt.ItemIsEnabled)
        fn = it_n.font(); fn.setBold(True); it_n.setFont(fn)
        it_n.setForeground(QColor("#ffffff"))
        it_h = QTableWidgetItem(f"{total_hour:.4f}")
        it_h.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        it_h.setFlags(Qt.ItemIsEnabled)
        fh = it_h.font(); fh.setBold(True); it_h.setFont(fh)
        it_h.setForeground(QColor("#ffffff"))
        tbl.setItem(r, 0, it_n)
        tbl.setItem(r, 1, it_h)
        tbl.setRowHeight(r, 30)

        # Summary
        balance = loss_hour

        ratio = (data["process_hour"] / total_hour * 100) if total_hour > 0 else 0.0
        ratio_color = (
            "#27ae60" if ratio >= 80
            else "#f39c12" if ratio >= 60
            else "#da291c"
        )
        self._lbl_ratio_big.setText(f"{ratio:.1f}%")
        self._lbl_ratio_big.setStyleSheet(
            f"color: {ratio_color}; font-size: 40px; font-weight: bold;"
        )
        self._lbl_prod_total.setText(f"{total_hour:.2f} H")

        bal_color = "#27ae60" if balance < 0.01 else "#da291c"
        self._lbl_prod_bal.setText(f"{balance:.4f}")
        self._lbl_prod_bal.setStyleSheet(
            f"color: {bal_color}; font-size: 11px; font-weight: bold;"
        )
        self._lbl_prod_count.setText(f"{data['report_count']} laporan")

    @staticmethod
    def _flabel(text):
        lbl = QLabel(text)
        lbl.setStyleSheet("color: #969696; font-size: 11px;")
        return lbl

    # Tab 5: Volume Produksi

    def _build_tab_volume(self):
        tab = QWidget()
        tab.setStyleSheet("background: transparent;")
        outer = QVBoxLayout(tab)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll_v = QScrollArea()
        scroll_v.setWidgetResizable(True)
        scroll_v.setStyleSheet("QScrollArea { border: none; background: transparent; }")
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

        fl.addWidget(self._flabel("Shop"))
        self.combo_vol_section = QComboBox()
        self.combo_vol_section.setMinimumHeight(30)
        self.combo_vol_section.setMinimumWidth(155)
        self.combo_vol_section.setStyleSheet(_COMBO_STYLE)
        fl.addWidget(self.combo_vol_section)

        fl.addWidget(self._flabel("Bulan"))
        self.combo_vol_bulan = QComboBox()
        self.combo_vol_bulan.setMinimumHeight(30)
        self.combo_vol_bulan.setMinimumWidth(115)
        self.combo_vol_bulan.setStyleSheet(_COMBO_STYLE)
        for i, name in enumerate([
            "Januari", "Februari", "Maret", "April", "Mei", "Juni",
            "Juli", "Agustus", "September", "Oktober", "November", "Desember",
        ], 1):
            self.combo_vol_bulan.addItem(name, i)
        self.combo_vol_bulan.setCurrentIndex(QDate.currentDate().month() - 1)
        fl.addWidget(self.combo_vol_bulan)

        fl.addWidget(self._flabel("Tahun"))
        self.input_vol_tahun = QLineEdit()
        self.input_vol_tahun.setMinimumHeight(30)
        self.input_vol_tahun.setFixedWidth(70)
        self.input_vol_tahun.setStyleSheet(_INPUT_STYLE)
        self.input_vol_tahun.setText(str(QDate.currentDate().year()))
        fl.addWidget(self.input_vol_tahun)

        fl.addStretch()
        btn_tampil = QPushButton("Tampilkan")
        btn_tampil.setMinimumSize(90, 32)
        btn_tampil.setStyleSheet(_BTN_CARI)
        btn_tampil.clicked.connect(self.load_volume_produksi)
        fl.addWidget(btn_tampil)
        main.addWidget(card_f)

        # Table card with horizontal scroll
        card_t = QFrame()
        card_t.setStyleSheet(_CARD_STYLE)
        tl = QVBoxLayout(card_t)
        tl.setContentsMargins(16, 16, 16, 16)
        tl.setSpacing(8)

        self.lbl_info_vol = QLabel("Pilih Shop dan klik Tampilkan.")
        self.lbl_info_vol.setStyleSheet("color: #969696; font-size: 10px;")
        tl.addWidget(self.lbl_info_vol)

        scroll_h = QScrollArea()
        scroll_h.setWidgetResizable(True)
        scroll_h.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_h.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_h.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.tabel_volume = QTableWidget()
        self.tabel_volume.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabel_volume.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabel_volume.verticalHeader().setVisible(False)
        self.tabel_volume.setStyleSheet(_TABLE_STYLE)
        self.tabel_volume.horizontalHeader().setDefaultSectionSize(28)
        self.tabel_volume.horizontalHeader().setMinimumSectionSize(20)
        self.tabel_volume.setMinimumHeight(300)

        scroll_h.setWidget(self.tabel_volume)
        tl.addWidget(scroll_h)
        main.addWidget(card_t)
        main.addStretch()
        scroll_v.setWidget(container)
        outer.addWidget(scroll_v)
        return tab

    def load_volume_produksi(self):
        section_id = self.combo_vol_section.currentData()
        if section_id is None:
            QMessageBox.warning(self, "Peringatan", "Pilih Shop terlebih dahulu.")
            return
        bulan = self.combo_vol_bulan.currentData()
        try:
            tahun = int(self.input_vol_tahun.text().strip())
        except ValueError:
            return

        try:
            result = get_production_volume(section_id, bulan, tahun)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Gagal memuat data: {e}")
            return

        tbl  = self.tabel_volume
        days = result["days"]

        tbl.setColumnCount(2 + days + 1)
        headers = ["Model", "Shift"] + [str(d) for d in range(1, days + 1)] + ["TOTAL"]
        tbl.setHorizontalHeaderLabels(headers)

        hh = tbl.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.Stretch)
        hh.setSectionResizeMode(0, QHeaderView.Fixed)
        hh.setSectionResizeMode(1, QHeaderView.Fixed)
        hh.setSectionResizeMode(2 + days, QHeaderView.Fixed)

        tbl.setColumnWidth(0, 100)
        tbl.setColumnWidth(1, 90)
        tbl.setColumnWidth(2 + days, 70)

        tbl.setRowCount(0)

        row_idx = 0
        for model in result["models"]:
            for shift in result["shifts"]:
                tbl.insertRow(row_idx)
                tbl.setRowHeight(row_idx, 26)

                tbl.setItem(row_idx, 0, _vol_item(model, bold=(shift == result["shifts"][0])))
                tbl.setItem(row_idx, 1, _vol_item(shift, center=True))

                key      = (model, shift)
                day_data = result["data"].get(key, {})
                for d in range(1, days + 1):
                    val = day_data.get(d)
                    it  = QTableWidgetItem(str(val) if val else "")
                    it.setTextAlignment(Qt.AlignCenter)
                    it.setFlags(Qt.ItemIsEnabled)
                    if val:
                        it.setBackground(QColor("#222222"))
                    else:
                        it.setBackground(QColor("#1a1a1a"))
                        it.setForeground(QColor("#2e2e2e"))
                    tbl.setItem(row_idx, d + 1, it)

                total    = result["totals"].get(key, 0)
                it_total = QTableWidgetItem(str(total) if total else "")
                it_total.setTextAlignment(Qt.AlignCenter)
                it_total.setFlags(Qt.ItemIsEnabled)
                it_total.setForeground(QColor("#da291c"))
                fn = it_total.font(); fn.setBold(True); it_total.setFont(fn)
                tbl.setItem(row_idx, 2 + days, it_total)

                row_idx += 1

        bulan_nama = self.combo_vol_bulan.currentText()
        self.lbl_info_vol.setText(
            f"{row_idx} baris — {bulan_nama} {tahun} | {self.combo_vol_section.currentText()}"
        )


# Module-level helpers

def _vol_item(text: str, bold: bool = False, center: bool = False) -> QTableWidgetItem:
    it = QTableWidgetItem(text)
    it.setTextAlignment(Qt.AlignCenter if center else Qt.AlignLeft | Qt.AlignVCenter)
    it.setFlags(Qt.ItemIsEnabled)
    if bold:
        f = it.font(); f.setBold(True); it.setFont(f)
    return it

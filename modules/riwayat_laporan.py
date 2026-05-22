import os

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QComboBox, QPushButton, QDateEdit,
    QScrollArea, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QDialog, QDialogButtonBox, QAbstractItemView,
    QSizePolicy,
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor

from modules.db_laporan import (
    get_all_sections, get_riwayat_laporan,
    get_detail_laporan, hapus_laporan,
)


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
        subcontrol-origin: padding;
        subcontrol-position: top right;
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
        background-color: rgb(33, 37, 43);
        color: rgb(220, 220, 220);
        selection-background-color: rgb(60, 65, 75);
        border: 1px solid rgb(60, 65, 75);
    }
"""

_TABLE_STYLE = """
    QTableWidget {
        background-color: rgb(33, 37, 43);
        border: 1px solid rgb(60, 65, 75);
        border-radius: 5px;
        gridline-color: rgb(55, 60, 70);
    }
    QTableWidget::item {
        color: rgb(230, 230, 230);
        padding: 4px 8px;
        background-color: rgb(38, 42, 50);
        border-bottom: 1px solid rgb(55, 60, 70);
    }
    QTableWidget::item:selected {
        background-color: rgb(100, 110, 125);
        color: white;
    }
    QHeaderView::section {
        background-color: rgb(28, 32, 40);
        color: rgb(150, 150, 150);
        border: none;
        border-bottom: 1px solid rgb(60, 65, 75);
        border-right: 1px solid rgb(60, 65, 75);
        padding: 6px;
        font-weight: bold;
        font-size: 10px;
    }
"""


class RiwayatLaporanWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._sections_loaded = False
        self._setup_ui()

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        main = QVBoxLayout(container)
        main.setContentsMargins(15, 15, 15, 15)
        main.setSpacing(12)

        title = QLabel("Riwayat Laporan Harian")
        title.setStyleSheet("color: #ffffff; font-size: 16px; font-weight: bold;")
        main.addWidget(title)

        # Filter bar
        card_filter = QFrame()
        card_filter.setStyleSheet(
            "QFrame { background-color: rgb(40, 44, 52); border-radius: 10px; }"
        )
        fl = QHBoxLayout(card_filter)
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
        btn_cari.setStyleSheet("""
            QPushButton {
                background-color: rgb(100, 60, 160); color: rgb(220, 200, 255);
                border: none; border-radius: 5px; font-size: 11px; padding: 0 12px;
            }
            QPushButton:hover { background-color: rgb(120, 75, 185); }
        """)
        btn_cari.clicked.connect(self.load_data)
        fl.addWidget(btn_cari)

        btn_reset = QPushButton("Reset Filter")
        btn_reset.setMinimumSize(88, 32)
        btn_reset.setStyleSheet("""
            QPushButton {
                background-color: rgb(60, 65, 75); color: rgb(200, 200, 200);
                border: none; border-radius: 5px; font-size: 11px; padding: 0 12px;
            }
            QPushButton:hover { background-color: rgb(75, 80, 90); }
        """)
        btn_reset.clicked.connect(self._reset_filter)
        fl.addWidget(btn_reset)

        btn_export = QPushButton("Export Excel")
        btn_export.setMinimumSize(100, 32)
        btn_export.setStyleSheet("""
            QPushButton {
                background-color: rgb(25, 90, 50); color: rgb(130, 220, 140);
                border: none; border-radius: 5px; font-size: 11px; padding: 0 12px;
            }
            QPushButton:hover { background-color: rgb(35, 110, 65); }
        """)
        btn_export.clicked.connect(self._export_excel)
        fl.addWidget(btn_export)

        main.addWidget(card_filter)

        # Table card
        card_table = QFrame()
        card_table.setStyleSheet(
            "QFrame { background-color: rgb(40, 44, 52); border-radius: 10px; }"
        )
        tl = QVBoxLayout(card_table)
        tl.setContentsMargins(16, 16, 16, 16)
        tl.setSpacing(8)

        self.lbl_info = QLabel("Memuat data...")
        self.lbl_info.setStyleSheet("color: rgb(130, 140, 165); font-size: 10px;")
        tl.addWidget(self.lbl_info)

        self.tabel = QTableWidget()
        self.tabel.setColumnCount(8)
        self.tabel.setHorizontalHeaderLabels([
            "No", "Tanggal", "Section", "Shift",
            "Koordinator", "Jml Masalah", "Status", "Aksi",
        ])
        self.tabel.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.tabel.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.tabel.horizontalHeader().setStretchLastSection(False)
        self.tabel.verticalHeader().setVisible(False)
        self.tabel.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabel.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabel.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tabel.setStyleSheet(_TABLE_STYLE)
        self.tabel.setColumnWidth(0, 40)
        self.tabel.setColumnWidth(1, 90)
        self.tabel.setColumnWidth(3, 90)
        self.tabel.setColumnWidth(4, 130)
        self.tabel.setColumnWidth(5, 85)
        self.tabel.setColumnWidth(6, 75)
        self.tabel.setColumnWidth(7, 180)
        tl.addWidget(self.tabel)

        main.addWidget(card_table)
        main.addStretch()

        scroll.setWidget(container)
        outer.addWidget(scroll)

    def showEvent(self, event):
        super().showEvent(event)
        self._load_sections_once()
        self.load_data()

    def _load_sections_once(self):
        if self._sections_loaded:
            return
        try:
            sections = get_all_sections()
            self.combo_section.blockSignals(True)
            for sid, sname in sections:
                self.combo_section.addItem(sname, sid)
            self.combo_section.blockSignals(False)
            self._sections_loaded = True
        except Exception:
            pass

    def load_data(self):
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
            self.lbl_info.setText(f"Gagal memuat data: {e}")
            self.tabel.setRowCount(0)
            return

        self.tabel.setRowCount(0)
        self.lbl_info.setText(f"{len(rows)} data ditemukan")

        for i, row in enumerate(rows):
            self.tabel.insertRow(i)

            def _item(text, align=Qt.AlignCenter):
                it = QTableWidgetItem(str(text) if text is not None else "")
                it.setTextAlignment(align)
                return it

            self.tabel.setItem(i, 0, _item(i + 1))
            self.tabel.setItem(i, 1, _item(row["date"]))
            self.tabel.setItem(i, 2, _item(row["section"], Qt.AlignLeft | Qt.AlignVCenter))
            self.tabel.setItem(i, 3, _item(row["shift"]))
            self.tabel.setItem(i, 4, _item(row["coordinator"], Qt.AlignLeft | Qt.AlignVCenter))
            self.tabel.setItem(i, 5, _item(str(row["jml_masalah"])))

            it_status = _item(row["status"])
            if row["status"] == "draft":
                it_status.setForeground(QColor(210, 170, 60))
            elif row["status"] == "submitted":
                it_status.setForeground(QColor(80, 200, 100))
            self.tabel.setItem(i, 6, it_status)

            report_id = row["id"]
            aksi = QWidget()
            aksi.setStyleSheet("background-color: rgb(38, 42, 50);")
            al = QHBoxLayout(aksi)
            al.setContentsMargins(4, 3, 4, 3)
            al.setSpacing(4)

            btn_lihat = QPushButton("Lihat")
            btn_lihat.setFixedSize(52, 26)
            btn_lihat.setStyleSheet("""
                QPushButton {
                    background-color: rgb(40, 75, 140); color: rgb(140, 185, 255);
                    border: none; border-radius: 4px; font-size: 10px;
                }
                QPushButton:hover { background-color: rgb(55, 95, 165); }
            """)
            btn_lihat.clicked.connect(lambda _, rid=report_id: self._lihat(rid))

            btn_edit = QPushButton("Edit")
            btn_edit.setFixedSize(44, 26)
            btn_edit.setStyleSheet("""
                QPushButton {
                    background-color: rgb(80, 65, 25); color: rgb(220, 195, 90);
                    border: none; border-radius: 4px; font-size: 10px;
                }
                QPushButton:hover { background-color: rgb(100, 85, 35); }
            """)
            btn_edit.clicked.connect(lambda _, rid=report_id: self._edit(rid))

            btn_hapus = QPushButton("Hapus")
            btn_hapus.setFixedSize(52, 26)
            btn_hapus.setStyleSheet("""
                QPushButton {
                    background-color: rgb(100, 30, 30); color: rgb(220, 120, 120);
                    border: none; border-radius: 4px; font-size: 10px;
                }
                QPushButton:hover { background-color: rgb(130, 40, 40); }
            """)
            btn_hapus.clicked.connect(lambda _, rid=report_id: self._hapus(rid))

            al.addWidget(btn_lihat)
            al.addWidget(btn_edit)
            al.addWidget(btn_hapus)
            al.addStretch()

            self.tabel.setCellWidget(i, 7, aksi)
            self.tabel.setRowHeight(i, 36)

    def _reset_filter(self):
        self.combo_section.setCurrentIndex(0)
        self.combo_shift.setCurrentIndex(0)
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        self.date_to.setDate(QDate.currentDate())
        self.load_data()

    def _lihat(self, report_id):
        try:
            header, produksi, catatan = get_detail_laporan(report_id)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Gagal memuat detail: {e}")
            return
        if header is None:
            QMessageBox.warning(self, "Tidak Ditemukan", f"Laporan #{report_id} tidak ditemukan.")
            return

        dlg = QDialog(self)
        dlg.setWindowTitle(f"Detail Laporan  —  #{report_id}")
        dlg.setMinimumWidth(900)
        dlg.setMinimumHeight(600)
        dlg.setStyleSheet("QDialog { background-color: rgb(33, 37, 43); color: rgb(220,220,220); }")

        lyt = QVBoxLayout(dlg)
        lyt.setContentsMargins(16, 16, 16, 16)
        lyt.setSpacing(10)

        def _cell(val, align=Qt.AlignLeft | Qt.AlignVCenter):
            it = QTableWidgetItem(str(val) if val else "")
            it.setTextAlignment(align)
            return it

        def _section_label(text):
            lbl = QLabel(text)
            lbl.setStyleSheet(
                "color: rgb(189, 147, 249); font-size: 12px; font-weight: bold; padding: 4px 0;"
            )
            return lbl

        hdr_frame = QFrame()
        hdr_frame.setStyleSheet(
            "QFrame { background-color: rgb(40, 44, 52); border-radius: 8px; }"
        )
        hdr_lyt = QGridLayout(hdr_frame)
        hdr_lyt.setContentsMargins(14, 10, 14, 10)
        hdr_lyt.setSpacing(6)
        hdr_lyt.setColumnStretch(1, 1)
        hdr_lyt.setColumnStretch(3, 1)

        def _fmt_whour(val):
            return f"{val:.2f} H" if val is not None else "—"

        pairs = [
            ("Tanggal",       header.get("date", "")),
            ("Shift",         header.get("shift", "")),
            ("Section",       header.get("section", "")),
            ("Koordinator",   header.get("coordinator", "")),
            ("Disetujui",     header.get("approved_by", "")),
            ("Diperiksa",     header.get("checked_by", "")),
            ("Plan W/Hour",   _fmt_whour(header.get("plan_whour"))),
            ("Actual W/Hour", _fmt_whour(header.get("actual_whour"))),
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

        if produksi:
            lyt.addWidget(_section_label("Data Produksi"))
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
                balance = p["plan_unit"] - (p["reg_actual"] + p["ot_2h"] + p["ot_3h"] + p["ot_11h"])
                bal_str = f"{balance:.0f}" if balance == int(balance) else f"{balance:.2f}"
                tbl_prod.setItem(i, 0, _cell(p.get("model", "")))
                tbl_prod.setItem(i, 1, _cell(f"{p['plan_unit']:.0f}", Qt.AlignCenter))
                tbl_prod.setItem(i, 2, _cell(f"{p['reg_actual']:.0f}", Qt.AlignCenter))
                tbl_prod.setItem(i, 3, _cell(f"{p['ot_2h']:.0f}", Qt.AlignCenter))
                tbl_prod.setItem(i, 4, _cell(f"{p['ot_3h']:.0f}", Qt.AlignCenter))
                tbl_prod.setItem(i, 5, _cell(f"{p['ot_11h']:.0f}", Qt.AlignCenter))
                tbl_prod.setItem(i, 6, _cell(bal_str, Qt.AlignCenter))
            lyt.addWidget(tbl_prod)

        lyt.addWidget(_section_label("Catatan Masalah"))
        tbl = QTableWidget()
        tbl.setColumnCount(9)
        tbl.setHorizontalHeaderLabels([
            "No. RA", "Kategori", "Deskripsi", "Penyebab",
            "Tindakan", "PIC", "Start", "End", "Loss Time (H)",
        ])
        tbl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        for fixed_col in (0, 1, 5, 6, 7, 8):
            tbl.horizontalHeader().setSectionResizeMode(
                fixed_col, QHeaderView.ResizeToContents
            )
        tbl.verticalHeader().setVisible(False)
        tbl.setEditTriggers(QAbstractItemView.NoEditTriggers)
        tbl.setWordWrap(True)
        tbl.setStyleSheet(_TABLE_STYLE)

        for i, c in enumerate(catatan):
            tbl.insertRow(i)
            tbl.setItem(i, 0, _cell(c.get("ra_number", ""), Qt.AlignCenter))
            tbl.setItem(i, 1, _cell(c.get("category", "")))
            tbl.setItem(i, 2, _cell(c.get("description", "")))
            tbl.setItem(i, 3, _cell(c.get("cause", "")))
            tbl.setItem(i, 4, _cell(c.get("corrective_action", "")))
            tbl.setItem(i, 5, _cell(c.get("pic", ""), Qt.AlignCenter))
            tbl.setItem(i, 6, _cell(c.get("start_time", ""), Qt.AlignCenter))
            tbl.setItem(i, 7, _cell(c.get("end_time", ""), Qt.AlignCenter))
            tbl.setItem(i, 8, _cell(f"{c.get('loss_time', 0):.2f}", Qt.AlignCenter))
            tbl.resizeRowToContents(i)
        lyt.addWidget(tbl)

        btn_box = QDialogButtonBox(QDialogButtonBox.Close)
        btn_box.setStyleSheet("""
            QPushButton {
                background-color: rgb(60, 65, 75); color: rgb(200, 200, 200);
                border: none; border-radius: 5px; padding: 6px 18px; font-size: 11px;
            }
            QPushButton:hover { background-color: rgb(75, 80, 90); }
        """)
        btn_box.rejected.connect(dlg.close)
        lyt.addWidget(btn_box)

        dlg.exec()

    def _edit(self, report_id):
        print(f"Edit laporan ID: {report_id}")

    def _hapus(self, report_id):
        reply = QMessageBox.question(
            self,
            "Konfirmasi Hapus",
            f"Hapus laporan #{report_id}?\nSemua catatan masalah terkait juga akan dihapus.\nTindakan ini tidak dapat dibatalkan.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            ok, msg = hapus_laporan(report_id)
            if ok:
                QMessageBox.information(self, "Berhasil", msg)
                self.load_data()
            else:
                QMessageBox.critical(self, "Gagal", msg)

    def _export_excel(self):
        try:
            import openpyxl
            from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        except ImportError:
            QMessageBox.critical(
                self, "Error",
                "openpyxl tidak terinstall.\nJalankan: pip install openpyxl",
            )
            return

        row_count = self.tabel.rowCount()
        if row_count == 0:
            QMessageBox.warning(self, "Peringatan", "Tidak ada data untuk diekspor.")
            return

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Riwayat Laporan"

        col_headers = [
            "No", "Tanggal", "Section", "Shift",
            "Koordinator", "Total Loss Time (H)", "Status",
        ]
        thin = Side(style="thin", color="3C4147")
        border = Border(left=thin, right=thin, top=thin, bottom=thin)
        hdr_fill = PatternFill("solid", fgColor="1C2028")
        hdr_font = Font(color="9696A0", bold=True, size=10)
        hdr_align = Alignment(horizontal="center", vertical="center")

        for ci, h in enumerate(col_headers, 1):
            cell = ws.cell(row=1, column=ci, value=h)
            cell.fill = hdr_fill
            cell.font = hdr_font
            cell.alignment = hdr_align
            cell.border = border

        center_cols = {0, 1, 3, 5, 6}
        for ri in range(row_count):
            for ci in range(7):
                item = self.tabel.item(ri, ci)
                val = item.text() if item else ""
                cell = ws.cell(row=ri + 2, column=ci + 1, value=val)
                cell.alignment = Alignment(
                    horizontal="center" if ci in center_cols else "left",
                    vertical="center",
                )
                cell.border = border

        for ci, w in enumerate([6, 12, 30, 12, 22, 20, 10], 1):
            ws.column_dimensions[openpyxl.utils.get_column_letter(ci)].width = w
        ws.row_dimensions[1].height = 20

        downloads = os.path.join(os.path.expanduser("~"), "Downloads")
        date_str = QDate.currentDate().toString("yyyyMMdd")
        filepath = os.path.join(downloads, f"riwayat_laporan_{date_str}.xlsx")

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

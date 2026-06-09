from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QComboBox, QPushButton, QCheckBox,
    QDateEdit, QTimeEdit, QScrollArea, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QAbstractItemView,
)
from PySide6.QtCore import Qt, QDate, QTime
from PySide6.QtGui import QColor

from controllers.laporan_controller import simpan_laporan_harian
from controllers.master_controller import (
    get_all_sections, get_all_shifts, get_models_by_section, get_all_category_names,
    get_op_numbers_by_section,
)
from modules.icons import ic_add, ic_del, ic_prev, ic_next, BTN_ICON_SIZE, NAV_ICON_SIZE
from modules.view_optimizer import LazyViewMixin

# Style constants — Light Theme
_CARD  = "QFrame { background-color: #FFFFFF; border-radius: 0px; border: 1px solid #E5E7EB; }"
_TBL   = """
    QTableWidget { background-color: #FFFFFF; border: 1px solid #D1D5DB; gridline-color: #F3F4F6; }
    QTableWidget::item { color: #212121; padding: 3px 6px; background-color: #FFFFFF;
        border-bottom: 1px solid #F3F4F6; }
    QTableWidget::item:alternate { background-color: #F9FAFB; }
    QTableWidget::item:selected { background-color: #F3F4F6; color: #212121; }
    QHeaderView::section { background-color: #F8F9FA; color: #6B7280; border: none;
        border-bottom: 1px solid #D1D5DB; border-right: 1px solid #E5E7EB;
        padding: 4px 6px; font-weight: bold; font-size: 10px;
        text-transform: uppercase; letter-spacing: 1px; }
"""
_COMBO_CELL = """
    QComboBox { background-color: transparent; color: #212121; border: none;
        padding: 0px 4px; margin: 0px; font-size: 11px; }
    QComboBox::drop-down { border: none; width: 18px; }
    QComboBox QAbstractItemView { background-color: #FFFFFF; color: #212121;
        selection-background-color: #F3F4F6; border: 1px solid #D1D5DB; }
"""
_BTN_ADD = ("QPushButton { background-color: #E8F5E9; color: #2e7d32;"
            " border: 1px solid #A5D6A7; border-radius: 0px; padding: 0 10px; font-size: 11px; }"
            "QPushButton:hover { background-color: #C8E6C9; }")
_BTN_DEL = ("QPushButton { background-color: #FFEBEE; color: #c62828;"
            " border: 1px solid #FFCDD2; border-radius: 0px; padding: 0 10px; font-size: 11px; }"
            "QPushButton:hover { background-color: #FFCDD2; }")
_HDR_LBL = ("color: #212121; font-size: 11px; font-weight: bold;"
            " border-left: 2px solid #E60012; padding-left: 8px;"
            " letter-spacing: 1px; text-transform: uppercase;")
_FLD_LBL = "color: #6B7280; font-size: 10px; letter-spacing: 1px;"

# Model & operation codes — bisa diperluas dari master data nanti
_MODELS  = ["4G15", "4G63", "4M40", "6D16", "6D16E", "6D16T",
            "TD-TI", "TD-TK", "TD-TH", "TD-TL"]
_OP_ST   = ["CS-10", "CS-12", "CS-17", "CS-18", "CS-20",
            "CS-30", "CS-40", "CS-50", "CS-60", "CS-70"]
_FACTORS = ["Machine", "Setting", "Man", "Tool", "Material",
            "Meeting", "Quality", "Try Cut", "Preparation", "Others"]
_NOTE_TYPES = ["Sakit", "Izin", "Alpa", "Cuti", "Sholat Jumat", "Terlambat", "Lainnya"]
_SATUAN  = ["Unit", "Pcs", "Set", "Lot", "Kg", "Box", "Sheet"]


def _mk_combo(items, popup_w=120) -> QComboBox:
    c = QComboBox()
    c.addItems(items)
    c.setStyleSheet(_COMBO_CELL)
    c.view().setMinimumWidth(popup_w)
    return c



def _item(text="", align=Qt.AlignLeft | Qt.AlignVCenter) -> QTableWidgetItem:
    it = QTableWidgetItem(text)
    it.setTextAlignment(align)
    return it


# Main Widget

class InputLaporanWidget(LazyViewMixin, QWidget):
    def __init__(self, user: dict, parent=None):
        super().__init__(parent)
        self._user         = user
        self._shift_map: dict = {}   # name → {total_hours, preparation_min, sholat_min}
        self._shift_hours  = 0.0
        self._prep_h       = 15.0 / 60
        self._sholat_h     = 10.0 / 60
        self._ot_hours     = 0.0
        self._shop_models: list[str] = []
        self._shop_model_hours: dict[str, float] = {}   # model → H/unit (MHU)
        self._shop_model_cycle: dict[str, float] = {}   # model → cycle time (s)
        self._op_numbers: list[str] = []                # OP/ST per shop
        self._factors: list[str] = _FACTORS[:]
        self._setup_ui()

    # lifecycle

    def _on_first_show(self):
        self._reload_sections()
        self._reload_shifts()
        self._reload_factors()

    def _on_show(self):
        pass  # state form dipertahankan — tidak perlu reload tiap klik

    def _reload_factors(self):
        names = get_all_category_names()
        if names:
            self._factors = names

    def _reload_sections(self):
        try:
            prev = self.combo_section.currentData()
            self.combo_section.blockSignals(True)
            self.combo_section.clear()
            for sid, sname in get_all_sections():
                self.combo_section.addItem(sname, sid)
            if prev is not None:
                idx = self.combo_section.findData(prev)
                if idx >= 0:
                    self.combo_section.setCurrentIndex(idx)
            self.combo_section.blockSignals(False)
        except Exception as e:
            QMessageBox.warning(self, "Gagal Memuat Shop", str(e))
        self._reload_models_for_shop()

    def _reload_models_for_shop(self):
        section_id = self.combo_section.currentData()
        if section_id is None:
            self._shop_models  = []
            self._shop_model_hours = {}
            self._op_numbers   = []
            return
        try:
            rows = get_models_by_section(section_id)
            self._shop_models      = [r["model_name"] for r in rows]
            self._shop_model_hours = {r["model_name"]: r["working_hour"]  for r in rows}
            self._shop_model_cycle = {r["model_name"]: r["cycle_time"]    for r in rows}
        except Exception as e:
            self._shop_models      = []
            self._shop_model_hours = {}
            self._shop_model_cycle = {}
            QMessageBox.warning(self, "Gagal Memuat Model", str(e))
        try:
            op_rows = get_op_numbers_by_section(section_id)
            self._op_numbers = [r["op_no"] for r in op_rows]
        except Exception:
            self._op_numbers = []

    def _reload_shifts(self):
        try:
            prev_name = self.combo_shift.currentText()
            shifts = get_all_shifts()
            self._shift_map = {
                s["name"]: {
                    "total_hours":     s["total_hours"],
                    "preparation_min": s.get("preparation_min", 15.0),
                    "sholat_min":      s.get("sholat_min", 10.0),
                }
                for s in shifts
            }
            self.combo_shift.blockSignals(True)
            self.combo_shift.clear()
            for s in shifts:
                self.combo_shift.addItem(s["name"])
            if prev_name:
                idx = self.combo_shift.findText(prev_name)
                if idx >= 0:
                    self.combo_shift.setCurrentIndex(idx)
            self.combo_shift.blockSignals(False)
            self._on_shift_changed()
        except Exception as e:
            QMessageBox.warning(self, "Gagal Memuat Shift", str(e))

    def _on_shift_changed(self):
        data = self._shift_map.get(self.combo_shift.currentText(), {})
        base_hours        = data.get("total_hours", 0.0)
        self._prep_h      = data.get("preparation_min", 15.0) / 60
        self._sholat_h    = data.get("sholat_min", 10.0) / 60
        # Jumat: potong 30 menit (0.5 jam) — hanya untuk Day Shift
        if self.chk_pengganti.isChecked():
            day_map = {"Senin": 1, "Selasa": 2, "Rabu": 3, "Kamis": 4,
                       "Jumat": 5, "Sabtu": 6, "Minggu": 7}
            effective_day = day_map.get(self.combo_pengganti.currentText(), 1)
        else:
            effective_day = self.input_tanggal.date().dayOfWeek()
        is_friday    = effective_day == 5
        is_day_shift = "night" not in self.combo_shift.currentText().lower()
        self._shift_hours = base_hours - 0.5 if (is_friday and is_day_shift and base_hours > 0) else base_hours
        self._shift_hours += self._ot_hours
        self._lbl_hour.setText(f"{self._shift_hours:.2f}")
        self._lbl_prep_val.setText(f"{self._prep_h:.4f}")
        self._lbl_sholat_val.setText(f"{self._sholat_h:.4f}")
        self._hitung_calc_hour()

    def _update_day(self, date: QDate):
        days = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
        self._lbl_day.setText(days[date.dayOfWeek() - 1])
        # Recalculate effective hours karena Jumat ada potongan 30 menit
        # Guard: combo_shift belum ada saat _build_header() pertama kali dipanggil
        if hasattr(self, "combo_shift"):
            self._on_shift_changed()

    # UI builder

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        main = QVBoxLayout(container)
        main.setContentsMargins(12, 12, 12, 12)
        main.setSpacing(8)

        main.addWidget(self._build_header())
        main.addLayout(self._build_top_row())
        main.addWidget(self._build_inhouse_claim())
        main.addWidget(self._build_line_stop())
        main.addLayout(self._build_footer())
        main.addStretch()

        scroll.setWidget(container)
        outer.addWidget(scroll)

    # Header

    def _build_header(self) -> QFrame:
        card = QFrame()
        card.setStyleSheet(
            "QFrame { background-color: #FFFFFF; border-radius: 0px;"
            " border-top: 2px solid #E60012; border-bottom: 1px solid #E5E7EB; }"
        )
        lay = QHBoxLayout(card)
        lay.setContentsMargins(12, 8, 12, 8)
        lay.setSpacing(8)

        _combo_ss = (
            "QComboBox { background:#FFFFFF; border:1px solid #D1D5DB; border-radius:2px;"
            " padding-left:8px; color:#212121; font-size:11px; }"
            "QComboBox::drop-down { border:none; width:22px; }"
            "QComboBox QAbstractItemView { background:#FFFFFF; color:#212121;"
            " selection-background-color:#F3F4F6; border:1px solid #D1D5DB; }"
        )

        def _lbl(t):
            l = QLabel(t)
            l.setStyleSheet(_FLD_LBL)
            return l

        def _vsep():
            sep = QFrame()
            sep.setFrameShape(QFrame.VLine)
            sep.setFixedWidth(1)
            sep.setFixedHeight(22)
            sep.setStyleSheet("background-color: #D1D5DB; border: none;")
            return sep

        # Shop group
        lay.addWidget(_lbl("Shop"))
        self.combo_section = QComboBox()
        self.combo_section.setMinimumWidth(150)
        self.combo_section.setMinimumHeight(28)
        self.combo_section.setStyleSheet(_combo_ss)
        self.combo_section.currentIndexChanged.connect(self._reload_models_for_shop)
        lay.addWidget(self.combo_section)

        lay.addSpacing(4)
        lay.addWidget(_vsep())
        lay.addSpacing(4)

        # Date group
        lay.addWidget(_lbl("Date"))
        btn_prev = QPushButton()
        btn_prev.setIcon(ic_prev())
        btn_prev.setIconSize(NAV_ICON_SIZE)
        btn_prev.setFixedSize(22, 26)
        btn_prev.setStyleSheet(
            "QPushButton { background:#F3F4F6; color:#6B7280; border:1px solid #D1D5DB;"
            " font-size:9px; }"
            "QPushButton:hover { background:#D1D5DB; color:#212121; }"
        )
        self.input_tanggal = QDateEdit()
        self.input_tanggal.setDate(QDate.currentDate())
        self.input_tanggal.setCalendarPopup(True)
        self.input_tanggal.setMinimumHeight(28)
        self.input_tanggal.setMinimumWidth(95)
        self.input_tanggal.setDisplayFormat("dd/MM/yyyy")
        self.input_tanggal.setStyleSheet(
            "QDateEdit { background:#FFFFFF; border:1px solid #D1D5DB; border-radius:2px;"
            " padding-left:8px; color:#212121; font-size:11px; }"
            "QDateEdit::drop-down { border:none; width:0px; }"
        )
        # ── Style kalender popup ─────────────────────────────────────────────
        cal = self.input_tanggal.calendarWidget()
        cal.setStyleSheet("""
            QCalendarWidget QWidget#qt_calendar_navigationbar {
                background-color: #F8F9FA; border-bottom: 1px solid #E5E7EB; }
            QCalendarWidget QToolButton {
                color: #212121; background: transparent; border: none;
                font-size: 11px; font-weight: bold; padding: 4px 8px; }
            QCalendarWidget QToolButton:hover { background-color: #F3F4F6; }
            QCalendarWidget QMenu {
                background-color: #FFFFFF; color: #212121;
                border: 1px solid #D1D5DB; }
            QCalendarWidget QSpinBox {
                color: #212121; background-color: #FFFFFF;
                border: 1px solid #D1D5DB; selection-background-color: #E60012; }
            QCalendarWidget QAbstractItemView {
                background-color: #FFFFFF; color: #6B7280;
                selection-background-color: #E60012; selection-color: #FFFFFF;
                outline: none; }
            QCalendarWidget QAbstractItemView:disabled { color: #D1D5DB; }
            QCalendarWidget QHeaderView::section {
                background-color: #F8F9FA; color: #9CA3AF;
                font-size: 10px; font-weight: bold;
                border: none; border-bottom: 1px solid #E5E7EB; padding: 3px; }
        """)
        btn_next = QPushButton()
        btn_next.setIcon(ic_next())
        btn_next.setIconSize(NAV_ICON_SIZE)
        btn_next.setFixedSize(22, 26)
        btn_next.setStyleSheet(
            "QPushButton { background:#F3F4F6; color:#6B7280; border:1px solid #D1D5DB;"
            " font-size:9px; }"
            "QPushButton:hover { background:#D1D5DB; color:#212121; }"
        )
        btn_prev.clicked.connect(
            lambda: self.input_tanggal.setDate(self.input_tanggal.date().addDays(-1))
        )
        btn_next.clicked.connect(
            lambda: self.input_tanggal.setDate(self.input_tanggal.date().addDays(1))
        )
        lay.addWidget(btn_prev)
        lay.addWidget(self.input_tanggal)
        lay.addWidget(btn_next)

        self._lbl_day = QLabel("—")
        self._lbl_day.setStyleSheet("color:#E60012; font-size:11px; font-weight:bold; min-width:48px; background:transparent;")
        lay.addWidget(self._lbl_day)
        self.input_tanggal.dateChanged.connect(self._update_day)
        self._update_day(QDate.currentDate())

        lay.addSpacing(4)
        lay.addWidget(_vsep())
        lay.addSpacing(4)

        # Shift group
        lay.addWidget(_lbl("Shift"))
        self.combo_shift = QComboBox()
        self.combo_shift.setMinimumWidth(90)
        self.combo_shift.setMinimumHeight(28)
        self.combo_shift.setStyleSheet(_combo_ss)
        self.combo_shift.currentIndexChanged.connect(self._on_shift_changed)
        lay.addWidget(self.combo_shift)

        lay.addSpacing(4)
        lay.addWidget(_vsep())
        lay.addSpacing(4)

        # Hour group
        lay.addWidget(_lbl("Hour"))
        self._lbl_hour = QLabel("—")
        self._lbl_hour.setStyleSheet("color:#212121; font-size:13px; font-weight:bold; min-width:36px; background:transparent;")
        lay.addWidget(self._lbl_hour)

        lay.addWidget(_vsep())
        lay.addSpacing(4)

        # OT group
        lay.addWidget(_lbl("OT"))
        self.combo_ot = QComboBox()
        self.combo_ot.addItems(["—", "2H", "3H", "11H"])
        self.combo_ot.setMinimumWidth(60)
        self.combo_ot.setMinimumHeight(28)
        self.combo_ot.setStyleSheet(_combo_ss)
        self.combo_ot.currentIndexChanged.connect(self._on_ot_changed)
        lay.addWidget(self.combo_ot)

        lay.addWidget(_vsep())
        lay.addSpacing(4)

        # Hari Pengganti group
        self.chk_pengganti = QCheckBox("Hari Pengganti")
        self.chk_pengganti.setStyleSheet(
            "QCheckBox { color: #6B7280; font-size: 10px; letter-spacing: 1px; background: transparent; }"
            "QCheckBox::indicator { width: 14px; height: 14px; }"
            "QCheckBox::indicator:checked { background: #E60012; border: 1px solid #E60012; }"
            "QCheckBox::indicator:unchecked { background: #FFFFFF; border: 1px solid #D1D5DB; }"
        )
        self.chk_pengganti.toggled.connect(self._on_pengganti_toggled)
        lay.addWidget(self.chk_pengganti)

        self.combo_pengganti = QComboBox()
        self.combo_pengganti.addItems(
            ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
        )
        self.combo_pengganti.setMinimumWidth(80)
        self.combo_pengganti.setMinimumHeight(28)
        self.combo_pengganti.setStyleSheet(_combo_ss)
        self.combo_pengganti.setVisible(False)
        self.combo_pengganti.currentIndexChanged.connect(self._on_shift_changed)
        lay.addWidget(self.combo_pengganti)

        lay.addStretch()

        lbl_user = QLabel(self._user.get("name", "").upper())
        lbl_user.setStyleSheet(
            "color:#E60012; font-size:11px; font-weight:bold;"
            " padding: 3px 8px; background-color: #F8F9FA;"
        )
        lay.addWidget(lbl_user)

        return card

    # Top 3-panel row

    def _build_top_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(8)
        row.addWidget(self._build_production_panel(), 3)
        row.addWidget(self._build_absence_panel(), 3)
        row.addWidget(self._build_calc_hour_panel(), 2)
        return row

    def _build_production_panel(self) -> QFrame:
        card = QFrame(); card.setStyleSheet(_CARD)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(10, 10, 10, 10); lay.setSpacing(6)

        hdr = QHBoxLayout()
        hdr.addWidget(QLabel("Production Volume", styleSheet=_HDR_LBL))
        hdr.addStretch()
        ba = QPushButton("Add"); ba.setIcon(ic_add()); ba.setIconSize(BTN_ICON_SIZE); ba.setFixedHeight(24); ba.setStyleSheet(_BTN_ADD)
        bd = QPushButton("Del"); bd.setIcon(ic_del()); bd.setIconSize(BTN_ICON_SIZE); bd.setFixedHeight(24); bd.setStyleSheet(_BTN_DEL)
        ba.clicked.connect(self._tambah_produksi)
        bd.clicked.connect(self._hapus_produksi)
        hdr.addWidget(ba); hdr.addWidget(bd)
        lay.addLayout(hdr)

        self.tbl_prod = QTableWidget(0, 5)
        self.tbl_prod.setHorizontalHeaderLabels(
            ["Model", "Plan Qty", "Act Qty", "Plan H", "Act H"]
        )
        h = self.tbl_prod.horizontalHeader()
        h.setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_prod.verticalHeader().setVisible(False)
        self.tbl_prod.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl_prod.setStyleSheet(_TBL)
        self.tbl_prod.setMinimumHeight(130)
        self.tbl_prod.itemChanged.connect(self._on_prod_item_changed)
        lay.addWidget(self.tbl_prod)
        return card

    def _build_absence_panel(self) -> QFrame:
        card = QFrame(); card.setStyleSheet(_CARD)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(10, 10, 10, 10); lay.setSpacing(6)

        hdr = QHBoxLayout()
        hdr.addWidget(QLabel("Absence", styleSheet=_HDR_LBL))
        hdr.addStretch()
        ba = QPushButton("Add"); ba.setIcon(ic_add()); ba.setIconSize(BTN_ICON_SIZE); ba.setFixedHeight(24); ba.setStyleSheet(_BTN_ADD)
        bd = QPushButton("Del"); bd.setIcon(ic_del()); bd.setIconSize(BTN_ICON_SIZE); bd.setFixedHeight(24); bd.setStyleSheet(_BTN_DEL)
        ba.clicked.connect(self._tambah_absen)
        bd.clicked.connect(self._hapus_absen)
        hdr.addWidget(ba); hdr.addWidget(bd)
        lay.addLayout(hdr)

        self.tbl_absen = QTableWidget(0, 4)
        self.tbl_absen.setHorizontalHeaderLabels(["NIK", "Name", "Note", "Hour"])
        h = self.tbl_absen.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.Fixed)
        h.setSectionResizeMode(1, QHeaderView.Stretch)
        h.setSectionResizeMode(2, QHeaderView.Fixed)
        h.setSectionResizeMode(3, QHeaderView.Fixed)
        self.tbl_absen.setColumnWidth(0, 55)
        self.tbl_absen.setColumnWidth(2, 80)
        self.tbl_absen.setColumnWidth(3, 52)
        self.tbl_absen.verticalHeader().setVisible(False)
        self.tbl_absen.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl_absen.setStyleSheet(_TBL)
        self.tbl_absen.setMinimumHeight(130)
        self.tbl_absen.itemChanged.connect(self._hitung_calc_hour)
        lay.addWidget(self.tbl_absen)
        return card

    def _build_calc_hour_panel(self) -> QFrame:
        card = QFrame(); card.setStyleSheet(_CARD)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(12, 10, 12, 10); lay.setSpacing(0)

        lay.addWidget(QLabel("Calculation Hour", styleSheet=_HDR_LBL))
        lay.addSpacing(8)

        grid = QGridLayout()
        grid.setSpacing(3)
        grid.setColumnMinimumWidth(0, 80)

        def _rlbl(t):
            l = QLabel(t); l.setStyleSheet(_FLD_LBL); return l

        def _vlbl(t="—"):
            l = QLabel(t)
            l.setStyleSheet("color:#212121; font-size:11px; font-weight:bold; background:transparent;")
            l.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            return l

        self._lbl_process   = _vlbl()
        self._lbl_prep_val  = _vlbl(f"{self._prep_h:.4f}")
        self._lbl_prep_val.setStyleSheet("color:#9CA3AF; font-size:11px; background:transparent;")
        self._lbl_prep_val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._lbl_quality   = _vlbl("0.0000")
        self._lbl_linestop  = _vlbl()
        self._lbl_absence   = _vlbl()
        self._lbl_sholat_val = _vlbl(f"{self._sholat_h:.4f}")
        self._lbl_sholat_val.setStyleSheet("color:#9CA3AF; font-size:11px; background:transparent;")
        self._lbl_sholat_val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._lbl_total     = _vlbl()
        self._lbl_balance   = _vlbl()

        rows = [
            ("Process",     self._lbl_process),
            ("Preparation", self._lbl_prep_val),
            ("Quality",     self._lbl_quality),
            ("Line Stop",   self._lbl_linestop),
            ("Absence",     self._lbl_absence),
            ("Sholat",      self._lbl_sholat_val),
        ]
        for i, (name, wgt) in enumerate(rows):
            grid.addWidget(_rlbl(name), i, 0)
            grid.addWidget(wgt, i, 1)

        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setFixedHeight(1)
        divider.setStyleSheet("background-color: #D1D5DB; border: none;")
        grid.addWidget(divider, len(rows), 0, 1, 2)

        lbl_total = QLabel("TOTAL")
        lbl_total.setStyleSheet("color:#6B7280; font-size:11px; font-weight:bold; background:transparent;")
        grid.addWidget(lbl_total, len(rows) + 1, 0)
        grid.addWidget(self._lbl_total, len(rows) + 1, 1)

        lay.addLayout(grid)
        lay.addSpacing(6)

        bal_frame = QFrame()
        bal_frame.setObjectName("balFrame")
        bal_frame.setStyleSheet(
            "#balFrame { background-color: #F8F9FA; border: 1px solid #D1D5DB;"
            " border-left: 3px solid #E60012; }"
        )
        bal_row = QHBoxLayout(bal_frame)
        bal_row.setContentsMargins(8, 5, 8, 5)
        lbl_bal = QLabel("BALANCE")
        lbl_bal.setStyleSheet("color:#6B7280; font-size:11px; font-weight:bold; background:transparent;")
        self._lbl_balance.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._lbl_balance.setStyleSheet("color:#212121; font-size:13px; font-weight:bold; background:transparent;")
        bal_row.addWidget(lbl_bal)
        bal_row.addStretch()
        bal_row.addWidget(self._lbl_balance)
        lay.addWidget(bal_frame)

        lay.addStretch()
        return card

    # In House Claim

    def _build_inhouse_claim(self) -> QFrame:
        card = QFrame(); card.setStyleSheet(_CARD)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(10, 10, 10, 10); lay.setSpacing(6)

        hdr = QHBoxLayout()
        hdr.addWidget(QLabel("In House (Reject) and Market Claim", styleSheet=_HDR_LBL))
        hdr.addStretch()
        ba = QPushButton("Add"); ba.setIcon(ic_add()); ba.setIconSize(BTN_ICON_SIZE); ba.setFixedHeight(24); ba.setStyleSheet(_BTN_ADD)
        bd = QPushButton("Del"); bd.setIcon(ic_del()); bd.setIconSize(BTN_ICON_SIZE); bd.setFixedHeight(24); bd.setStyleSheet(_BTN_DEL)
        ba.clicked.connect(self._tambah_claim)
        bd.clicked.connect(self._hapus_claim)
        hdr.addWidget(ba); hdr.addWidget(bd)
        lay.addLayout(hdr)

        # No | Model | OP/ST | Item | Qty | Satuan | Cause/Penyebab | Action/Perbaikan | Factor | Hour | Lost
        self.tbl_claim = QTableWidget(0, 12)
        self.tbl_claim.setHorizontalHeaderLabels([
            "No", "Model", "OP/ST", "Item", "Qty", "Satuan",
            "Cause / Penyebab", "Action / Perbaikan", "Factor", "Hour", "Lost", "Status",
        ])
        h = self.tbl_claim.horizontalHeader()
        h.setSectionResizeMode(QHeaderView.Fixed)
        h.setSectionResizeMode(3, QHeaderView.Stretch)
        h.setSectionResizeMode(6, QHeaderView.Stretch)
        h.setSectionResizeMode(7, QHeaderView.Stretch)
        self.tbl_claim.setColumnWidth(0,  28)
        self.tbl_claim.setColumnWidth(1,  60)
        self.tbl_claim.setColumnWidth(2,  60)
        self.tbl_claim.setColumnWidth(4,  42)
        self.tbl_claim.setColumnWidth(5,  55)
        self.tbl_claim.setColumnWidth(8,  75)
        self.tbl_claim.setColumnWidth(9,  50)
        self.tbl_claim.setColumnWidth(10, 50)
        self.tbl_claim.setColumnWidth(11, 75)
        self.tbl_claim.verticalHeader().setVisible(False)
        self.tbl_claim.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl_claim.setWordWrap(True)
        self.tbl_claim.setStyleSheet(_TBL)
        self.tbl_claim.setMinimumHeight(140)
        self.tbl_claim.itemChanged.connect(self._on_claim_item_changed)
        self.tbl_claim.itemChanged.connect(self._auto_resize_claim_row)
        lay.addWidget(self.tbl_claim)
        return card

    # Line Stop

    def _build_line_stop(self) -> QFrame:
        card = QFrame(); card.setStyleSheet(_CARD)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(10, 10, 10, 10); lay.setSpacing(6)

        title = QLabel(
            "Line Stop  ( Tool / Model Change / Man / Machine / Material / Meeting / Quality and Others )",
            styleSheet=_HDR_LBL,
        )
        title.setWordWrap(True)

        hdr = QHBoxLayout()
        hdr.addWidget(title)
        hdr.addStretch()
        ba = QPushButton("Add"); ba.setIcon(ic_add()); ba.setIconSize(BTN_ICON_SIZE); ba.setFixedHeight(24); ba.setStyleSheet(_BTN_ADD)
        bd = QPushButton("Del"); bd.setIcon(ic_del()); bd.setIconSize(BTN_ICON_SIZE); bd.setFixedHeight(24); bd.setStyleSheet(_BTN_DEL)
        ba.clicked.connect(self._tambah_linestop)
        bd.clicked.connect(self._hapus_linestop)
        hdr.addWidget(ba); hdr.addWidget(bd)
        lay.addLayout(hdr)

        # No | Model | OP/ST | Problem / Masalah | Cause / Penyebab | Action / Perbaikan | Factor | Start | End | Stop | Lost
        self.tbl_ls = QTableWidget(0, 11)
        self.tbl_ls.setHorizontalHeaderLabels([
            "No", "Model", "OP/ST",
            "Problem / Masalah", "Cause / Penyebab", "Action / Perbaikan",
            "Factor", "Start", "End", "Stop", "Lost",
        ])
        h = self.tbl_ls.horizontalHeader()
        h.setSectionResizeMode(QHeaderView.Fixed)
        h.setSectionResizeMode(3, QHeaderView.Stretch)
        h.setSectionResizeMode(4, QHeaderView.Stretch)
        h.setSectionResizeMode(5, QHeaderView.Stretch)
        self.tbl_ls.setColumnWidth(0,  28)
        self.tbl_ls.setColumnWidth(1,  60)
        self.tbl_ls.setColumnWidth(2,  60)
        self.tbl_ls.setColumnWidth(6,  80)
        self.tbl_ls.setColumnWidth(7,  54)
        self.tbl_ls.setColumnWidth(8,  54)
        self.tbl_ls.setColumnWidth(9,  52)
        self.tbl_ls.setColumnWidth(10, 52)
        self.tbl_ls.verticalHeader().setVisible(False)
        self.tbl_ls.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl_ls.setWordWrap(True)
        self.tbl_ls.setStyleSheet(_TBL)
        self.tbl_ls.setMinimumHeight(140)
        self.tbl_ls.itemChanged.connect(self._hitung_calc_hour)
        self.tbl_ls.itemChanged.connect(self._auto_resize_ls_row)
        lay.addWidget(self.tbl_ls)
        return card

    # Footer

    def _build_footer(self) -> QHBoxLayout:
        lay = QHBoxLayout(); lay.setSpacing(10)

        lay.addStretch()

        btn_reset = QPushButton("Reset")
        btn_reset.setMinimumSize(90, 34)
        btn_reset.setStyleSheet(
            "QPushButton { background:#F3F4F6; color:#6B7280; border:none; font-size:11px; }"
            "QPushButton:hover { background:#D1D5DB; color:#212121; }"
        )
        btn_reset.clicked.connect(self.reset_form)

        btn_save = QPushButton("Simpan Laporan")
        btn_save.setMinimumSize(140, 34)
        btn_save.setStyleSheet(
            "QPushButton { background:#E60012; color:#fff; border:none; font-size:11px; font-weight:bold; }"
            "QPushButton:hover { background:#C0000F; }"
        )
        btn_save.clicked.connect(self.simpan_laporan)

        lay.addWidget(btn_reset)
        lay.addWidget(btn_save)
        return lay

    # Row helpers

    def _tambah_produksi(self):
        r = self.tbl_prod.rowCount()
        self.tbl_prod.blockSignals(True)
        self.tbl_prod.insertRow(r)
        self.tbl_prod.setRowHeight(r, 30)
        models = self._shop_models or _MODELS
        combo = _mk_combo(models)
        self.tbl_prod.setCellWidget(r, 0, combo)
        self.tbl_prod.setItem(r, 1, _item("", Qt.AlignCenter))  # Plan Qty
        self.tbl_prod.setItem(r, 2, _item("", Qt.AlignCenter))  # Act Qty
        plh_it = _item("", Qt.AlignCenter)
        plh_it.setFlags(Qt.ItemIsEnabled)
        plh_it.setBackground(QColor("#F3F4F6"))
        plh_it.setForeground(QColor("#9CA3AF"))
        self.tbl_prod.setItem(r, 3, plh_it)                     # Plan H (readonly)
        self.tbl_prod.setItem(r, 4, _item("", Qt.AlignCenter))  # Act H
        self.tbl_prod.blockSignals(False)
        combo.currentTextChanged.connect(lambda _, cb=combo: self._autofill_mhu_by_model(cb))

    def _on_ot_changed(self):
        ot_map = {"—": 0.0, "2H": 2.0, "3H": 3.0, "11H": 11.0}
        self._ot_hours = ot_map.get(self.combo_ot.currentText(), 0.0)
        self._on_shift_changed()

    def _on_pengganti_toggled(self, checked: bool):
        self.combo_pengganti.setVisible(checked)
        self._on_shift_changed()

    def _hapus_produksi(self):
        r = self.tbl_prod.currentRow()
        if r >= 0:
            self.tbl_prod.removeRow(r)
            self._hitung_calc_hour()

    def _tambah_absen(self):
        r = self.tbl_absen.rowCount()
        self.tbl_absen.blockSignals(True)
        self.tbl_absen.insertRow(r)
        self.tbl_absen.setRowHeight(r, 30)
        self.tbl_absen.setItem(r, 0, _item("", Qt.AlignCenter))
        self.tbl_absen.setItem(r, 1, _item("", Qt.AlignCenter))
        self.tbl_absen.setCellWidget(r, 2, _mk_combo(_NOTE_TYPES, popup_w=100))
        self.tbl_absen.setItem(r, 3, _item("", Qt.AlignCenter))
        self.tbl_absen.blockSignals(False)

    def _hapus_absen(self):
        r = self.tbl_absen.currentRow()
        if r >= 0:
            self.tbl_absen.removeRow(r)
            self._hitung_calc_hour()

    def _tambah_claim(self):
        r = self.tbl_claim.rowCount()
        self.tbl_claim.insertRow(r)
        self.tbl_claim.setRowHeight(r, 30)

        no_it = _item(str(r + 1), Qt.AlignCenter)
        no_it.setFlags(Qt.ItemIsEnabled)
        self.tbl_claim.setItem(r, 0, no_it)

        combo_model = _mk_combo(self._shop_models or _MODELS)
        self.tbl_claim.setCellWidget(r, 1, combo_model)
        combo_model.currentTextChanged.connect(lambda _, row=r: self._calc_claim_stop(row))
        self.tbl_claim.setCellWidget(r, 2, _mk_combo(self._op_numbers or _OP_ST, popup_w=80))
        self.tbl_claim.setItem(r, 3, _item("", Qt.AlignCenter))
        self.tbl_claim.setItem(r, 4, _item("", Qt.AlignCenter))
        self.tbl_claim.setCellWidget(r, 5, _mk_combo(_SATUAN, popup_w=70))
        self.tbl_claim.setItem(r, 6, _item("", Qt.AlignCenter))
        self.tbl_claim.setItem(r, 7, _item("", Qt.AlignCenter))
        self.tbl_claim.setCellWidget(r, 8, _mk_combo(self._factors, popup_w=100))
        self.tbl_claim.setItem(r, 9,  _item("0", Qt.AlignCenter))
        self.tbl_claim.setItem(r, 10, _item("0", Qt.AlignCenter))
        self.tbl_claim.setCellWidget(r, 11, _mk_combo(["NG", "Pending", "OK"], popup_w=70))

    def _hapus_claim(self):
        r = self.tbl_claim.currentRow()
        if r >= 0:
            self.tbl_claim.removeRow(r)
            for i in range(self.tbl_claim.rowCount()):
                it = self.tbl_claim.item(i, 0)
                if it:
                    it.setText(str(i + 1))

    def _on_claim_item_changed(self, item):
        if item.column() == 4:  # Qty changed → recalc Hour (col 9)
            self._calc_claim_stop(item.row())
        self._hitung_calc_hour()  # Lost (col 10) atau perubahan apapun → update Quality

    def _calc_claim_stop(self, r: int):
        cb_model = self.tbl_claim.cellWidget(r, 1)
        qty_it   = self.tbl_claim.item(r, 4)
        if not cb_model or not qty_it:
            return
        model = cb_model.currentText()
        mhu   = self._shop_model_hours.get(model, 0.0)
        try:
            qty = float(qty_it.text()) if qty_it.text() else 0.0
        except ValueError:
            qty = 0.0
        stop = round(mhu * qty, 4) if mhu > 0 and qty > 0 else 0.0
        self.tbl_claim.blockSignals(True)
        stop_it = self.tbl_claim.item(r, 9)
        if not stop_it:
            stop_it = _item("0", Qt.AlignCenter)
            self.tbl_claim.setItem(r, 9, stop_it)
        stop_it.setText(f"{stop:.4f}" if stop > 0 else "0")
        self.tbl_claim.blockSignals(False)

    def _tambah_linestop(self):
        r = self.tbl_ls.rowCount()
        self.tbl_ls.blockSignals(True)
        self.tbl_ls.insertRow(r)
        self.tbl_ls.setRowHeight(r, 30)

        no_it = _item(str(r + 1), Qt.AlignCenter)
        no_it.setFlags(Qt.ItemIsEnabled)
        self.tbl_ls.setItem(r, 0, no_it)

        self.tbl_ls.setCellWidget(r, 1, _mk_combo(self._shop_models or _MODELS))
        self.tbl_ls.setCellWidget(r, 2, _mk_combo(self._op_numbers or _OP_ST, popup_w=80))
        self.tbl_ls.setItem(r, 3, _item("", Qt.AlignCenter))
        self.tbl_ls.setItem(r, 4, _item("", Qt.AlignCenter))
        self.tbl_ls.setItem(r, 5, _item("", Qt.AlignCenter))
        self.tbl_ls.setCellWidget(r, 6, _mk_combo(self._factors, popup_w=100))

        for col in (7, 8):
            te = QTimeEdit(QTime(0, 0))
            te.setDisplayFormat("HH:mm")
            te.setStyleSheet(
                "QTimeEdit { background: transparent; color: #212121; border: none;"
                " font-size: 11px; padding: 0px 4px; margin: 0px; }"
                "QTimeEdit::up-button, QTimeEdit::down-button { width: 0; }"
            )
            te.timeChanged.connect(self._on_ls_time_changed)
            self.tbl_ls.setCellWidget(r, col, te)

        self.tbl_ls.setItem(r, 9,  _item("0", Qt.AlignCenter))
        self.tbl_ls.setItem(r, 10, _item("0", Qt.AlignCenter))
        self.tbl_ls.blockSignals(False)

    def _hapus_linestop(self):
        r = self.tbl_ls.currentRow()
        if r >= 0:
            self.tbl_ls.removeRow(r)
            for i in range(self.tbl_ls.rowCount()):
                it = self.tbl_ls.item(i, 0)
                if it:
                    it.setText(str(i + 1))
            self._hitung_calc_hour()

    # Auto-kalkulasi Stop/Lost dari Start-End time

    def _on_ls_time_changed(self):
        sender = self.sender()
        for r in range(self.tbl_ls.rowCount()):
            for col in (7, 8):
                if self.tbl_ls.cellWidget(r, col) is sender:
                    self._calc_ls_time(r)
                    self._hitung_calc_hour()
                    return

    def _calc_ls_time(self, r: int):
        start_te = self.tbl_ls.cellWidget(r, 7)
        end_te   = self.tbl_ls.cellWidget(r, 8)
        if not (start_te and end_te):
            return
        s = start_te.time()
        e = end_te.time()
        diff_min = (e.hour() * 60 + e.minute()) - (s.hour() * 60 + s.minute())
        if diff_min < 0:
            diff_min += 1440
        h = round(diff_min / 60, 4)
        self.tbl_ls.blockSignals(True)
        it = self.tbl_ls.item(r, 9)
        if not it:
            it = _item("0", Qt.AlignCenter)
            self.tbl_ls.setItem(r, 9, it)
        it.setText(f"{h:.4f}")
        self.tbl_ls.blockSignals(False)

    def _auto_resize_ls_row(self, item):
        """Row tbl_ls mengembang otomatis kalau teks panjang (wrap)."""
        self.tbl_ls.resizeRowToContents(item.row())
        h = self.tbl_ls.rowHeight(item.row())
        if h < 30:
            self.tbl_ls.setRowHeight(item.row(), 30)

    def _auto_resize_claim_row(self, item):
        """Row tbl_claim mengembang otomatis kalau teks panjang (wrap)."""
        self.tbl_claim.resizeRowToContents(item.row())
        h = self.tbl_claim.rowHeight(item.row())
        if h < 30:
            self.tbl_claim.setRowHeight(item.row(), 30)

    # Auto-fill Hour dari MHU

    def _on_prod_item_changed(self, item):
        col = item.column()
        if col in (1, 2):  # Plan Qty or Act Qty changed
            r = item.row()
            cb = self.tbl_prod.cellWidget(r, 0)
            model = cb.currentText() if cb else ""
            mhu = self._shop_model_hours.get(model, 0.0)
            if mhu > 0:
                try:
                    qty = float(item.text())
                except Exception:
                    qty = 0.0
                self.tbl_prod.blockSignals(True)
                if col == 1:  # Plan Qty → Plan H
                    plh_it = self.tbl_prod.item(r, 3)
                    if not plh_it:
                        plh_it = _item("", Qt.AlignCenter)
                        plh_it.setFlags(Qt.ItemIsEnabled)
                        plh_it.setBackground(QColor("#212121"))
                        plh_it.setForeground(QColor("#606060"))
                        self.tbl_prod.setItem(r, 3, plh_it)
                    plh_it.setText(f"{qty * mhu:.6f}" if qty > 0 else "")
                else:  # col == 2, Act Qty → Act H
                    ach_it = self.tbl_prod.item(r, 4)
                    if not ach_it:
                        ach_it = _item("", Qt.AlignCenter)
                        self.tbl_prod.setItem(r, 4, ach_it)
                    ach_it.setText(f"{qty * mhu:.6f}" if qty > 0 else "")
                self.tbl_prod.blockSignals(False)
        self._hitung_calc_hour()

    def _autofill_mhu_by_model(self, combo_widget):
        for r in range(self.tbl_prod.rowCount()):
            if self.tbl_prod.cellWidget(r, 0) is combo_widget:
                model = combo_widget.currentText()
                mhu = self._shop_model_hours.get(model, 0.0)
                self.tbl_prod.blockSignals(True)
                if mhu > 0:
                    def _qty(col):
                        it = self.tbl_prod.item(r, col)
                        try:
                            return float(it.text()) if it and it.text() else 0.0
                        except Exception:
                            return 0.0
                    plh_it = self.tbl_prod.item(r, 3)
                    if not plh_it:
                        plh_it = _item("", Qt.AlignCenter)
                        plh_it.setFlags(Qt.ItemIsEnabled)
                        plh_it.setBackground(QColor("#212121"))
                        plh_it.setForeground(QColor("#606060"))
                        self.tbl_prod.setItem(r, 3, plh_it)
                    pq = _qty(1)
                    plh_it.setText(f"{pq * mhu:.6f}" if pq > 0 else "")
                    ach_it = self.tbl_prod.item(r, 4)
                    if not ach_it:
                        ach_it = _item("", Qt.AlignCenter)
                        self.tbl_prod.setItem(r, 4, ach_it)
                    aq = _qty(2)
                    ach_it.setText(f"{aq * mhu:.6f}" if aq > 0 else "")
                self.tbl_prod.blockSignals(False)
                self._hitung_calc_hour()
                break

    # Calculation Hour

    def _hitung_calc_hour(self, *_):
        self.tbl_prod.blockSignals(True)
        self.tbl_absen.blockSignals(True)
        self.tbl_ls.blockSignals(True)
        self.tbl_claim.blockSignals(True)

        def _fval(tbl, row, col):
            it = tbl.item(row, col)
            if it:
                try:
                    return float(it.text())
                except Exception:
                    pass
            return 0.0

        process  = sum(_fval(self.tbl_prod,  r, 4)  for r in range(self.tbl_prod.rowCount()))
        absence  = sum(_fval(self.tbl_absen, r, 3)  for r in range(self.tbl_absen.rowCount()))
        linestop = sum(_fval(self.tbl_ls,    r, 10) for r in range(self.tbl_ls.rowCount()))
        quality  = sum(_fval(self.tbl_claim, r, 10) for r in range(self.tbl_claim.rowCount()))
        total    = self._shift_hours
        balance  = total - process - self._prep_h - quality - linestop - absence - self._sholat_h

        self._lbl_process.setText(f"{process:.4f}")
        self._lbl_quality.setText(f"{quality:.4f}")
        self._lbl_linestop.setText(f"{linestop:.4f}")
        self._lbl_absence.setText(f"{absence:.4f}")
        self._lbl_total.setText(f"{total:.4f}")

        ok = abs(balance) < 0.001
        clr = "rgb(80,200,100)" if ok else "rgb(220,80,80)"
        self._lbl_balance.setText(f"{balance:.4f}")
        self._lbl_balance.setStyleSheet(
            f"color: {clr}; font-size:13px; font-weight:bold;"
        )

        self.tbl_prod.blockSignals(False)
        self.tbl_absen.blockSignals(False)
        self.tbl_ls.blockSignals(False)
        self.tbl_claim.blockSignals(False)

    # Reset

    def reset_form(self):
        self.input_tanggal.setDate(QDate.currentDate())
        self.tbl_prod.setRowCount(0)
        self.tbl_absen.setRowCount(0)
        self.tbl_claim.setRowCount(0)
        self.tbl_ls.setRowCount(0)

        self._hitung_calc_hour()

    # Save

    def simpan_laporan(self):
        if self.combo_section.currentData() is None:
            QMessageBox.warning(self, "Validasi", "Pilih section terlebih dahulu.")
            return
        if self.tbl_prod.rowCount() == 0:
            QMessageBox.warning(self, "Validasi", "Tambahkan minimal 1 baris data produksi.")
            return

        bal_text = self._lbl_balance.text()
        try:
            bal_val = float(bal_text.replace("+", ""))
        except Exception:
            bal_val = None

        if bal_val is not None and abs(bal_val) > 0.001:
            if QMessageBox.question(
                self, "Balance Tidak Nol",
                f"BALANCE = {bal_text}\n\nData belum balance. Tetap simpan?",
                QMessageBox.Yes | QMessageBox.No,
            ) != QMessageBox.Yes:
                return

        def _fv(tbl, row, col):
            it = tbl.item(row, col)
            try:
                return float(it.text()) if it else 0.0
            except Exception:
                return 0.0

        # Production
        produksi = []
        for r in range(self.tbl_prod.rowCount()):
            cb = self.tbl_prod.cellWidget(r, 0)
            model = cb.currentText() if cb else ""
            if not model:
                continue
            mhu       = self._shop_model_hours.get(model, 0.0)
            plan_u    = _fv(self.tbl_prod, r, 1)
            actual_u  = _fv(self.tbl_prod, r, 2)
            # Hitung langsung dari raw float — tidak melalui cell text yg sudah di-format
            plan_wh   = plan_u   * mhu if mhu else _fv(self.tbl_prod, r, 3)
            actual_wh = actual_u * mhu if mhu else _fv(self.tbl_prod, r, 4)
            produksi.append({
                "model":        model,
                "plan_unit":    plan_u,
                "actual_unit":  actual_u,
                "plan_whour":   plan_wh,
                "actual_whour": actual_wh,
                "ot_2h":  self._ot_hours == 2.0,
                "ot_3h":  self._ot_hours == 3.0,
                "ot_11h": self._ot_hours == 11.0,
            })

        # Line Stop → catatan (problem_record)
        catatan = []
        for r in range(self.tbl_ls.rowCount()):
            cb_model  = self.tbl_ls.cellWidget(r, 1)
            cb_opst   = self.tbl_ls.cellWidget(r, 2)
            cb_factor = self.tbl_ls.cellWidget(r, 6)
            start_te  = self.tbl_ls.cellWidget(r, 7)
            end_te    = self.tbl_ls.cellWidget(r, 8)
            prob_it   = self.tbl_ls.item(r, 3)
            cause_it  = self.tbl_ls.item(r, 4)
            act_it    = self.tbl_ls.item(r, 5)
            prob = prob_it.text().strip() if prob_it else ""
            if not prob:
                continue
            model_v  = cb_model.currentText()  if cb_model  else ""
            opst_v   = cb_opst.currentText()   if cb_opst   else ""
            factor_v = cb_factor.currentText() if cb_factor else ""
            catatan.append({
                "nomor_ra":   opst_v,
                "kategori":   factor_v,
                "deskripsi":  f"[{model_v}] {prob}" if model_v else prob,
                "penyebab":   cause_it.text().strip() if cause_it else "",
                "tindakan":   act_it.text().strip()   if act_it   else "",
                "pic":        "",
                "down_time":  _fv(self.tbl_ls, r, 9),
                "loss_time":  _fv(self.tbl_ls, r, 10),
                "start_time": start_te.time().toString("HH:mm") if start_te else None,
                "end_time":   end_te.time().toString("HH:mm")   if end_te   else None,
            })

        # Absence
        absen_data = []
        for r in range(self.tbl_absen.rowCount()):
            nama_it = self.tbl_absen.item(r, 1)
            nama = nama_it.text().strip() if nama_it else ""
            if not nama:
                continue
            nik_it  = self.tbl_absen.item(r, 0)
            note_cb = self.tbl_absen.cellWidget(r, 2)
            hr_it   = self.tbl_absen.item(r, 3)
            absen_data.append({
                "no":         r + 1,
                "nama":       nama,
                "nik":        nik_it.text().strip()    if nik_it  else "",
                "shop":       note_cb.currentText()    if note_cb else "",
                "keterangan": hr_it.text().strip()     if hr_it   else "",
            })

        # Inhouse Claim
        claim_data = []
        for r in range(self.tbl_claim.rowCount()):
            item_it = self.tbl_claim.item(r, 3)
            item_v  = item_it.text().strip() if item_it else ""
            if not item_v:
                continue
            cb_model  = self.tbl_claim.cellWidget(r, 1)
            cb_opst   = self.tbl_claim.cellWidget(r, 2)
            cb_sat    = self.tbl_claim.cellWidget(r, 5)
            cb_factor = self.tbl_claim.cellWidget(r, 8)
            cause_it  = self.tbl_claim.item(r, 6)
            act_it    = self.tbl_claim.item(r, 7)
            claim_data.append({
                "tanggal":  self.input_tanggal.date().toString("yyyy-MM-dd"),
                "model":    cb_model.currentText()  if cb_model  else "",
                "op_no_st": cb_opst.currentText()   if cb_opst   else "",
                "item":     item_v,
                "qty":      _fv(self.tbl_claim, r, 4),
                "satuan":   cb_sat.currentText()    if cb_sat    else "",
                "penyebab": cause_it.text().strip() if cause_it  else "",
                "tindakan": act_it.text().strip()   if act_it    else "",
                "faktor":   cb_factor.currentText() if cb_factor else "",
                "stop_hr":  _fv(self.tbl_claim, r, 9),
                "lost_hr":  _fv(self.tbl_claim, r, 10),
                "status":   (self.tbl_claim.cellWidget(r, 11).currentText()
                             if self.tbl_claim.cellWidget(r, 11) else "NG"),
            })

        manpower_data = [
            {"role": "Foreman", "plan": 0, "act": 0},
            {"role": "Ass.For", "plan": 0, "act": 0},
            {"role": "Worker",  "plan": 0, "act": 0},
        ]

        header = {
            "tanggal":     self.input_tanggal.date().toString("yyyy-MM-dd"),
            "shift":       self.combo_shift.currentText(),
            "section":     self.combo_section.currentText(),
            "koordinator": self._user.get("name", ""),
            "approved_by": "",
            "checked_by":  "",
            "plan_whour":   self._shift_hours,
            "actual_whour": self._shift_hours,
        }

        ok, msg = simpan_laporan_harian(
            user_id=self._user["id"],
            header=header,
            catatan=catatan,
            produksi=produksi,
            inhouse_claim=claim_data,
            manpower=manpower_data,
            absen=absen_data,
        )
        if ok:
            self.reset_form()
            QMessageBox.information(self, "Berhasil", msg)
        else:
            QMessageBox.critical(self, "Gagal", msg)

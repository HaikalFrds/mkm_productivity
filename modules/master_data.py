import hashlib

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QDialog, QDialogButtonBox, QLineEdit, QComboBox,
    QAbstractItemView, QTabWidget, QTimeEdit, QScrollArea, QDoubleSpinBox,
)
from PySide6.QtCore import Qt, QTime

from modules.db_laporan import (
    get_all_sections, tambah_section, edit_section, hapus_section,
    get_all_users, tambah_user, reset_password_user, hapus_user,
    get_all_groups, get_all_kategori, tambah_kategori, edit_kategori, hapus_kategori,
    get_all_shifts, tambah_shift, edit_shift, hapus_shift,
    update_shift_working_hour, ensure_shift_columns,
    get_models_by_section, tambah_shop_model, edit_shop_model, hapus_shop_model,
    get_work_centers_by_section, tambah_work_center, edit_work_center, hapus_work_center,
)


# ── Styles ────────────────────────────────────────────────────────────────────

_CARD = "QFrame { background-color: #252525; border-radius: 0px; }"

_TABLE = """
    QTableWidget {
        background-color: #1e1e1e;
        border: 1px solid #303030; border-radius: 0px;
        gridline-color: #303030;
    }
    QTableWidget::item {
        color: #ffffff; padding: 4px 8px;
        background-color: #252525;
        border-bottom: 1px solid #303030;
    }
    QTableWidget::item:selected { background-color: #303030; color: #ffffff; }
    QHeaderView::section {
        background-color: #111111; color: #969696;
        border: none; border-bottom: 1px solid #303030;
        border-right: 1px solid #303030;
        padding: 6px; font-weight: bold; font-size: 10px;
    }
"""

_TAB = """
    QTabWidget::pane { background-color: transparent; border: none; }
    QTabBar::tab {
        background-color: #252525; color: #969696;
        padding: 8px 22px; margin-right: 3px;
        border-top-left-radius: 0px; border-top-right-radius: 0px;
        font-size: 11px; font-weight: bold;
    }
    QTabBar::tab:selected {
        background-color: #2e2e2e; color: #ffffff;
        border-bottom: 2px solid #da291c;
    }
    QTabBar::tab:hover:!selected {
        background-color: #2e2e2e; color: #ffffff;
    }
"""

_BTN_ADD = """
    QPushButton {
        background-color: #da291c; color: #ffffff;
        border: none; border-radius: 0px; font-size: 11px; padding: 0 14px;
    }
    QPushButton:hover { background-color: #b01e0a; }
"""
_BTN_EDIT = """
    QPushButton {
        background-color: rgb(60, 100, 160); color: rgb(180, 210, 255);
        border: none; border-radius: 0px; font-size: 10px;
    }
    QPushButton:hover { background-color: rgb(75, 120, 185); }
"""
_BTN_DEL = """
    QPushButton {
        background-color: rgb(140, 40, 40); color: rgb(255, 180, 180);
        border: none; border-radius: 0px; font-size: 10px;
    }
    QPushButton:hover { background-color: rgb(170, 55, 55); }
"""
_BTN_RESET_PW = """
    QPushButton {
        background-color: rgb(100, 60, 160); color: rgb(220, 200, 255);
        border: none; border-radius: 0px; font-size: 10px;
    }
    QPushButton:hover { background-color: rgb(120, 75, 185); }
"""
_INPUT = """
    QLineEdit {
        background-color: #1e1e1e;
        border: 1px solid #303030; border-radius: 2px;
        padding: 6px 10px; color: #ffffff; font-size: 11px;
        min-height: 30px;
    }
    QLineEdit:focus { border: 1px solid #da291c; }
"""
_COMBO = """
    QComboBox {
        background-color: #1e1e1e; border: 1px solid #303030;
        border-radius: 2px; padding-left: 8px;
        color: #ffffff; font-size: 11px; min-height: 30px;
    }
    QComboBox::drop-down { border: none; width: 24px; }
    QComboBox QAbstractItemView {
        background-color: #252525; color: #ffffff;
        selection-background-color: #303030;
        border: 1px solid #303030;
    }
"""
_DLG_BG    = "background-color: #252525; color: #ffffff;"
_LBL_FIELD = "color: #969696; font-size: 11px;"
_CARD_HDR  = ("color: #ffffff; font-size: 12px; font-weight: bold;"
              " border-left: 3px solid #da291c; padding-left: 8px;")
_TIME_EDIT_STYLE = """
    QTimeEdit {
        background-color: #1e1e1e; border: 1px solid #303030;
        border-radius: 2px; padding: 4px 8px;
        color: #ffffff; font-size: 11px; min-height: 30px;
    }
    QTimeEdit:focus { border: 1px solid #da291c; }
"""


# ── Dialogs ───────────────────────────────────────────────────────────────────

class _SectionDialog(QDialog):
    def __init__(self, parent, nama: str = ""):
        super().__init__(parent)
        self.setWindowTitle("Tambah Shop" if not nama else "Edit Shop")
        self.setFixedWidth(340)
        self.setStyleSheet(_DLG_BG)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 16)
        lay.setSpacing(10)
        lbl = QLabel("Nama Shop"); lbl.setStyleSheet(_LBL_FIELD)
        lay.addWidget(lbl)
        self.input_nama = QLineEdit(nama)
        self.input_nama.setPlaceholderText("Contoh: CAM SHAFT")
        self.input_nama.setStyleSheet(_INPUT)
        lay.addWidget(self.input_nama)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Ok).setText("Simpan")
        btns.button(QDialogButtonBox.Cancel).setText("Batal")
        btns.accepted.connect(self.accept); btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def get_nama(self) -> str:
        return self.input_nama.text().strip()


class _UserDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Tambah User")
        self.setFixedWidth(380)
        self.setStyleSheet(_DLG_BG)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 16)
        lay.setSpacing(8)

        def _f(label, widget):
            l = QLabel(label); l.setStyleSheet(_LBL_FIELD)
            lay.addWidget(l); lay.addWidget(widget)

        self.input_nik = QLineEdit(); self.input_nik.setPlaceholderText("NIK")
        self.input_nik.setStyleSheet(_INPUT); _f("NIK", self.input_nik)
        self.input_nama = QLineEdit(); self.input_nama.setPlaceholderText("Nama Lengkap")
        self.input_nama.setStyleSheet(_INPUT); _f("Nama", self.input_nama)
        self.combo_role = QComboBox(); self.combo_role.addItems(["operator", "admin"])
        self.combo_role.setStyleSheet(_COMBO); _f("Role", self.combo_role)
        self.input_pw = QLineEdit(); self.input_pw.setPlaceholderText("Password")
        self.input_pw.setEchoMode(QLineEdit.Password)
        self.input_pw.setStyleSheet(_INPUT); _f("Password", self.input_pw)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Ok).setText("Tambah")
        btns.button(QDialogButtonBox.Cancel).setText("Batal")
        btns.accepted.connect(self.accept); btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def get_data(self) -> dict:
        return {
            "nik":      self.input_nik.text().strip(),
            "nama":     self.input_nama.text().strip(),
            "role":     self.combo_role.currentText(),
            "password": self.input_pw.text(),
        }


class _ResetPwDialog(QDialog):
    def __init__(self, parent, user_name: str):
        super().__init__(parent)
        self.setWindowTitle(f"Reset Password — {user_name}")
        self.setFixedWidth(340)
        self.setStyleSheet(_DLG_BG)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 16)
        lay.setSpacing(10)
        lbl = QLabel("Password Baru"); lbl.setStyleSheet(_LBL_FIELD)
        lay.addWidget(lbl)
        self.input_pw = QLineEdit()
        self.input_pw.setPlaceholderText("Password baru")
        self.input_pw.setEchoMode(QLineEdit.Password)
        self.input_pw.setStyleSheet(_INPUT)
        lay.addWidget(self.input_pw)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Ok).setText("Reset")
        btns.button(QDialogButtonBox.Cancel).setText("Batal")
        btns.accepted.connect(self.accept); btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def get_password(self) -> str:
        return self.input_pw.text()


class _KategoriDialog(QDialog):
    def __init__(self, parent, groups: list, name: str = "", group_id: int = None):
        super().__init__(parent)
        self.setWindowTitle("Tambah Kategori" if not name else "Edit Kategori")
        self.setFixedWidth(360)
        self.setStyleSheet(_DLG_BG)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 16)
        lay.setSpacing(10)

        def _f(label, widget):
            l = QLabel(label); l.setStyleSheet(_LBL_FIELD)
            lay.addWidget(l); lay.addWidget(widget)

        self.combo_group = QComboBox(); self.combo_group.setStyleSheet(_COMBO)
        for gid, gname in groups:
            self.combo_group.addItem(gname, gid)
        if group_id is not None:
            idx = self.combo_group.findData(group_id)
            if idx >= 0:
                self.combo_group.setCurrentIndex(idx)
        _f("Group", self.combo_group)
        self.input_name = QLineEdit(name)
        self.input_name.setPlaceholderText("Nama kategori")
        self.input_name.setStyleSheet(_INPUT)
        _f("Nama Kategori", self.input_name)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Ok).setText("Simpan")
        btns.button(QDialogButtonBox.Cancel).setText("Batal")
        btns.accepted.connect(self.accept); btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def get_data(self) -> tuple:
        return self.input_name.text().strip(), self.combo_group.currentData()


class _ModelDialog(QDialog):
    """Dialog untuk tambah/edit model dan working hour-nya."""
    def __init__(self, parent, nama: str = "", working_hour: float = 0.0, cycle_time: float = 0.0):
        super().__init__(parent)
        is_edit = bool(nama)
        self.setWindowTitle("Edit Model" if is_edit else "Tambah Model")
        self.setFixedWidth(340)
        self.setStyleSheet(_DLG_BG)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 16)
        lay.setSpacing(10)

        def _f(label, widget):
            l = QLabel(label); l.setStyleSheet(_LBL_FIELD)
            lay.addWidget(l); lay.addWidget(widget)

        self.input_nama = QLineEdit(nama)
        self.input_nama.setPlaceholderText("Contoh: 4G15")
        self.input_nama.setStyleSheet(_INPUT)
        _f("Nama Model", self.input_nama)

        self.input_wh = QDoubleSpinBox()
        self.input_wh.setRange(0.0, 100.0)
        self.input_wh.setDecimals(6)
        self.input_wh.setSingleStep(0.001)
        self.input_wh.setValue(working_hour)
        self.input_wh.setSuffix(" H/unit")
        self.input_wh.setMinimumHeight(32)
        self.input_wh.setStyleSheet(_TIME_EDIT_STYLE)
        _f("Working Hour / MHU (H/unit)", self.input_wh)

        self.input_ct = QDoubleSpinBox()
        self.input_ct.setRange(0.0, 9999.0)
        self.input_ct.setDecimals(1)
        self.input_ct.setSingleStep(1.0)
        self.input_ct.setValue(cycle_time)
        self.input_ct.setSuffix(" s/unit")
        self.input_ct.setMinimumHeight(32)
        self.input_ct.setStyleSheet(_TIME_EDIT_STYLE)
        _f("Cycle Time (s/unit)", self.input_ct)

        lbl_hint = QLabel("MHU: Qty 10 unit × 0.5 H/unit = 5.0 H")
        lbl_hint.setStyleSheet("color: #555555; font-size: 10px;")
        lay.addWidget(lbl_hint)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Ok).setText("Simpan")
        btns.button(QDialogButtonBox.Cancel).setText("Batal")
        btns.accepted.connect(self.accept); btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def get_data(self) -> dict:
        return {
            "nama":         self.input_nama.text().strip(),
            "working_hour": self.input_wh.value(),
            "cycle_time":   self.input_ct.value(),
        }


class _WorkCenterDialog(QDialog):
    def __init__(self, parent, nama: str = ""):
        super().__init__(parent)
        self.setWindowTitle("Edit Work Center" if nama else "Tambah Work Center")
        self.setFixedWidth(340)
        self.setStyleSheet(_DLG_BG)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 16)
        lay.setSpacing(10)
        lbl = QLabel("Nama Work Center"); lbl.setStyleSheet(_LBL_FIELD)
        lay.addWidget(lbl)
        self.input_nama = QLineEdit(nama)
        self.input_nama.setPlaceholderText("Contoh: WC-01")
        self.input_nama.setStyleSheet(_INPUT)
        lay.addWidget(self.input_nama)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Ok).setText("Simpan")
        btns.button(QDialogButtonBox.Cancel).setText("Batal")
        btns.accepted.connect(self.accept); btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def get_nama(self) -> str:
        return self.input_nama.text().strip()


class _ShiftDialog(QDialog):
    def __init__(self, parent, name="", start="07:00", end="15:00", total=8.0,
                 preparation_min=15.0, sholat_min=10.0):
        super().__init__(parent)
        self.setWindowTitle("Tambah Shift" if not name else "Edit Shift")
        self.setFixedWidth(380)
        self.setStyleSheet(_DLG_BG)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 16)
        lay.setSpacing(10)

        def _f(label, widget):
            l = QLabel(label); l.setStyleSheet(_LBL_FIELD)
            lay.addWidget(l); lay.addWidget(widget)

        self.input_name = QLineEdit(name)
        self.input_name.setPlaceholderText("Nama shift")
        self.input_name.setStyleSheet(_INPUT)
        _f("Nama Shift", self.input_name)

        self.time_start = QTimeEdit(QTime.fromString(start, "HH:mm"))
        self.time_start.setDisplayFormat("HH:mm"); self.time_start.setStyleSheet(_TIME_EDIT_STYLE)
        _f("Jam Mulai", self.time_start)

        self.time_end = QTimeEdit(QTime.fromString(end, "HH:mm"))
        self.time_end.setDisplayFormat("HH:mm"); self.time_end.setStyleSheet(_TIME_EDIT_STYLE)
        _f("Jam Selesai", self.time_end)

        self.input_total = QDoubleSpinBox()
        self.input_total.setRange(0.0, 24.0)
        self.input_total.setSingleStep(0.25)
        self.input_total.setDecimals(2)
        self.input_total.setValue(total)
        self.input_total.setMinimumHeight(34)
        self.input_total.setStyleSheet(_TIME_EDIT_STYLE)
        _f("Working Hour (H)", self.input_total)

        # ── Waktu non-produktif ──────────────────────────────────────────────
        lbl_sep = QLabel("─── Waktu Non-Produktif (menit) ───")
        lbl_sep.setStyleSheet("color: #666666; font-size: 10px;")
        lay.addWidget(lbl_sep)

        row_prep = QHBoxLayout()
        lbl_prep = QLabel("Preparation (Meeting + Prep + Cleaning)")
        lbl_prep.setStyleSheet(_LBL_FIELD)
        self.input_prep = QDoubleSpinBox()
        self.input_prep.setRange(0.0, 60.0)
        self.input_prep.setSingleStep(1.0)
        self.input_prep.setDecimals(1)
        self.input_prep.setValue(preparation_min)
        self.input_prep.setSuffix(" menit")
        self.input_prep.setMinimumHeight(32)
        self.input_prep.setStyleSheet(_TIME_EDIT_STYLE)
        lay.addWidget(lbl_prep)
        lay.addWidget(self.input_prep)

        lbl_sholat = QLabel("Sholat / Istirahat Ibadah")
        lbl_sholat.setStyleSheet(_LBL_FIELD)
        self.input_sholat = QDoubleSpinBox()
        self.input_sholat.setRange(0.0, 60.0)
        self.input_sholat.setSingleStep(1.0)
        self.input_sholat.setDecimals(1)
        self.input_sholat.setValue(sholat_min)
        self.input_sholat.setSuffix(" menit")
        self.input_sholat.setMinimumHeight(32)
        self.input_sholat.setStyleSheet(_TIME_EDIT_STYLE)
        lay.addWidget(lbl_sholat)
        lay.addWidget(self.input_sholat)

        # preview
        self._lbl_preview = QLabel()
        self._lbl_preview.setStyleSheet("color: #666666; font-size: 10px;")
        lay.addWidget(self._lbl_preview)
        self.input_prep.valueChanged.connect(self._update_preview)
        self.input_sholat.valueChanged.connect(self._update_preview)
        self._update_preview()

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Ok).setText("Simpan")
        btns.button(QDialogButtonBox.Cancel).setText("Batal")
        btns.accepted.connect(self.accept); btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def _update_preview(self):
        p = self.input_prep.value()
        s = self.input_sholat.value()
        self._lbl_preview.setText(
            f"Preparation = {p/60:.4f} H  |  Sholat = {s/60:.4f} H"
        )

    def get_data(self) -> dict:
        return {
            "name":            self.input_name.text().strip(),
            "start_time":      self.time_start.time().toString("HH:mm"),
            "end_time":        self.time_end.time().toString("HH:mm"),
            "total_hours":     self.input_total.value(),
            "preparation_min": self.input_prep.value(),
            "sholat_min":      self.input_sholat.value(),
        }


# ── Widget ────────────────────────────────────────────────────────────────────

class MasterDataWidget(QWidget):
    def __init__(self, user: dict, parent=None):
        super().__init__(parent)
        self.user = user
        self._setup_ui()

    def showEvent(self, event):
        super().showEvent(event)
        self._load_sections()
        self._load_shop_model_sections()
        self._load_users()
        self._load_kategori()
        self._load_shifts()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(_TAB)
        self.tabs.addTab(self._build_tab_data_master(), "Data Master")
        self.tabs.addTab(self._build_tab_user(),        "User")
        outer.addWidget(self.tabs)

    # ── Tab 1: Data Master (Section + Kategori + Shift dalam scroll) ──────────

    def _build_tab_data_master(self):
        tab = QWidget()
        tab.setStyleSheet("background: transparent;")
        tab_lay = QVBoxLayout(tab)
        tab_lay.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        lay = QVBoxLayout(container)
        lay.setContentsMargins(15, 15, 15, 15)
        lay.setSpacing(16)

        lay.addWidget(self._build_section_card())
        lay.addWidget(_divider())
        lay.addWidget(self._build_shop_model_card())
        lay.addWidget(_divider())
        lay.addWidget(self._build_kategori_card())
        lay.addWidget(_divider())
        lay.addWidget(self._build_shift_card())
        lay.addStretch()

        scroll.setWidget(container)
        tab_lay.addWidget(scroll)
        return tab

    def _build_section_card(self) -> QFrame:
        card = QFrame(); card.setStyleSheet(_CARD)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(16, 14, 16, 16)
        lay.setSpacing(10)

        hdr = QHBoxLayout()
        lbl = QLabel("Shop")
        lbl.setStyleSheet(_CARD_HDR)
        hdr.addWidget(lbl); hdr.addStretch()
        btn = QPushButton("+ Tambah Shop")
        btn.setMinimumSize(130, 30); btn.setStyleSheet(_BTN_ADD)
        btn.clicked.connect(self._tambah_section)
        hdr.addWidget(btn)
        lay.addLayout(hdr)

        self.tabel_section = QTableWidget()
        self.tabel_section.setColumnCount(3)
        self.tabel_section.setHorizontalHeaderLabels(["No", "Nama Shop", "Aksi"])
        hh = self.tabel_section.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.Interactive)
        hh.setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabel_section.verticalHeader().setVisible(False)
        self.tabel_section.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabel_section.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabel_section.setStyleSheet(_TABLE)
        self.tabel_section.setColumnWidth(0, 45)
        self.tabel_section.setColumnWidth(2, 145)
        self.tabel_section.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        lay.addWidget(self.tabel_section)
        return card

    def _build_shop_model_card(self) -> QFrame:
        card = QFrame(); card.setStyleSheet(_CARD)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(16, 14, 16, 16)
        lay.setSpacing(10)

        # ── Header ──────────────────────────────────────────────────────────────
        hdr = QHBoxLayout()
        lbl = QLabel("Model per Shop")
        lbl.setStyleSheet(_CARD_HDR)
        hdr.addWidget(lbl)
        hdr.addStretch()
        btn_add = QPushButton("+ Tambah Model")
        btn_add.setMinimumSize(130, 30); btn_add.setStyleSheet(_BTN_ADD)
        btn_add.clicked.connect(self._tambah_shop_model)
        hdr.addWidget(btn_add)
        lay.addLayout(hdr)

        # ── Shop selector ────────────────────────────────────────────────────────
        sel_row = QHBoxLayout()
        lbl_shop = QLabel("Shop :"); lbl_shop.setStyleSheet(_LBL_FIELD)
        self._combo_shop_model = QComboBox()
        self._combo_shop_model.setMinimumHeight(30)
        self._combo_shop_model.setStyleSheet(_COMBO)
        self._combo_shop_model.currentIndexChanged.connect(self._on_shop_model_changed)
        sel_row.addWidget(lbl_shop)
        sel_row.addWidget(self._combo_shop_model, 1)
        sel_row.addStretch()
        lay.addLayout(sel_row)

        # ── Tabel model ──────────────────────────────────────────────────────────
        self.tabel_model = QTableWidget()
        self.tabel_model.setColumnCount(4)
        self.tabel_model.setHorizontalHeaderLabels(["No", "Model", "H/unit", "Aksi"])
        hh = self.tabel_model.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.Interactive)
        hh.setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabel_model.verticalHeader().setVisible(False)
        self.tabel_model.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabel_model.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabel_model.setStyleSheet(_TABLE)
        self.tabel_model.setColumnWidth(0, 45)
        self.tabel_model.setColumnWidth(2, 90)
        self.tabel_model.setColumnWidth(3, 145)
        self.tabel_model.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        lay.addWidget(self.tabel_model)
        return card

    def _build_kategori_card(self) -> QFrame:
        card = QFrame(); card.setStyleSheet(_CARD)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(16, 14, 16, 16)
        lay.setSpacing(10)

        hdr = QHBoxLayout()
        lbl = QLabel("Kategori Masalah")
        lbl.setStyleSheet(_CARD_HDR)
        hdr.addWidget(lbl); hdr.addStretch()
        btn = QPushButton("+ Tambah Kategori")
        btn.setMinimumSize(145, 30); btn.setStyleSheet(_BTN_ADD)
        btn.clicked.connect(self._tambah_kategori)
        hdr.addWidget(btn)
        lay.addLayout(hdr)

        self.tabel_kategori = QTableWidget()
        self.tabel_kategori.setColumnCount(4)
        self.tabel_kategori.setHorizontalHeaderLabels(["No", "Group", "Nama Kategori", "Aksi"])
        hh = self.tabel_kategori.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.Interactive)
        hh.setSectionResizeMode(2, QHeaderView.Stretch)
        self.tabel_kategori.verticalHeader().setVisible(False)
        self.tabel_kategori.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabel_kategori.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabel_kategori.setStyleSheet(_TABLE)
        self.tabel_kategori.setColumnWidth(0, 45)
        self.tabel_kategori.setColumnWidth(1, 130)
        self.tabel_kategori.setColumnWidth(3, 145)
        self.tabel_kategori.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        lay.addWidget(self.tabel_kategori)
        return card

    def _build_shift_card(self) -> QFrame:
        card = QFrame(); card.setStyleSheet(_CARD)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(16, 14, 16, 16)
        lay.setSpacing(10)

        hdr = QHBoxLayout()
        lbl = QLabel("Shift")
        lbl.setStyleSheet(_CARD_HDR)
        hdr.addWidget(lbl); hdr.addStretch()
        btn = QPushButton("+ Tambah Shift")
        btn.setMinimumSize(120, 30); btn.setStyleSheet(_BTN_ADD)
        btn.clicked.connect(self._tambah_shift)
        hdr.addWidget(btn)
        lay.addLayout(hdr)

        self.tabel_shift = QTableWidget()
        self.tabel_shift.setColumnCount(8)
        self.tabel_shift.setHorizontalHeaderLabels(
            ["No", "Nama Shift", "Mulai", "Selesai", "Working Hour (H)",
             "Preparation (mnt)", "Sholat (mnt)", "Aksi"]
        )
        hh = self.tabel_shift.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.Interactive)
        hh.setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabel_shift.verticalHeader().setVisible(False)
        self.tabel_shift.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabel_shift.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabel_shift.setStyleSheet(_TABLE)
        self.tabel_shift.setColumnWidth(0, 40)
        self.tabel_shift.setColumnWidth(2, 70)
        self.tabel_shift.setColumnWidth(3, 70)
        self.tabel_shift.setColumnWidth(4, 90)
        self.tabel_shift.setColumnWidth(5, 100)
        self.tabel_shift.setColumnWidth(6, 85)
        self.tabel_shift.setColumnWidth(7, 145)
        self.tabel_shift.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        lay.addWidget(self.tabel_shift)
        return card

    # ── Tab 2: User ───────────────────────────────────────────────────────────

    def _build_tab_user(self):
        tab = QWidget()
        tab.setStyleSheet("background: transparent;")
        lay = QVBoxLayout(tab)
        lay.setContentsMargins(15, 15, 15, 15)
        lay.setSpacing(12)

        card_a = QFrame(); card_a.setStyleSheet(_CARD)
        al = QHBoxLayout(card_a); al.setContentsMargins(16, 12, 16, 12)
        lbl_h = QLabel("Daftar User")
        lbl_h.setStyleSheet(_CARD_HDR)
        al.addWidget(lbl_h); al.addStretch()
        btn_add = QPushButton("+ Tambah User")
        btn_add.setMinimumSize(120, 32); btn_add.setStyleSheet(_BTN_ADD)
        btn_add.clicked.connect(self._tambah_user)
        al.addWidget(btn_add)
        lay.addWidget(card_a)

        card_t = QFrame(); card_t.setStyleSheet(_CARD)
        tl = QVBoxLayout(card_t); tl.setContentsMargins(16, 16, 16, 16)
        self.tabel_user = QTableWidget()
        self.tabel_user.setColumnCount(5)
        self.tabel_user.setHorizontalHeaderLabels(["No", "NIK", "Nama", "Role", "Aksi"])
        hh = self.tabel_user.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.Interactive)
        hh.setSectionResizeMode(2, QHeaderView.Stretch)
        self.tabel_user.verticalHeader().setVisible(False)
        self.tabel_user.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabel_user.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabel_user.setStyleSheet(_TABLE)
        self.tabel_user.setColumnWidth(0, 45)
        self.tabel_user.setColumnWidth(1, 110)
        self.tabel_user.setColumnWidth(3, 80)
        self.tabel_user.setColumnWidth(4, 205)
        tl.addWidget(self.tabel_user)
        lay.addWidget(card_t, 1)
        return tab

    # ── Section CRUD ──────────────────────────────────────────────────────────

    def _load_sections(self):
        try:
            rows = get_all_sections()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Gagal memuat section: {e}")
            return
        self.tabel_section.setRowCount(0)
        for i, (sid, sname) in enumerate(rows):
            self.tabel_section.insertRow(i)
            self.tabel_section.setItem(i, 0, _item(str(i + 1), Qt.AlignCenter))
            self.tabel_section.setItem(i, 1, _item(sname))
            self.tabel_section.setCellWidget(i, 2, self._aksi_section(sid, sname))
            self.tabel_section.setRowHeight(i, 38)
        _fit_table(self.tabel_section)

    def _aksi_section(self, sid: int, sname: str) -> QWidget:
        w = QWidget(); w.setStyleSheet("background: transparent;")
        hl = QHBoxLayout(w); hl.setContentsMargins(6, 4, 6, 4); hl.setSpacing(6)
        btn_e = QPushButton("Edit"); btn_e.setFixedSize(55, 26); btn_e.setStyleSheet(_BTN_EDIT)
        btn_e.clicked.connect(lambda _, s=sid, n=sname: self._edit_section(s, n))
        btn_d = QPushButton("Hapus"); btn_d.setFixedSize(55, 26); btn_d.setStyleSheet(_BTN_DEL)
        btn_d.clicked.connect(lambda _, s=sid, n=sname: self._hapus_section(s, n))
        hl.addWidget(btn_e); hl.addWidget(btn_d); hl.addStretch()
        return w

    def _tambah_section(self):
        dlg = _SectionDialog(self)
        if dlg.exec() != QDialog.Accepted:
            return
        nama = dlg.get_nama()
        if not nama:
            QMessageBox.warning(self, "Validasi", "Nama shop tidak boleh kosong.")
            return
        ok, msg = tambah_section(nama)
        if ok:
            self._load_sections()
            QMessageBox.information(self, "Berhasil", msg)
        else:
            QMessageBox.warning(self, "Gagal", msg)

    def _edit_section(self, sid: int, nama_lama: str):
        dlg = _SectionDialog(self, nama_lama)
        if dlg.exec() != QDialog.Accepted:
            return
        nama = dlg.get_nama()
        if not nama:
            QMessageBox.warning(self, "Validasi", "Nama shop tidak boleh kosong.")
            return
        ok, msg = edit_section(sid, nama)
        if ok:
            self._load_sections()
            QMessageBox.information(self, "Berhasil", msg)
        else:
            QMessageBox.warning(self, "Gagal", msg)

    def _hapus_section(self, sid: int, nama: str):
        ans = QMessageBox.question(
            self, "Konfirmasi Hapus", f"Hapus shop '{nama}'?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if ans != QMessageBox.Yes:
            return
        ok, msg = hapus_section(sid)
        if ok:
            self._load_sections()
            QMessageBox.information(self, "Berhasil", msg)
        else:
            QMessageBox.warning(self, "Gagal", msg)

    # ── Shop Model CRUD ───────────────────────────────────────────────────────

    def _load_shop_model_sections(self):
        try:
            rows = get_all_sections()
        except Exception:
            return
        prev = self._combo_shop_model.currentData()
        self._combo_shop_model.blockSignals(True)
        self._combo_shop_model.clear()
        for sid, sname in rows:
            self._combo_shop_model.addItem(sname, sid)
        if prev is not None:
            idx = self._combo_shop_model.findData(prev)
            if idx >= 0:
                self._combo_shop_model.setCurrentIndex(idx)
        self._combo_shop_model.blockSignals(False)
        self._on_shop_model_changed()

    def _on_shop_model_changed(self):
        section_id = self._combo_shop_model.currentData()
        if section_id is None:
            self.tabel_model.setRowCount(0)
            _fit_table(self.tabel_model)
            return
        try:
            models = get_models_by_section(section_id)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Gagal memuat model: {e}")
            return
        self.tabel_model.setRowCount(0)
        for i, m in enumerate(models):
            self.tabel_model.insertRow(i)
            self.tabel_model.setItem(i, 0, _item(str(i + 1), Qt.AlignCenter))
            self.tabel_model.setItem(i, 1, _item(m["model_name"]))
            self.tabel_model.setItem(i, 2, _item(f"{m['working_hour']:.6f}", Qt.AlignCenter))
            self.tabel_model.setCellWidget(i, 3, self._aksi_model(m))
            self.tabel_model.setRowHeight(i, 38)
        _fit_table(self.tabel_model)

    def _aksi_model(self, m: dict) -> QWidget:
        w = QWidget(); w.setStyleSheet("background: transparent;")
        hl = QHBoxLayout(w); hl.setContentsMargins(6, 4, 6, 4); hl.setSpacing(6)
        btn_e = QPushButton("Edit"); btn_e.setFixedSize(55, 26); btn_e.setStyleSheet(_BTN_EDIT)
        btn_e.clicked.connect(lambda _, mm=m: self._edit_shop_model(mm))
        btn_d = QPushButton("Hapus"); btn_d.setFixedSize(55, 26); btn_d.setStyleSheet(_BTN_DEL)
        btn_d.clicked.connect(lambda _, mm=m: self._hapus_shop_model(mm["id"], mm["model_name"]))
        hl.addWidget(btn_e); hl.addWidget(btn_d); hl.addStretch()
        return w

    def _tambah_shop_model(self):
        section_id = self._combo_shop_model.currentData()
        if section_id is None:
            QMessageBox.warning(self, "Pilih Shop", "Pilih shop terlebih dahulu.")
            return
        dlg = _ModelDialog(self)
        if dlg.exec() != QDialog.Accepted:
            return
        d = dlg.get_data()
        if not d["nama"]:
            QMessageBox.warning(self, "Validasi", "Nama model tidak boleh kosong.")
            return
        ok, msg = tambah_shop_model(section_id, d["nama"], d["working_hour"], d["cycle_time"])
        if ok:
            self._on_shop_model_changed()
            QMessageBox.information(self, "Berhasil", msg)
        else:
            QMessageBox.warning(self, "Gagal", msg)

    def _edit_shop_model(self, m: dict):
        dlg = _ModelDialog(self, m["model_name"], m["working_hour"], m.get("cycle_time", 0.0))
        if dlg.exec() != QDialog.Accepted:
            return
        d = dlg.get_data()
        if not d["nama"]:
            QMessageBox.warning(self, "Validasi", "Nama model tidak boleh kosong.")
            return
        ok, msg = edit_shop_model(m["id"], d["nama"], d["working_hour"], d["cycle_time"])
        if ok:
            self._on_shop_model_changed()
        else:
            QMessageBox.warning(self, "Gagal", msg)

    def _hapus_shop_model(self, model_id: int, model_name: str):
        ans = QMessageBox.question(
            self, "Konfirmasi Hapus", f"Hapus model '{model_name}'?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if ans != QMessageBox.Yes:
            return
        ok, msg = hapus_shop_model(model_id)
        if ok:
            self._on_shop_model_changed()
        else:
            QMessageBox.warning(self, "Gagal", msg)

    # ── Work Center CRUD ──────────────────────────────────────────────────────

    def _build_work_center_card(self) -> QFrame:
        card = QFrame(); card.setStyleSheet(_CARD)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(16, 14, 16, 16)
        lay.setSpacing(10)

        hdr = QHBoxLayout()
        lbl = QLabel("Work Center per Shop")
        lbl.setStyleSheet(_CARD_HDR)
        hdr.addWidget(lbl)
        hdr.addStretch()
        btn_add = QPushButton("+ Tambah Work Center")
        btn_add.setMinimumSize(155, 30); btn_add.setStyleSheet(_BTN_ADD)
        btn_add.clicked.connect(self._tambah_work_center)
        hdr.addWidget(btn_add)
        lay.addLayout(hdr)

        sel_row = QHBoxLayout()
        lbl_shop = QLabel("Shop :"); lbl_shop.setStyleSheet(_LBL_FIELD)
        self._combo_wc_shop = QComboBox()
        self._combo_wc_shop.setMinimumHeight(30)
        self._combo_wc_shop.setStyleSheet(_COMBO)
        self._combo_wc_shop.currentIndexChanged.connect(self._on_wc_shop_changed)
        sel_row.addWidget(lbl_shop)
        sel_row.addWidget(self._combo_wc_shop, 1)
        sel_row.addStretch()
        lay.addLayout(sel_row)

        self.tabel_wc = QTableWidget()
        self.tabel_wc.setColumnCount(3)
        self.tabel_wc.setHorizontalHeaderLabels(["No", "Work Center", "Aksi"])
        hh = self.tabel_wc.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.Interactive)
        hh.setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabel_wc.verticalHeader().setVisible(False)
        self.tabel_wc.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabel_wc.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabel_wc.setStyleSheet(_TABLE)
        self.tabel_wc.setColumnWidth(0, 45)
        self.tabel_wc.setColumnWidth(2, 145)
        self.tabel_wc.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        lay.addWidget(self.tabel_wc)
        return card

    def _load_work_center_sections(self):
        try:
            rows = get_all_sections()
        except Exception:
            return
        prev = self._combo_wc_shop.currentData()
        self._combo_wc_shop.blockSignals(True)
        self._combo_wc_shop.clear()
        for sid, sname in rows:
            self._combo_wc_shop.addItem(sname, sid)
        if prev is not None:
            idx = self._combo_wc_shop.findData(prev)
            if idx >= 0:
                self._combo_wc_shop.setCurrentIndex(idx)
        self._combo_wc_shop.blockSignals(False)
        self._on_wc_shop_changed()

    def _on_wc_shop_changed(self):
        section_id = self._combo_wc_shop.currentData()
        if section_id is None:
            self.tabel_wc.setRowCount(0)
            _fit_table(self.tabel_wc)
            return
        try:
            wcs = get_work_centers_by_section(section_id)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Gagal memuat work center: {e}")
            return
        self.tabel_wc.setRowCount(0)
        for i, wc in enumerate(wcs):
            self.tabel_wc.insertRow(i)
            self.tabel_wc.setItem(i, 0, _item(str(i + 1), Qt.AlignCenter))
            self.tabel_wc.setItem(i, 1, _item(wc["name"]))
            self.tabel_wc.setCellWidget(i, 2, self._aksi_wc(wc))
            self.tabel_wc.setRowHeight(i, 38)
        _fit_table(self.tabel_wc)

    def _aksi_wc(self, wc: dict) -> QWidget:
        w = QWidget(); w.setStyleSheet("background: transparent;")
        hl = QHBoxLayout(w); hl.setContentsMargins(6, 4, 6, 4); hl.setSpacing(6)
        btn_e = QPushButton("Edit"); btn_e.setFixedSize(55, 26); btn_e.setStyleSheet(_BTN_EDIT)
        btn_e.clicked.connect(lambda _, x=wc: self._edit_work_center(x))
        btn_d = QPushButton("Hapus"); btn_d.setFixedSize(55, 26); btn_d.setStyleSheet(_BTN_DEL)
        btn_d.clicked.connect(lambda _, x=wc: self._hapus_work_center(x))
        hl.addWidget(btn_e); hl.addWidget(btn_d); hl.addStretch()
        return w

    def _tambah_work_center(self):
        section_id = self._combo_wc_shop.currentData()
        if section_id is None:
            QMessageBox.warning(self, "Pilih Shop", "Pilih shop terlebih dahulu.")
            return
        dlg = _WorkCenterDialog(self)
        if dlg.exec() != QDialog.Accepted:
            return
        nama = dlg.get_nama()
        if not nama:
            QMessageBox.warning(self, "Validasi", "Nama work center tidak boleh kosong.")
            return
        ok, msg = tambah_work_center(section_id, nama)
        if ok:
            self._on_wc_shop_changed()
            QMessageBox.information(self, "Berhasil", msg)
        else:
            QMessageBox.warning(self, "Gagal", msg)

    def _edit_work_center(self, wc: dict):
        dlg = _WorkCenterDialog(self, wc["name"])
        if dlg.exec() != QDialog.Accepted:
            return
        nama = dlg.get_nama()
        if not nama:
            QMessageBox.warning(self, "Validasi", "Nama work center tidak boleh kosong.")
            return
        ok, msg = edit_work_center(wc["id"], nama)
        if ok:
            self._on_wc_shop_changed()
        else:
            QMessageBox.warning(self, "Gagal", msg)

    def _hapus_work_center(self, wc: dict):
        ans = QMessageBox.question(
            self, "Konfirmasi Hapus", f"Hapus work center '{wc['name']}'?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if ans != QMessageBox.Yes:
            return
        ok, msg = hapus_work_center(wc["id"])
        if ok:
            self._on_wc_shop_changed()
        else:
            QMessageBox.warning(self, "Gagal", msg)

    # ── User CRUD ─────────────────────────────────────────────────────────────

    def _load_users(self):
        try:
            users = get_all_users()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Gagal memuat user: {e}")
            return
        self.tabel_user.setRowCount(0)
        for i, u in enumerate(users):
            self.tabel_user.insertRow(i)
            self.tabel_user.setItem(i, 0, _item(str(i + 1), Qt.AlignCenter))
            self.tabel_user.setItem(i, 1, _item(u["nik"]))
            self.tabel_user.setItem(i, 2, _item(u["name"]))
            self.tabel_user.setItem(i, 3, _item(u["role"], Qt.AlignCenter))
            self.tabel_user.setCellWidget(i, 4, self._aksi_user(u))
            self.tabel_user.setRowHeight(i, 38)

    def _aksi_user(self, u: dict) -> QWidget:
        w = QWidget(); w.setStyleSheet("background: transparent;")
        hl = QHBoxLayout(w); hl.setContentsMargins(6, 4, 6, 4); hl.setSpacing(6)
        btn_pw = QPushButton("Reset PW"); btn_pw.setFixedSize(70, 26)
        btn_pw.setStyleSheet(_BTN_RESET_PW)
        btn_pw.clicked.connect(lambda _, uid=u["id"], un=u["name"]: self._reset_pw(uid, un))
        btn_d = QPushButton("Hapus"); btn_d.setFixedSize(55, 26); btn_d.setStyleSheet(_BTN_DEL)
        is_self = u["id"] == self.user.get("id")
        btn_d.setEnabled(not is_self)
        if is_self:
            btn_d.setToolTip("Tidak bisa hapus akun sendiri")
        btn_d.clicked.connect(lambda _, uid=u["id"], un=u["name"]: self._hapus_user(uid, un))
        hl.addWidget(btn_pw); hl.addWidget(btn_d); hl.addStretch()
        return w

    def _tambah_user(self):
        dlg = _UserDialog(self)
        if dlg.exec() != QDialog.Accepted:
            return
        d = dlg.get_data()
        if not d["nik"] or not d["nama"]:
            QMessageBox.warning(self, "Validasi", "NIK dan Nama tidak boleh kosong.")
            return
        if not d["password"]:
            QMessageBox.warning(self, "Validasi", "Password tidak boleh kosong.")
            return
        pw_hash = hashlib.sha256(d["password"].encode()).hexdigest()
        ok, msg = tambah_user(d["nik"], d["nama"], d["role"], pw_hash)
        if ok:
            self._load_users()
            QMessageBox.information(self, "Berhasil", msg)
        else:
            QMessageBox.warning(self, "Gagal", msg)

    def _reset_pw(self, user_id: int, user_name: str):
        dlg = _ResetPwDialog(self, user_name)
        if dlg.exec() != QDialog.Accepted:
            return
        pw = dlg.get_password()
        if not pw:
            QMessageBox.warning(self, "Validasi", "Password tidak boleh kosong.")
            return
        pw_hash = hashlib.sha256(pw.encode()).hexdigest()
        ok, msg = reset_password_user(user_id, pw_hash)
        if ok:
            QMessageBox.information(self, "Berhasil", msg)
        else:
            QMessageBox.warning(self, "Gagal", msg)

    def _hapus_user(self, user_id: int, user_name: str):
        if user_id == self.user.get("id"):
            QMessageBox.warning(self, "Ditolak", "Tidak bisa menghapus akun sendiri.")
            return
        ans = QMessageBox.question(
            self, "Konfirmasi Hapus", f"Hapus user '{user_name}'?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if ans != QMessageBox.Yes:
            return
        ok, msg = hapus_user(user_id)
        if ok:
            self._load_users()
            QMessageBox.information(self, "Berhasil", msg)
        else:
            QMessageBox.warning(self, "Gagal", msg)

    # ── Kategori CRUD ─────────────────────────────────────────────────────────

    def _load_kategori(self):
        try:
            rows   = get_all_kategori()
            groups = get_all_groups()
            self._groups_cache = groups
            self.tabel_kategori.setRowCount(0)
            for i, k in enumerate(rows):
                self.tabel_kategori.insertRow(i)
                self.tabel_kategori.setItem(i, 0, _item(str(i + 1), Qt.AlignCenter))
                self.tabel_kategori.setItem(i, 1, _item(str(k.get("group_name") or "")))
                self.tabel_kategori.setItem(i, 2, _item(str(k.get("name") or "")))
                self.tabel_kategori.setCellWidget(i, 3, self._aksi_kategori(k))
                self.tabel_kategori.setRowHeight(i, 38)
            _fit_table(self.tabel_kategori)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Gagal memuat kategori: {e}")
            return

    def _aksi_kategori(self, k: dict) -> QWidget:
        w = QWidget(); w.setStyleSheet("background: transparent;")
        hl = QHBoxLayout(w); hl.setContentsMargins(6, 4, 6, 4); hl.setSpacing(6)
        btn_e = QPushButton("Edit"); btn_e.setFixedSize(55, 26); btn_e.setStyleSheet(_BTN_EDIT)
        btn_e.clicked.connect(lambda _, kk=k: self._edit_kategori(kk))
        btn_d = QPushButton("Hapus"); btn_d.setFixedSize(55, 26); btn_d.setStyleSheet(_BTN_DEL)
        btn_d.clicked.connect(lambda _, kk=k: self._hapus_kategori(kk))
        hl.addWidget(btn_e); hl.addWidget(btn_d); hl.addStretch()
        return w

    def _tambah_kategori(self):
        groups = getattr(self, "_groups_cache", None) or get_all_groups()
        dlg = _KategoriDialog(self, groups)
        if dlg.exec() != QDialog.Accepted:
            return
        name, group_id = dlg.get_data()
        if not name:
            QMessageBox.warning(self, "Validasi", "Nama kategori tidak boleh kosong.")
            return
        ok, msg = tambah_kategori(name, group_id)
        if ok:
            self._load_kategori()
            QMessageBox.information(self, "Berhasil", msg)
        else:
            QMessageBox.warning(self, "Gagal", msg)

    def _edit_kategori(self, k: dict):
        groups = getattr(self, "_groups_cache", None) or get_all_groups()
        dlg = _KategoriDialog(self, groups, k["name"], k["group_id"])
        if dlg.exec() != QDialog.Accepted:
            return
        name, group_id = dlg.get_data()
        if not name:
            QMessageBox.warning(self, "Validasi", "Nama kategori tidak boleh kosong.")
            return
        ok, msg = edit_kategori(k["id"], name, group_id)
        if ok:
            self._load_kategori()
            QMessageBox.information(self, "Berhasil", msg)
        else:
            QMessageBox.warning(self, "Gagal", msg)

    def _hapus_kategori(self, k: dict):
        ans = QMessageBox.question(
            self, "Konfirmasi Hapus", f"Hapus kategori '{k['name']}'?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if ans != QMessageBox.Yes:
            return
        ok, msg = hapus_kategori(k["id"])
        if ok:
            self._load_kategori()
            QMessageBox.information(self, "Berhasil", msg)
        else:
            QMessageBox.warning(self, "Gagal", msg)

    # ── Shift CRUD ────────────────────────────────────────────────────────────

    def _load_shifts(self):
        try:
            rows = get_all_shifts()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Gagal memuat shift: {e}")
            return
        self.tabel_shift.setRowCount(0)
        for i, s in enumerate(rows):
            self.tabel_shift.insertRow(i)
            self.tabel_shift.setItem(i, 0, _item(str(i + 1), Qt.AlignCenter))
            self.tabel_shift.setItem(i, 1, _item(s["name"]))
            self.tabel_shift.setItem(i, 2, _item(s["start_time"], Qt.AlignCenter))
            self.tabel_shift.setItem(i, 3, _item(s["end_time"],   Qt.AlignCenter))
            self.tabel_shift.setItem(i, 4, _item(f"{s['total_hours']:.1f}", Qt.AlignCenter))
            self.tabel_shift.setItem(i, 5, _item(f"{s['preparation_min']:.0f}", Qt.AlignCenter))
            self.tabel_shift.setItem(i, 6, _item(f"{s['sholat_min']:.0f}", Qt.AlignCenter))
            self.tabel_shift.setCellWidget(i, 7, self._aksi_shift(s))
            self.tabel_shift.setRowHeight(i, 38)
        _fit_table(self.tabel_shift)

    def _aksi_shift(self, s: dict) -> QWidget:
        w = QWidget(); w.setStyleSheet("background: transparent;")
        hl = QHBoxLayout(w); hl.setContentsMargins(6, 4, 6, 4); hl.setSpacing(6)
        btn_e = QPushButton("Edit"); btn_e.setFixedSize(55, 26); btn_e.setStyleSheet(_BTN_EDIT)
        btn_e.clicked.connect(lambda _, ss=s: self._edit_shift(ss))
        btn_d = QPushButton("Hapus"); btn_d.setFixedSize(55, 26); btn_d.setStyleSheet(_BTN_DEL)
        btn_d.clicked.connect(lambda _, ss=s: self._hapus_shift(ss))
        hl.addWidget(btn_e); hl.addWidget(btn_d); hl.addStretch()
        return w

    def _tambah_shift(self):
        dlg = _ShiftDialog(self)
        if dlg.exec() != QDialog.Accepted:
            return
        d = dlg.get_data()
        if not d["name"]:
            QMessageBox.warning(self, "Validasi", "Nama shift tidak boleh kosong.")
            return
        ok, msg = tambah_shift(
            d["name"], d["start_time"], d["end_time"], d["total_hours"],
            d["preparation_min"], d["sholat_min"],
        )
        if ok:
            self._load_shifts()
            QMessageBox.information(self, "Berhasil", msg)
        else:
            QMessageBox.warning(self, "Gagal", msg)

    def _edit_shift(self, s: dict):
        dlg = _ShiftDialog(
            self, s["name"], s["start_time"], s["end_time"], s["total_hours"],
            s.get("preparation_min", 15.0), s.get("sholat_min", 10.0),
        )
        if dlg.exec() != QDialog.Accepted:
            return
        d = dlg.get_data()
        if not d["name"]:
            QMessageBox.warning(self, "Validasi", "Nama shift tidak boleh kosong.")
            return
        ok, msg = edit_shift(
            s["id"], d["name"], d["start_time"], d["end_time"], d["total_hours"],
            d["preparation_min"], d["sholat_min"],
        )
        if ok:
            self._load_shifts()
            QMessageBox.information(self, "Berhasil", msg)
        else:
            QMessageBox.warning(self, "Gagal", msg)

    def _hapus_shift(self, s: dict):
        ans = QMessageBox.question(
            self, "Konfirmasi Hapus", f"Hapus shift '{s['name']}'?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if ans != QMessageBox.Yes:
            return
        ok, msg = hapus_shift(s["id"])
        if ok:
            self._load_shifts()
            QMessageBox.information(self, "Berhasil", msg)
        else:
            QMessageBox.warning(self, "Gagal", msg)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _item(text: str, align=Qt.AlignLeft | Qt.AlignVCenter) -> QTableWidgetItem:
    it = QTableWidgetItem(text)
    it.setTextAlignment(align)
    return it


def _divider() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setFixedHeight(1)
    line.setStyleSheet("background-color: #303030; border: none;")
    return line


def _fit_table(tbl: QTableWidget):
    """Sesuaikan tinggi tabel agar pas dengan jumlah baris tanpa scrollbar."""
    h = tbl.horizontalHeader().height()
    for i in range(tbl.rowCount()):
        h += tbl.rowHeight(i)
    tbl.setFixedHeight(h + 2)

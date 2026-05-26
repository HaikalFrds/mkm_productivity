import hashlib

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QDialog, QDialogButtonBox, QLineEdit, QComboBox,
    QAbstractItemView, QTabWidget, QTimeEdit, QScrollArea,
)
from PySide6.QtCore import Qt, QTime

from modules.db_laporan import (
    get_all_sections, tambah_section, edit_section, hapus_section,
    get_all_users, tambah_user, reset_password_user, hapus_user,
    get_all_groups, get_all_kategori, tambah_kategori, edit_kategori, hapus_kategori,
    get_all_shifts_full, tambah_shift, edit_shift, hapus_shift,
)


# ── Styles ────────────────────────────────────────────────────────────────────

_CARD = "QFrame { background-color: rgb(40, 44, 52); border-radius: 10px; }"

_TABLE = """
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

_TAB = """
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

_BTN_ADD = """
    QPushButton {
        background-color: rgb(25, 90, 50); color: rgb(130, 220, 140);
        border: none; border-radius: 5px; font-size: 11px; padding: 0 14px;
    }
    QPushButton:hover { background-color: rgb(35, 110, 65); }
"""
_BTN_EDIT = """
    QPushButton {
        background-color: rgb(60, 100, 160); color: rgb(180, 210, 255);
        border: none; border-radius: 4px; font-size: 10px;
    }
    QPushButton:hover { background-color: rgb(75, 120, 185); }
"""
_BTN_DEL = """
    QPushButton {
        background-color: rgb(140, 40, 40); color: rgb(255, 180, 180);
        border: none; border-radius: 4px; font-size: 10px;
    }
    QPushButton:hover { background-color: rgb(170, 55, 55); }
"""
_BTN_RESET_PW = """
    QPushButton {
        background-color: rgb(100, 60, 160); color: rgb(220, 200, 255);
        border: none; border-radius: 4px; font-size: 10px;
    }
    QPushButton:hover { background-color: rgb(120, 75, 185); }
"""
_INPUT = """
    QLineEdit {
        background-color: rgb(33, 37, 43);
        border: 1px solid rgb(60, 65, 75); border-radius: 5px;
        padding: 6px 10px; color: rgb(220, 220, 220); font-size: 11px;
        min-height: 30px;
    }
    QLineEdit:focus { border: 1px solid rgb(150, 150, 150); }
"""
_COMBO = """
    QComboBox {
        background-color: rgb(33, 37, 43); border: 1px solid rgb(60, 65, 75);
        border-radius: 5px; padding-left: 8px;
        color: rgb(220, 220, 220); font-size: 11px; min-height: 30px;
    }
    QComboBox::drop-down { border: none; width: 24px; }
    QComboBox QAbstractItemView {
        background-color: rgb(33, 37, 43); color: rgb(220, 220, 220);
        selection-background-color: rgb(60, 65, 75);
        border: 1px solid rgb(60, 65, 75);
    }
"""
_DLG_BG    = "background-color: rgb(33, 37, 43); color: rgb(220, 220, 220);"
_LBL_FIELD = "color: rgb(150, 150, 150); font-size: 11px;"
_TIME_EDIT_STYLE = """
    QTimeEdit {
        background-color: rgb(33, 37, 43); border: 1px solid rgb(60, 65, 75);
        border-radius: 5px; padding: 4px 8px;
        color: rgb(220, 220, 220); font-size: 11px; min-height: 30px;
    }
"""


# ── Dialogs ───────────────────────────────────────────────────────────────────

class _SectionDialog(QDialog):
    def __init__(self, parent, nama: str = ""):
        super().__init__(parent)
        self.setWindowTitle("Tambah Section" if not nama else "Edit Section")
        self.setFixedWidth(340)
        self.setStyleSheet(_DLG_BG)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 16)
        lay.setSpacing(10)
        lbl = QLabel("Nama Section"); lbl.setStyleSheet(_LBL_FIELD)
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


class _ShiftDialog(QDialog):
    def __init__(self, parent, name="", start="07:00", end="15:00", total=8.0):
        super().__init__(parent)
        self.setWindowTitle("Tambah Shift" if not name else "Edit Shift")
        self.setFixedWidth(360)
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
        self.input_total = QLineEdit(str(total))
        self.input_total.setPlaceholderText("Total jam kerja")
        self.input_total.setStyleSheet(_INPUT)
        _f("Total Jam", self.input_total)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Ok).setText("Simpan")
        btns.button(QDialogButtonBox.Cancel).setText("Batal")
        btns.accepted.connect(self.accept); btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def get_data(self) -> dict:
        try:
            total = float(self.input_total.text().strip())
        except ValueError:
            total = 0.0
        return {
            "name":        self.input_name.text().strip(),
            "start_time":  self.time_start.time().toString("HH:mm"),
            "end_time":    self.time_end.time().toString("HH:mm"),
            "total_hours": total,
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
        lbl = QLabel("Section")
        lbl.setStyleSheet("color: white; font-size: 12px; font-weight: bold;")
        hdr.addWidget(lbl); hdr.addStretch()
        btn = QPushButton("+ Tambah Section")
        btn.setMinimumSize(140, 30); btn.setStyleSheet(_BTN_ADD)
        btn.clicked.connect(self._tambah_section)
        hdr.addWidget(btn)
        lay.addLayout(hdr)

        self.tabel_section = QTableWidget()
        self.tabel_section.setColumnCount(3)
        self.tabel_section.setHorizontalHeaderLabels(["No", "Nama Section", "Aksi"])
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

    def _build_kategori_card(self) -> QFrame:
        card = QFrame(); card.setStyleSheet(_CARD)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(16, 14, 16, 16)
        lay.setSpacing(10)

        hdr = QHBoxLayout()
        lbl = QLabel("Kategori Masalah")
        lbl.setStyleSheet("color: white; font-size: 12px; font-weight: bold;")
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
        lbl.setStyleSheet("color: white; font-size: 12px; font-weight: bold;")
        hdr.addWidget(lbl); hdr.addStretch()
        btn = QPushButton("+ Tambah Shift")
        btn.setMinimumSize(120, 30); btn.setStyleSheet(_BTN_ADD)
        btn.clicked.connect(self._tambah_shift)
        hdr.addWidget(btn)
        lay.addLayout(hdr)

        self.tabel_shift = QTableWidget()
        self.tabel_shift.setColumnCount(6)
        self.tabel_shift.setHorizontalHeaderLabels(
            ["No", "Nama Shift", "Mulai", "Selesai", "Total Jam", "Aksi"]
        )
        hh = self.tabel_shift.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.Interactive)
        hh.setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabel_shift.verticalHeader().setVisible(False)
        self.tabel_shift.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabel_shift.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabel_shift.setStyleSheet(_TABLE)
        self.tabel_shift.setColumnWidth(0, 45)
        self.tabel_shift.setColumnWidth(2, 80)
        self.tabel_shift.setColumnWidth(3, 80)
        self.tabel_shift.setColumnWidth(4, 80)
        self.tabel_shift.setColumnWidth(5, 145)
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
        lbl_h.setStyleSheet("color: white; font-size: 12px; font-weight: bold;")
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
            QMessageBox.warning(self, "Validasi", "Nama section tidak boleh kosong.")
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
            QMessageBox.warning(self, "Validasi", "Nama section tidak boleh kosong.")
            return
        ok, msg = edit_section(sid, nama)
        if ok:
            self._load_sections()
            QMessageBox.information(self, "Berhasil", msg)
        else:
            QMessageBox.warning(self, "Gagal", msg)

    def _hapus_section(self, sid: int, nama: str):
        ans = QMessageBox.question(
            self, "Konfirmasi Hapus", f"Hapus section '{nama}'?",
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
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Gagal memuat kategori: {e}")
            return
        self._groups_cache = groups
        self.tabel_kategori.setRowCount(0)
        for i, k in enumerate(rows):
            self.tabel_kategori.insertRow(i)
            self.tabel_kategori.setItem(i, 0, _item(str(i + 1), Qt.AlignCenter))
            self.tabel_kategori.setItem(i, 1, _item(k["group_name"]))
            self.tabel_kategori.setItem(i, 2, _item(k["name"]))
            self.tabel_kategori.setCellWidget(i, 3, self._aksi_kategori(k))
            self.tabel_kategori.setRowHeight(i, 38)
        _fit_table(self.tabel_kategori)

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
            rows = get_all_shifts_full()
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
            self.tabel_shift.setCellWidget(i, 5, self._aksi_shift(s))
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
        ok, msg = tambah_shift(d["name"], d["start_time"], d["end_time"], d["total_hours"])
        if ok:
            self._load_shifts()
            QMessageBox.information(self, "Berhasil", msg)
        else:
            QMessageBox.warning(self, "Gagal", msg)

    def _edit_shift(self, s: dict):
        dlg = _ShiftDialog(self, s["name"], s["start_time"], s["end_time"], s["total_hours"])
        if dlg.exec() != QDialog.Accepted:
            return
        d = dlg.get_data()
        if not d["name"]:
            QMessageBox.warning(self, "Validasi", "Nama shift tidak boleh kosong.")
            return
        ok, msg = edit_shift(s["id"], d["name"], d["start_time"], d["end_time"], d["total_hours"])
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
    line.setStyleSheet("background-color: rgb(55, 60, 70); border: none;")
    return line


def _fit_table(tbl: QTableWidget):
    """Sesuaikan tinggi tabel agar pas dengan jumlah baris tanpa scrollbar."""
    h = tbl.horizontalHeader().height()
    for i in range(tbl.rowCount()):
        h += tbl.rowHeight(i)
    tbl.setFixedHeight(h + 2)

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QLineEdit, QComboBox,
    QPushButton, QDateEdit, QScrollArea, QSizePolicy,
    QTableWidget, QTableWidgetItem, QHeaderView, QTextEdit, QMessageBox,
    QAbstractSpinBox, QSplitter
)
from PySide6.QtCore import Qt, QDate, QSize
from PySide6.QtGui import QTextOption, QColor
from modules.db_laporan import simpan_laporan_harian, get_all_sections


class SectionHeader(QLabel):
    def __init__(self, text):
        super().__init__(text)
        self.setStyleSheet("""
            color: #ffffff;
            font-size: 13px;
            font-weight: bold;
            padding: 8px 0px 4px 0px;
            border-bottom: 1px solid rgb(60, 65, 75);
        """)


class FormLabel(QLabel):
    def __init__(self, text):
        super().__init__(text)
        self.setStyleSheet("color: rgb(150, 150, 150); font-size: 11px;")


class FormInput(QLineEdit):
    def __init__(self, placeholder=""):
        super().__init__()
        self.setPlaceholderText(placeholder)
        self.setMinimumHeight(34)
        self.setStyleSheet("""
            QLineEdit {
                background-color: rgb(33, 37, 43);
                border: 1px solid rgb(60, 65, 75);
                border-radius: 5px;
                padding-left: 10px;
                color: rgb(220, 220, 220);
                font-size: 11px;
            }
            QLineEdit:focus {
                border: 1px solid rgb(150, 150, 150);
            }
        """)


class FormCombo(QComboBox):
    def __init__(self):
        super().__init__()
        self.setMinimumHeight(34)
        self.setStyleSheet("""
            QComboBox {
                background-color: rgb(33, 37, 43);
                border: 1px solid rgb(60, 65, 75);
                border-radius: 5px;
                padding-left: 10px;
                color: rgb(220, 220, 220);
                font-size: 11px;
            }
            QComboBox:focus {
                border: 1px solid rgb(150, 150, 150);
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox QAbstractItemView {
                background-color: rgb(33, 37, 43);
                color: rgb(220, 220, 220);
                selection-background-color: rgb(60, 65, 75);
                border: 1px solid rgb(60, 65, 75);
            }
        """)


class AutoResizeTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(28)
        self.setMaximumHeight(200)
        self.document().setDocumentMargin(0)
        self.setLineWrapMode(QTextEdit.WidgetWidth)
        self.setWordWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setViewportMargins(0, 0, 0, 0)
        self.setContentsMargins(0, 0, 0, 0)
        self.setStyleSheet("""
            QTextEdit {
                background-color: transparent;
                color: rgb(230, 230, 230);
                border: none;
                padding: 0px;
                font-size: 11px;
            }
        """)
        self.setAcceptRichText(False)
        self.document().contentsChanged.connect(self.updateGeometry)

    def sizeHint(self):
        w = self.viewport().width()
        if w <= 0:
            return QSize(0, 28)
        return QSize(w, self.heightForWidth(w))

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        doc = self.document().clone()
        doc.setTextWidth(width)
        return max(28, int(doc.size().height()) + 4)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.updateGeometry()

    def keyPressEvent(self, event):
        super().keyPressEvent(event)


class InputLaporanWidget(QWidget):
    def __init__(self, user: dict, parent=None):
        super().__init__(parent)
        self._user = user
        self._sections_loaded = False
        self.setup_ui()

    def showEvent(self, event):
        super().showEvent(event)
        self._load_sections_once()

    def _load_sections_once(self):
        if self._sections_loaded:
            return
        try:
            sections = get_all_sections()
            self.combo_section.clear()
            for sid, sname in sections:
                self.combo_section.addItem(sname, sid)
            self._sections_loaded = True
        except Exception:
            pass

    def setup_ui(self):
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(12)

        # Card Header Laporan
        card = QFrame()
        card.setStyleSheet("QFrame { background-color: rgb(40, 44, 52); border-radius: 10px; }")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.setSpacing(10)
        card_layout.addWidget(SectionHeader("Informasi Laporan"))

        grid = QGridLayout()
        grid.setSpacing(10)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(3, 1)

        grid.addWidget(FormLabel("Tanggal"), 0, 0)
        self.input_tanggal = QDateEdit()
        self.input_tanggal.setDate(QDate.currentDate())
        self.input_tanggal.setCalendarPopup(True)
        self.input_tanggal.setMinimumHeight(34)
        self.input_tanggal.setStyleSheet("""
            QDateEdit {
                background-color: rgb(33, 37, 43);
                border: 1px solid rgb(60, 65, 75);
                border-radius: 5px;
                padding-left: 10px;
                padding-right: 4px;
                color: rgb(220, 220, 220);
                font-size: 11px;
            }
            QDateEdit:focus { border: 1px solid rgb(150, 150, 150); }
            QDateEdit::drop-down {
                border: none;
                width: 22px;
                subcontrol-origin: padding;
                subcontrol-position: center right;
            }
        """)
        grid.addWidget(self.input_tanggal, 0, 1)

        grid.addWidget(FormLabel("Shift"), 0, 2)
        self.combo_shift = FormCombo()
        self.combo_shift.addItems(["Day Shift", "Night Shift"])
        grid.addWidget(self.combo_shift, 0, 3)

        grid.addWidget(FormLabel("Section"), 1, 0)
        self.combo_section = FormCombo()
        grid.addWidget(self.combo_section, 1, 1)

        grid.addWidget(FormLabel("Koordinator"), 1, 2)
        self.input_koordinator = FormInput("Nama koordinator")
        grid.addWidget(self.input_koordinator, 1, 3)

        grid.addWidget(FormLabel("Disetujui Oleh"), 2, 0)
        self.input_approved = FormInput("Nama yang menyetujui")
        grid.addWidget(self.input_approved, 2, 1)

        grid.addWidget(FormLabel("Diperiksa Oleh"), 2, 2)
        self.input_checked = FormInput("Nama yang memeriksa")
        grid.addWidget(self.input_checked, 2, 3)

        card_layout.addLayout(grid)
        card_layout.addStretch()
        main_layout.addWidget(card)

        # Card Data Produksi & Kalkulasi
        card_dp = QFrame()
        card_dp.setStyleSheet("QFrame { background-color: rgb(40, 44, 52); border-radius: 10px; }")
        card_dp_layout = QVBoxLayout(card_dp)
        card_dp_layout.setContentsMargins(16, 16, 16, 16)
        card_dp_layout.setSpacing(10)
        card_dp_layout.addWidget(SectionHeader("Data Produksi & Kalkulasi"))

        _input_dp_style = """
            QLineEdit {
                background-color: rgb(33, 37, 43);
                border: 1px solid rgb(60, 65, 75);
                border-radius: 5px;
                padding-left: 8px;
                color: rgb(220, 220, 220);
                font-size: 11px;
            }
            QLineEdit:focus { border: 1px solid rgb(150, 150, 150); }
        """
        _calc_dp_style = """
            QLineEdit {
                background-color: rgb(25, 28, 35);
                border: 1px solid rgb(45, 50, 60);
                border-radius: 5px;
                padding-left: 8px;
                color: rgb(150, 155, 170);
                font-size: 11px;
            }
        """
        _dp_lbl_style = "color: rgb(150, 150, 150); font-size: 11px;"

        whour_row = QHBoxLayout()
        whour_row.setSpacing(6)
        lbl_pw = QLabel("Plan W/Hour")
        lbl_pw.setStyleSheet(_dp_lbl_style)
        whour_row.addWidget(lbl_pw)
        self.input_plan_whour = QLineEdit()
        self.input_plan_whour.setPlaceholderText("0.0")
        self.input_plan_whour.setFixedWidth(90)
        self.input_plan_whour.setMinimumHeight(30)
        self.input_plan_whour.setStyleSheet(_input_dp_style)
        whour_row.addWidget(self.input_plan_whour)
        whour_row.addSpacing(16)
        lbl_aw = QLabel("Actual W/Hour")
        lbl_aw.setStyleSheet(_dp_lbl_style)
        whour_row.addWidget(lbl_aw)
        self.input_actual_whour = QLineEdit()
        self.input_actual_whour.setPlaceholderText("0.0")
        self.input_actual_whour.setFixedWidth(90)
        self.input_actual_whour.setMinimumHeight(30)
        self.input_actual_whour.setStyleSheet(_input_dp_style)
        whour_row.addWidget(self.input_actual_whour)
        whour_row.addStretch()
        card_dp_layout.addLayout(whour_row)

        model_toolbar = QHBoxLayout()
        btn_tambah_model = QPushButton("+ Tambah Model")
        btn_tambah_model.setMinimumHeight(28)
        btn_tambah_model.setStyleSheet("""
            QPushButton {
                background-color: rgb(40, 80, 50); color: rgb(150, 210, 160);
                border: none; border-radius: 5px; padding: 0 12px; font-size: 11px;
            }
            QPushButton:hover { background-color: rgb(50, 100, 65); }
        """)
        btn_hapus_model = QPushButton("Hapus Baris")
        btn_hapus_model.setMinimumHeight(28)
        btn_hapus_model.setStyleSheet("""
            QPushButton {
                background-color: rgb(80, 40, 40); color: rgb(200, 150, 150);
                border: none; border-radius: 5px; padding: 0 12px; font-size: 11px;
            }
            QPushButton:hover { background-color: rgb(100, 50, 50); }
        """)
        model_toolbar.addWidget(btn_tambah_model)
        model_toolbar.addWidget(btn_hapus_model)
        model_toolbar.addStretch()
        card_dp_layout.addLayout(model_toolbar)

        self.tabel_produksi = QTableWidget()
        self.tabel_produksi.setColumnCount(7)
        self.tabel_produksi.setHorizontalHeaderLabels([
            "Model", "Plan", "Reg", "2H OT", "3H OT", "11H OT", "Balance",
        ])
        self.tabel_produksi.setFixedHeight(160)
        self.tabel_produksi.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for _c in range(1, 7):
            self.tabel_produksi.horizontalHeader().setSectionResizeMode(_c, QHeaderView.Fixed)
            self.tabel_produksi.setColumnWidth(_c, 50)
        self.tabel_produksi.verticalHeader().setVisible(False)
        self.tabel_produksi.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabel_produksi.setStyleSheet("""
            QTableWidget {
                background-color: rgb(33, 37, 43);
                border: 1px solid rgb(60, 65, 75);
                border-radius: 5px;
                gridline-color: rgb(55, 60, 70);
            }
            QTableWidget::item {
                color: rgb(230, 230, 230);
                padding: 4px;
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
                padding: 4px;
                font-weight: bold;
                font-size: 10px;
            }
        """)
        card_dp_layout.addWidget(self.tabel_produksi)

        def _calc_strip_field():
            f = QLineEdit("—")
            f.setReadOnly(True)
            f.setMinimumHeight(28)
            f.setFixedWidth(110)
            f.setStyleSheet(_calc_dp_style)
            return f

        def _clbl(text):
            lbl = QLabel(text)
            lbl.setStyleSheet(_dp_lbl_style)
            return lbl

        calc_strip = QHBoxLayout()
        calc_strip.setSpacing(4)
        calc_strip.addWidget(_clbl("Cap/Hour"))
        self.calc_cap_hour = _calc_strip_field()
        calc_strip.addWidget(self.calc_cap_hour)
        calc_strip.addSpacing(12)
        calc_strip.addWidget(_clbl("Plan Loss Time"))
        self.calc_plan_loss_time = _calc_strip_field()
        calc_strip.addWidget(self.calc_plan_loss_time)
        calc_strip.addSpacing(12)
        calc_strip.addWidget(_clbl("Actual Loss Time"))
        self.calc_actual_loss_time = _calc_strip_field()
        calc_strip.addWidget(self.calc_actual_loss_time)
        calc_strip.addSpacing(12)
        calc_strip.addWidget(_clbl("Sisa Balance"))
        self.calc_sisa_balance = _calc_strip_field()
        calc_strip.addWidget(self.calc_sisa_balance)
        calc_strip.addStretch()
        card_dp_layout.addLayout(calc_strip)
        card_dp_layout.addStretch()

        btn_tambah_model.clicked.connect(self.tambah_baris_produksi)
        btn_hapus_model.clicked.connect(self.hapus_baris_produksi)
        self.tabel_produksi.itemChanged.connect(self._hitung_kalkulasi)
        self.input_actual_whour.textChanged.connect(self._hitung_kalkulasi)

        _tbl_sm = """
            QTableWidget { background-color: rgb(33,37,43); border: 1px solid rgb(60,65,75);
                border-radius: 5px; gridline-color: rgb(55,60,70); }
            QTableWidget::item { color: rgb(230,230,230); padding: 4px;
                background-color: rgb(38,42,50); border-bottom: 1px solid rgb(55,60,70); }
            QTableWidget::item:selected { background-color: rgb(100,110,125); color: white; }
            QHeaderView::section { background-color: rgb(28,32,40); color: rgb(150,150,150);
                border: none; border-bottom: 1px solid rgb(60,65,75);
                border-right: 1px solid rgb(60,65,75); padding: 4px;
                font-weight: bold; font-size: 10px; }
        """

        # Card Manpower
        card_mp = QFrame()
        card_mp.setStyleSheet("QFrame { background-color: rgb(40,44,52); border-radius: 10px; }")
        card_mp_layout = QVBoxLayout(card_mp)
        card_mp_layout.setContentsMargins(16, 16, 16, 16)
        card_mp_layout.setSpacing(10)
        card_mp_layout.addWidget(SectionHeader("Manpower"))

        self.tabel_mp = QTableWidget(4, 4)
        self.tabel_mp.setHorizontalHeaderLabels(["Deskripsi", "Plan", "Actual", "Balance"])
        self.tabel_mp.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tabel_mp.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.tabel_mp.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.tabel_mp.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.tabel_mp.setColumnWidth(1, 60)
        self.tabel_mp.setColumnWidth(2, 60)
        self.tabel_mp.setColumnWidth(3, 60)
        self.tabel_mp.verticalHeader().setVisible(False)
        self.tabel_mp.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabel_mp.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.tabel_mp.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.tabel_mp.setStyleSheet(_tbl_sm)

        for r, role in enumerate(["Foreman", "Ass.For", "Worker", "Total"]):
            self.tabel_mp.setRowHeight(r, 30)
            desc = QTableWidgetItem(role)
            desc.setFlags(Qt.ItemIsEnabled)
            self.tabel_mp.setItem(r, 0, desc)
            for col in [1, 2]:
                it = QTableWidgetItem("")
                it.setTextAlignment(Qt.AlignCenter)
                if r == 3:
                    it.setFlags(Qt.ItemIsEnabled)
                    it.setText("0")
                self.tabel_mp.setItem(r, col, it)
            bal = QTableWidgetItem("0")
            bal.setFlags(Qt.ItemIsEnabled)
            bal.setTextAlignment(Qt.AlignCenter)
            bal.setForeground(QColor(80, 200, 100))
            self.tabel_mp.setItem(r, 3, bal)

        self.tabel_mp.itemChanged.connect(self._hitung_manpower)
        self.tabel_mp.setFixedHeight(182)
        card_mp_layout.addWidget(self.tabel_mp)
        card_mp_layout.addStretch()

        # Card Absen
        card_absen = QFrame()
        card_absen.setStyleSheet("QFrame { background-color: rgb(40,44,52); border-radius: 10px; }")
        card_absen_layout = QVBoxLayout(card_absen)
        card_absen_layout.setContentsMargins(16, 16, 16, 16)
        card_absen_layout.setSpacing(10)
        card_absen_layout.addWidget(SectionHeader("Absen"))

        toolbar_absen = QHBoxLayout()
        btn_tambah_absen = QPushButton("+ Tambah Baris")
        btn_tambah_absen.setMinimumHeight(28)
        btn_tambah_absen.setStyleSheet("""
            QPushButton { background-color: rgb(50,55,65); color: rgb(200,200,200);
                border: none; border-radius: 5px; padding: 0 12px; font-size: 11px; }
            QPushButton:hover { background-color: rgb(65,70,80); }
        """)
        btn_hapus_absen = QPushButton("Hapus Baris")
        btn_hapus_absen.setMinimumHeight(28)
        btn_hapus_absen.setStyleSheet("""
            QPushButton { background-color: rgb(80,40,40); color: rgb(200,150,150);
                border: none; border-radius: 5px; padding: 0 12px; font-size: 11px; }
            QPushButton:hover { background-color: rgb(100,50,50); }
        """)
        toolbar_absen.addWidget(btn_tambah_absen)
        toolbar_absen.addWidget(btn_hapus_absen)
        toolbar_absen.addStretch()
        card_absen_layout.addLayout(toolbar_absen)

        self.tabel_absen = QTableWidget(0, 5)
        self.tabel_absen.setHorizontalHeaderLabels(["No", "Nama", "NIK", "Shop", "Keterangan"])
        self.tabel_absen.setFixedHeight(210)
        self.tabel_absen.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.tabel_absen.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabel_absen.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.tabel_absen.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.tabel_absen.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.tabel_absen.setColumnWidth(0, 28)
        self.tabel_absen.setColumnWidth(2, 60)
        self.tabel_absen.setColumnWidth(3, 45)
        self.tabel_absen.verticalHeader().setVisible(False)
        self.tabel_absen.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabel_absen.setStyleSheet(_tbl_sm)

        btn_tambah_absen.clicked.connect(self.tambah_baris_absen)
        btn_hapus_absen.clicked.connect(self.hapus_baris_absen)
        card_absen_layout.addWidget(self.tabel_absen)

        left_widget = QWidget()
        left_widget.setStyleSheet("background: transparent;")
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(12)
        left_layout.addWidget(card_mp)
        left_layout.addWidget(card_absen)
        left_layout.addStretch()

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(6)
        splitter.setStyleSheet("QSplitter::handle { background-color: rgb(55, 60, 70); }")
        splitter.addWidget(left_widget)
        splitter.addWidget(card_dp)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        splitter.setSizes([280, 400])
        main_layout.addWidget(splitter)

        # Card Catatan Masalah
        card_masalah = QFrame()
        card_masalah.setStyleSheet("QFrame { background-color: rgb(40, 44, 52); border-radius: 10px; }")
        card_masalah_layout = QVBoxLayout(card_masalah)
        card_masalah_layout.setContentsMargins(16, 16, 16, 16)
        card_masalah_layout.setSpacing(10)
        card_masalah_layout.addWidget(SectionHeader("Catatan Masalah"))

        toolbar = QHBoxLayout()
        btn_tambah_baris = QPushButton("+ Tambah Baris")
        btn_tambah_baris.setMinimumHeight(32)
        btn_tambah_baris.setStyleSheet("""
            QPushButton {
                background-color: rgb(50, 55, 65); color: rgb(200, 200, 200);
                border: none; border-radius: 5px; padding: 0 12px; font-size: 11px;
            }
            QPushButton:hover { background-color: rgb(65, 70, 80); }
        """)
        btn_hapus_baris = QPushButton("Hapus Baris")
        btn_hapus_baris.setMinimumHeight(32)
        btn_hapus_baris.setStyleSheet("""
            QPushButton {
                background-color: rgb(80, 40, 40); color: rgb(200, 150, 150);
                border: none; border-radius: 5px; padding: 0 12px; font-size: 11px;
            }
            QPushButton:hover { background-color: rgb(100, 50, 50); }
        """)
        toolbar.addWidget(btn_tambah_baris)
        toolbar.addWidget(btn_hapus_baris)
        toolbar.addStretch()
        card_masalah_layout.addLayout(toolbar)

        self.tabel_masalah = QTableWidget()
        self.tabel_masalah.setColumnCount(10)
        self.tabel_masalah.setHorizontalHeaderLabels([
            "No. RA", "Kategori", "Deskripsi Masalah",
            "Penyebab", "Tindakan Perbaikan", "PIC",
            "Start", "End", "Down Time (H)", "Loss Time (H)",
        ])
        self.tabel_masalah.setMinimumHeight(200)
        self.tabel_masalah.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabel_masalah.verticalHeader().setVisible(False)
        self.tabel_masalah.verticalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.tabel_masalah.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabel_masalah.setWordWrap(True)
        self.tabel_masalah.setTextElideMode(Qt.ElideNone)
        self.tabel_masalah.setStyleSheet("""
            QTableWidget {
                background-color: rgb(33, 37, 43);
                border: 1px solid rgb(60, 65, 75);
                border-radius: 5px;
                gridline-color: rgb(55, 60, 70);
            }
            QTableWidget::item {
                color: rgb(230, 230, 230);
                padding: 6px;
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
        """)
        card_masalah_layout.addWidget(self.tabel_masalah)
        main_layout.addWidget(card_masalah)

        btn_tambah_baris.clicked.connect(self.tambah_baris_masalah)
        btn_hapus_baris.clicked.connect(self.hapus_baris_masalah)
        self.tabel_masalah.itemChanged.connect(self._hitung_kalkulasi)

        # Card Inhouse Claim
        card_claim = QFrame()
        card_claim.setStyleSheet("QFrame { background-color: rgb(40, 44, 52); border-radius: 10px; }")
        card_claim_layout = QVBoxLayout(card_claim)
        card_claim_layout.setContentsMargins(16, 16, 16, 16)
        card_claim_layout.setSpacing(10)
        card_claim_layout.addWidget(SectionHeader("Data Inhouse Claim"))

        toolbar_claim = QHBoxLayout()
        btn_tambah_claim = QPushButton("+ Tambah Baris")
        btn_tambah_claim.setMinimumHeight(32)
        btn_tambah_claim.setStyleSheet("""
            QPushButton {
                background-color: rgb(50, 55, 65); color: rgb(200, 200, 200);
                border: none; border-radius: 5px; padding: 0 12px; font-size: 11px;
            }
            QPushButton:hover { background-color: rgb(65, 70, 80); }
        """)
        btn_hapus_claim = QPushButton("Hapus Baris")
        btn_hapus_claim.setMinimumHeight(32)
        btn_hapus_claim.setStyleSheet("""
            QPushButton {
                background-color: rgb(80, 40, 40); color: rgb(200, 150, 150);
                border: none; border-radius: 5px; padding: 0 12px; font-size: 11px;
            }
            QPushButton:hover { background-color: rgb(100, 50, 50); }
        """)
        toolbar_claim.addWidget(btn_tambah_claim)
        toolbar_claim.addWidget(btn_hapus_claim)
        toolbar_claim.addStretch()
        card_claim_layout.addLayout(toolbar_claim)

        self.tabel_claim = QTableWidget()
        self.tabel_claim.setColumnCount(13)
        self.tabel_claim.setHorizontalHeaderLabels([
            "No", "Tanggal", "Model", "OP.No/St.", "Item",
            "Qty", "Satuan", "Penyebab", "Tindakan",
            "Faktor", "Stop (Hr)", "Lost (Hr)", "Status",
        ])
        self.tabel_claim.setMinimumHeight(180)
        self.tabel_claim.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabel_claim.verticalHeader().setVisible(False)
        self.tabel_claim.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabel_claim.setStyleSheet("""
            QTableWidget {
                background-color: rgb(33, 37, 43);
                border: 1px solid rgb(60, 65, 75);
                border-radius: 5px;
                gridline-color: rgb(55, 60, 70);
            }
            QTableWidget::item {
                color: rgb(230, 230, 230);
                padding: 4px;
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
                padding: 4px;
                font-weight: bold;
                font-size: 10px;
            }
        """)
        card_claim_layout.addWidget(self.tabel_claim)
        main_layout.addWidget(card_claim)

        btn_tambah_claim.clicked.connect(self.tambah_baris_claim)
        btn_hapus_claim.clicked.connect(self.hapus_baris_claim)

        # Tombol aksi bawah
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_reset = QPushButton("Reset")
        btn_reset.setMinimumSize(100, 36)
        btn_reset.setStyleSheet("""
            QPushButton {
                background-color: rgb(55, 60, 70); color: rgb(190, 190, 190);
                border: none; border-radius: 5px; font-size: 11px;
            }
            QPushButton:hover { background-color: rgb(70, 75, 85); }
        """)
        btn_reset.clicked.connect(self.reset_form)

        btn_simpan = QPushButton("Simpan Laporan")
        btn_simpan.setMinimumSize(140, 36)
        btn_simpan.setStyleSheet("""
            QPushButton {
                background-color: rgb(180, 30, 30); color: #ffffff;
                border: none; border-radius: 5px; font-size: 11px; font-weight: bold;
            }
            QPushButton:hover { background-color: rgb(200, 40, 40); }
            QPushButton:pressed { background-color: rgb(150, 20, 20); }
        """)
        btn_simpan.clicked.connect(self.simpan_laporan)

        btn_layout.addWidget(btn_reset)
        btn_layout.addWidget(btn_simpan)
        main_layout.addLayout(btn_layout)
        main_layout.addStretch()

        scroll.setWidget(container)
        outer_layout.addWidget(scroll)

    def _reset_kalkulasi(self):
        for f in [self.calc_cap_hour, self.calc_plan_loss_time,
                  self.calc_actual_loss_time, self.calc_sisa_balance]:
            f.setText("—")

    def reset_form(self):
        self.input_tanggal.setDate(QDate.currentDate())
        self.combo_shift.setCurrentIndex(0)
        self.combo_section.setCurrentIndex(0)
        self.input_koordinator.clear()
        self.input_approved.clear()
        self.input_checked.clear()
        self.input_plan_whour.clear()
        self.input_actual_whour.clear()
        self.tabel_produksi.setRowCount(0)
        self._reset_kalkulasi()
        self._reset_manpower()
        self._reset_absen()
        self.tabel_masalah.setRowCount(0)
        self.tabel_claim.setRowCount(0)

    def tambah_baris_produksi(self):
        from PySide6.QtWidgets import QComboBox
        row = self.tabel_produksi.rowCount()
        self.tabel_produksi.insertRow(row)
        self.tabel_produksi.setRowHeight(row, 30)

        combo_model = QComboBox()
        combo_model.addItems(["T8", "T8 SHDX", "T6 STD", "T6 Long", "T7"])
        combo_model.setStyleSheet("""
            QComboBox {
                background-color: transparent;
                color: rgb(210, 210, 210);
                border: none;
                padding: 2px 6px;
                font-size: 11px;
            }
            QComboBox::drop-down { border: none; width: 20px; }
            QComboBox QAbstractItemView {
                background-color: rgb(33, 37, 43);
                color: rgb(210, 210, 210);
                selection-background-color: rgb(100, 110, 125);
                border: 1px solid rgb(60, 65, 75);
            }
        """)
        self.tabel_produksi.setCellWidget(row, 0, combo_model)

        for col in range(1, 6):
            item = QTableWidgetItem("")
            item.setTextAlignment(Qt.AlignCenter)
            self.tabel_produksi.setItem(row, col, item)

        bal_item = QTableWidgetItem("0")
        bal_item.setFlags(Qt.ItemIsEnabled)
        bal_item.setTextAlignment(Qt.AlignCenter)
        self.tabel_produksi.setItem(row, 6, bal_item)

    def hapus_baris_produksi(self):
        row = self.tabel_produksi.currentRow()
        if row >= 0:
            self.tabel_produksi.removeRow(row)
            self._hitung_kalkulasi()

    def tambah_baris_masalah(self):
        from PySide6.QtWidgets import QComboBox, QTimeEdit

        row = self.tabel_masalah.rowCount()
        self.tabel_masalah.insertRow(row)

        item_no = QTableWidgetItem("")
        item_no.setTextAlignment(Qt.AlignCenter)
        self.tabel_masalah.setItem(row, 0, item_no)

        combo_kategori = QComboBox()
        combo_kategori.addItems([
            "Machine", "Man", "Material", "Model Change", "Tool",
            "Try Cut", "PLN Off", "Quality", "Preparation",
            "Sholat", "Meeting", "Others",
        ])
        combo_kategori.setStyleSheet("""
            QComboBox {
                background-color: transparent;
                color: rgb(210, 210, 210);
                border: none;
                padding: 2px 6px;
                font-size: 11px;
            }
            QComboBox::drop-down { border: none; width: 20px; }
            QComboBox QAbstractItemView {
                background-color: rgb(33, 37, 43);
                color: rgb(210, 210, 210);
                selection-background-color: rgb(100, 110, 125);
                border: 1px solid rgb(60, 65, 75);
            }
        """)
        combo_kategori.view().setMinimumWidth(130)
        self.tabel_masalah.setCellWidget(row, 1, combo_kategori)

        for col in [2, 3, 4]:
            editor = AutoResizeTextEdit()
            editor.clear()
            editor.document().contentsChanged.connect(
                lambda r=row: self._auto_resize_row(r)
            )
            self.tabel_masalah.setCellWidget(row, col, editor)

        time_style = """
            QTimeEdit {
                background-color: transparent;
                color: rgb(210, 210, 210);
                border: none;
                font-size: 11px;
                padding: 0px;
            }
        """
        time_start = QTimeEdit()
        time_start.setDisplayFormat("HH:mm")
        time_start.setButtonSymbols(QAbstractSpinBox.NoButtons)
        time_start.setStyleSheet(time_style)

        time_end = QTimeEdit()
        time_end.setDisplayFormat("HH:mm")
        time_end.setButtonSymbols(QAbstractSpinBox.NoButtons)
        time_end.setStyleSheet(time_style)

        self.tabel_masalah.setCellWidget(row, 6, time_start)
        self.tabel_masalah.setCellWidget(row, 7, time_end)

        item_downtime = QTableWidgetItem("")
        item_downtime.setTextAlignment(Qt.AlignCenter)
        self.tabel_masalah.setItem(row, 8, item_downtime)

        item_loss = QTableWidgetItem("")
        item_loss.setTextAlignment(Qt.AlignCenter)
        self.tabel_masalah.setItem(row, 9, item_loss)

    def _auto_resize_row(self, row):
        from PySide6.QtCore import QTimer
        QTimer.singleShot(0, lambda r=row: self.tabel_masalah.resizeRowToContents(r))

    def hapus_baris_masalah(self):
        if self.tabel_masalah.selectedItems() or self.tabel_masalah.currentRow() >= 0:
            self.tabel_masalah.removeRow(self.tabel_masalah.currentRow())
            self._hitung_kalkulasi()

    def tambah_baris_claim(self):
        _combo_style = """
            QComboBox {
                background-color: transparent; color: rgb(210, 210, 210);
                border: none; padding: 2px 6px; font-size: 11px;
            }
            QComboBox::drop-down { border: none; width: 20px; }
            QComboBox QAbstractItemView {
                background-color: rgb(33, 37, 43); color: rgb(210, 210, 210);
                selection-background-color: rgb(100, 110, 125);
                border: 1px solid rgb(60, 65, 75);
            }
        """
        row = self.tabel_claim.rowCount()
        self.tabel_claim.insertRow(row)
        self.tabel_claim.setRowHeight(row, 30)

        item_no = QTableWidgetItem(str(row + 1))
        item_no.setFlags(Qt.ItemIsEnabled)
        item_no.setTextAlignment(Qt.AlignCenter)
        self.tabel_claim.setItem(row, 0, item_no)

        tgl = self.input_tanggal.date().toString("dd/MM/yyyy")
        item_tgl = QTableWidgetItem(tgl)
        item_tgl.setFlags(Qt.ItemIsEnabled)
        item_tgl.setTextAlignment(Qt.AlignCenter)
        self.tabel_claim.setItem(row, 1, item_tgl)

        def _mk_combo(items, popup_w=120):
            from PySide6.QtWidgets import QComboBox
            c = QComboBox()
            c.addItems(items)
            c.setStyleSheet(_combo_style)
            c.view().setMinimumWidth(popup_w)
            return c

        self.tabel_claim.setCellWidget(row, 2, _mk_combo(["T8", "T8 SHDX", "T6 STD", "T6 Long", "T7"]))
        self.tabel_claim.setCellWidget(row, 3, _mk_combo(["CM-10", "CM-20", "CM-30", "CM-40", "CM-45", "CM-52", "CM-60", "CM-68"]))

        for col in [4, 5, 6, 7, 8]:
            item = QTableWidgetItem("")
            item.setTextAlignment(Qt.AlignCenter)
            self.tabel_claim.setItem(row, col, item)

        self.tabel_claim.setCellWidget(row, 9, _mk_combo(["Material", "Tool", "Machine", "Man", "Method"]))

        for col in [10, 11]:
            item = QTableWidgetItem("")
            item.setTextAlignment(Qt.AlignCenter)
            self.tabel_claim.setItem(row, col, item)

        self.tabel_claim.setCellWidget(row, 12, _mk_combo(["NG", "PENDING", "OK"], popup_w=90))

    def hapus_baris_claim(self):
        row = self.tabel_claim.currentRow()
        if row >= 0:
            self.tabel_claim.removeRow(row)
            for r in range(self.tabel_claim.rowCount()):
                item = self.tabel_claim.item(r, 0)
                if item:
                    item.setText(str(r + 1))

    def _hitung_manpower(self, *_):
        self.tabel_mp.blockSignals(True)
        total_plan = total_act = 0
        for r in range(3):
            def _iv(col, row=r):
                it = self.tabel_mp.item(row, col)
                if it and it.text().strip():
                    try:
                        return int(float(it.text().strip()))
                    except Exception:
                        pass
                return 0
            plan = _iv(1)
            act = _iv(2)
            blc = act - plan
            bal = self.tabel_mp.item(r, 3)
            if bal:
                bal.setText(str(blc))
                bal.setForeground(QColor(220, 80, 80) if blc < 0 else QColor(80, 200, 100))
            total_plan += plan
            total_act += act
        total_blc = total_act - total_plan
        for col, val in [(1, total_plan), (2, total_act), (3, total_blc)]:
            it = self.tabel_mp.item(3, col)
            if it:
                it.setText(str(val))
                if col == 3:
                    it.setForeground(QColor(220, 80, 80) if total_blc < 0 else QColor(80, 200, 100))
        self.tabel_mp.blockSignals(False)

    def _reset_manpower(self):
        self.tabel_mp.blockSignals(True)
        for r in range(3):
            for col in [1, 2]:
                it = self.tabel_mp.item(r, col)
                if it:
                    it.setText("")
            bal = self.tabel_mp.item(r, 3)
            if bal:
                bal.setText("0")
                bal.setForeground(QColor(80, 200, 100))
        for col in [1, 2, 3]:
            it = self.tabel_mp.item(3, col)
            if it:
                it.setText("0")
                if col == 3:
                    it.setForeground(QColor(80, 200, 100))
        self.tabel_mp.blockSignals(False)

    def _reset_absen(self):
        self.tabel_absen.setRowCount(0)

    def tambah_baris_absen(self):
        row = self.tabel_absen.rowCount()
        self.tabel_absen.insertRow(row)
        self.tabel_absen.setRowHeight(row, 30)
        no_it = QTableWidgetItem(str(row + 1))
        no_it.setFlags(Qt.ItemIsEnabled)
        no_it.setTextAlignment(Qt.AlignCenter)
        self.tabel_absen.setItem(row, 0, no_it)
        for col in [1, 2, 3, 4]:
            self.tabel_absen.setItem(row, col, QTableWidgetItem(""))

    def hapus_baris_absen(self):
        row = self.tabel_absen.currentRow()
        if row >= 0:
            self.tabel_absen.removeRow(row)
            for r in range(self.tabel_absen.rowCount()):
                it = self.tabel_absen.item(r, 0)
                if it:
                    it.setText(str(r + 1))

    def _hitung_kalkulasi(self, *_):
        _calc_base = """
            QLineEdit {
                background-color: rgb(25, 28, 35);
                border: 1px solid rgb(45, 50, 60);
                border-radius: 5px;
                padding-left: 8px;
                font-size: 11px;
            }
        """
        _neutral = _calc_base + "color: rgb(150, 155, 170);"

        self.tabel_produksi.blockSignals(True)
        total_plan = 0.0
        total_balance = 0.0
        for r in range(self.tabel_produksi.rowCount()):
            def _cell(col, row=r):
                it = self.tabel_produksi.item(row, col)
                if it and it.text().strip():
                    try:
                        return float(it.text().strip())
                    except ValueError:
                        pass
                return 0.0

            plan  = _cell(1)
            reg   = _cell(2)
            ot2h  = _cell(3)
            ot3h  = _cell(4)
            ot11h = _cell(5)
            bal   = (reg + ot2h + ot3h + ot11h) - plan

            bal_item = self.tabel_produksi.item(r, 6)
            if bal_item is None:
                bal_item = QTableWidgetItem()
                bal_item.setFlags(Qt.ItemIsEnabled)
                bal_item.setTextAlignment(Qt.AlignCenter)
                self.tabel_produksi.setItem(r, 6, bal_item)
            bal_item.setText(f"{bal:.0f}" if bal == int(bal) else f"{bal:.2f}")
            bal_item.setForeground(
                QColor(220, 80, 80) if bal < 0 else QColor(80, 200, 100)
            )
            total_plan    += plan
            total_balance += bal
        self.tabel_produksi.blockSignals(False)

        try:
            actual_whour = float(self.input_actual_whour.text().strip())
        except ValueError:
            actual_whour = 0.0

        if actual_whour > 0 and total_plan > 0:
            cap_hour = total_plan / actual_whour
            self.calc_cap_hour.setText(f"{cap_hour:.2f} U/H")
            self.calc_cap_hour.setStyleSheet(_neutral)
        else:
            cap_hour = 0.0
            self.calc_cap_hour.setText("—")
            self.calc_cap_hour.setStyleSheet(_neutral)

        if cap_hour > 0 and total_balance != 0:
            plan_loss = total_balance / cap_hour
            color_plt = "color: rgb(220, 80, 80);" if plan_loss < 0 else "color: rgb(80, 200, 100);"
            self.calc_plan_loss_time.setText(f"{plan_loss:+.2f} H")
            self.calc_plan_loss_time.setStyleSheet(_calc_base + color_plt)
        else:
            plan_loss = 0.0
            self.calc_plan_loss_time.setText("—")
            self.calc_plan_loss_time.setStyleSheet(_neutral)

        actual_loss = 0.0
        for r in range(self.tabel_masalah.rowCount()):
            it = self.tabel_masalah.item(r, 9)
            if it and it.text().strip():
                try:
                    actual_loss += float(it.text())
                except ValueError:
                    pass
        self.calc_actual_loss_time.setText(f"{actual_loss:.2f} H")
        self.calc_actual_loss_time.setStyleSheet(_neutral)

        if plan_loss != 0:
            sisa = plan_loss + actual_loss
            color_sisa = "color: rgb(80, 200, 100);" if sisa >= 0 else "color: rgb(220, 80, 80);"
            self.calc_sisa_balance.setText(f"{sisa:+.2f} H")
            self.calc_sisa_balance.setStyleSheet(_calc_base + color_sisa)
        else:
            self.calc_sisa_balance.setText("—")
            self.calc_sisa_balance.setStyleSheet(_neutral)

    def simpan_laporan(self):
        if not self.input_koordinator.text().strip():
            self.input_koordinator.setFocus()
            return

        def _safe_float(text):
            try:
                return float(text.strip()) if text.strip() else None
            except ValueError:
                return None

        header = {
            "tanggal": self.input_tanggal.date().toString("yyyy-MM-dd"),
            "shift": self.combo_shift.currentText(),
            "section": self.combo_section.currentText(),
            "koordinator": self.input_koordinator.text().strip(),
            "approved_by": self.input_approved.text().strip(),
            "checked_by": self.input_checked.text().strip(),
            "plan_whour": _safe_float(self.input_plan_whour.text()),
            "actual_whour": _safe_float(self.input_actual_whour.text()),
        }

        produksi = []
        for row in range(self.tabel_produksi.rowCount()):
            def _pval(col, r=row):
                it = self.tabel_produksi.item(r, col)
                val = it.text().strip() if it else ""
                try:
                    return float(val) if val else 0.0
                except ValueError:
                    return 0.0
            combo_m = self.tabel_produksi.cellWidget(row, 0)
            model_name = combo_m.currentText() if combo_m else ""
            if not model_name:
                continue
            produksi.append({
                "model": model_name,
                "plan_unit": _pval(1),
                "reg_actual": _pval(2),
                "ot_2h": _pval(3),
                "ot_3h": _pval(4),
                "ot_11h": _pval(5),
            })

        catatan = []
        for row in range(self.tabel_masalah.rowCount()):
            nomor_ra = self.tabel_masalah.item(row, 0)
            kategori_w = self.tabel_masalah.cellWidget(row, 1)
            deskripsi_w = self.tabel_masalah.cellWidget(row, 2)
            penyebab_w = self.tabel_masalah.cellWidget(row, 3)
            tindakan_w = self.tabel_masalah.cellWidget(row, 4)
            pic = self.tabel_masalah.item(row, 5)
            loss = self.tabel_masalah.item(row, 9)

            deskripsi = deskripsi_w.toPlainText().strip() if deskripsi_w else ""
            if not deskripsi:
                continue

            try:
                loss_time = float(loss.text()) if loss and loss.text().strip() else 0.0
            except ValueError:
                loss_time = 0.0

            catatan.append({
                "nomor_ra": nomor_ra.text() if nomor_ra else "",
                "kategori": kategori_w.currentText() if kategori_w else "",
                "deskripsi": deskripsi,
                "penyebab": penyebab_w.toPlainText().strip() if penyebab_w else "",
                "tindakan": tindakan_w.toPlainText().strip() if tindakan_w else "",
                "pic": pic.text() if pic else "",
                "loss_time": loss_time,
            })

        catatan_idx = 0
        for row in range(self.tabel_masalah.rowCount()):
            deskripsi_w = self.tabel_masalah.cellWidget(row, 2)
            if not deskripsi_w or not deskripsi_w.toPlainText().strip():
                continue
            start_w = self.tabel_masalah.cellWidget(row, 6)
            end_w = self.tabel_masalah.cellWidget(row, 7)
            st = start_w.time().toString("HH:mm") if start_w else None
            et = end_w.time().toString("HH:mm") if end_w else None
            catatan[catatan_idx]["start_time"] = None if st == "00:00" else st
            catatan[catatan_idx]["end_time"] = None if et == "00:00" else et
            catatan_idx += 1

        def _iv(it):
            val = it.text().strip() if it else ""
            try:
                return int(float(val)) if val else 0
            except Exception:
                return 0

        manpower_data = []
        for r in range(3):
            role_it = self.tabel_mp.item(r, 0)
            manpower_data.append({
                "role": role_it.text() if role_it else "",
                "plan": _iv(self.tabel_mp.item(r, 1)),
                "act":  _iv(self.tabel_mp.item(r, 2)),
            })

        absen_data = []
        for r in range(self.tabel_absen.rowCount()):
            nama_it = self.tabel_absen.item(r, 1)
            nama = nama_it.text().strip() if nama_it else ""
            if not nama:
                continue
            absen_data.append({
                "no": r + 1,
                "nama": nama,
                "nik":  self.tabel_absen.item(r, 2).text().strip() if self.tabel_absen.item(r, 2) else "",
                "shop": self.tabel_absen.item(r, 3).text().strip() if self.tabel_absen.item(r, 3) else "",
                "keterangan": self.tabel_absen.item(r, 4).text().strip() if self.tabel_absen.item(r, 4) else "",
            })

        claim_data = []
        for row in range(self.tabel_claim.rowCount()):
            def _cval(col, r=row):
                it = self.tabel_claim.item(r, col)
                return it.text().strip() if it else ""
            def _cfloat(col, r=row):
                it = self.tabel_claim.item(r, col)
                val = it.text().strip() if it else ""
                try:
                    return float(val) if val else 0.0
                except ValueError:
                    return 0.0
            combo_m  = self.tabel_claim.cellWidget(row, 2)
            combo_op = self.tabel_claim.cellWidget(row, 3)
            combo_f  = self.tabel_claim.cellWidget(row, 9)
            combo_s  = self.tabel_claim.cellWidget(row, 12)
            claim_data.append({
                "tanggal": self.input_tanggal.date().toString("yyyy-MM-dd"),
                "model": combo_m.currentText() if combo_m else "",
                "op_no_st": combo_op.currentText() if combo_op else "",
                "item": _cval(4),
                "qty": _cfloat(5),
                "satuan": _cval(6),
                "penyebab": _cval(7),
                "tindakan": _cval(8),
                "faktor": combo_f.currentText() if combo_f else "",
                "stop_hr": _cfloat(10),
                "lost_hr": _cfloat(11),
                "status": combo_s.currentText() if combo_s else "",
            })

        success, message = simpan_laporan_harian(
            user_id=self._user["id"],
            header=header,
            catatan=catatan,
            produksi=produksi,
            inhouse_claim=claim_data,
            manpower=manpower_data,
            absen=absen_data,
        )

        if success:
            self.reset_form()
            QMessageBox.information(self, "Berhasil", message)
        else:
            QMessageBox.critical(self, "Gagal", message)

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout,
    QLabel, QLineEdit, QPushButton, QFrame
)
from PySide6.QtCore import Qt, Signal, QThread
from controllers.auth_controller import verify_login


class LoginWorker(QThread):
    success = Signal(dict)
    failed  = Signal(str)

    def __init__(self, nik, password):
        super().__init__()
        self.nik      = nik
        self.password = password

    def run(self):
        try:
            user = verify_login(self.nik, self.password)
            if user:
                self.success.emit(user)
            else:
                self.failed.emit("NIK atau password salah.")
        except Exception as e:
            self.failed.emit(str(e))


class LoginWindow(QWidget):
    login_success = Signal(dict)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("MKM Productivity System")
        self.setFixedSize(360, 480)
        self.setWindowFlags(Qt.Window)
        from styles.theme import ThemeManager
        self.setStyleSheet("QWidget { background-color: #F8F9FA; }")
        self.setup_ui()

    def setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setAlignment(Qt.AlignCenter)
        outer.setContentsMargins(0, 0, 0, 0)

        card = QFrame()
        card.setObjectName("login_card")
        card.setFixedWidth(300)
        from styles.theme import ThemeManager
        card.setStyleSheet(
            "QFrame#login_card { background-color: #FFFFFF; border: 1px solid #E5E7EB;"
            " border-bottom: 2px solid #D1D5DB; border-radius: 8px; }"
        )

        layout = QVBoxLayout(card)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(0)

        # Logo
        accent     = ThemeManager.c("accent")
        sub_col    = "#6B7280"
        div_col    = "#D1D5DB"
        lbl_col    = "#6B7280"
        inp_bg     = "#FFFFFF"
        inp_border = "#D1D5DB"
        inp_color  = "#111111"

        title = QLabel("MKM")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            f"color: {accent}; font-size: 32pt; font-weight: bold; letter-spacing: 4px;"
            " background: transparent; border: none;"
        )

        subtitle = QLabel("PRODUCTIVITY SYSTEM")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet(
            f"color: {sub_col}; font-size: 8pt; letter-spacing: 2px;"
            " background: transparent; border: none;"
        )

        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet(f"background-color: {div_col}; border: none; max-height: 1px;")

        # Fields
        _lbl_ss = (
            f"color: {lbl_col}; font-size: 9pt; letter-spacing: 1px;"
            " background: transparent; border: none; padding: 0px;"
        )
        _inp_ss = (
            f"QLineEdit {{ background-color: {inp_bg}; border: 1px solid {inp_border};"
            f" border-radius: 4px; padding: 0 12px; color: {inp_color};"
            f" font-size: 10pt; min-height: 44px; }}"
            f"QLineEdit:focus {{ border: 1.5px solid {accent}; background-color: #FFFAFA; }}"
        )

        lbl_nik = QLabel("NIK")
        lbl_nik.setStyleSheet(_lbl_ss)
        self.input_nik = QLineEdit()
        self.input_nik.setPlaceholderText("Masukkan NIK")
        self.input_nik.setStyleSheet(_inp_ss)

        lbl_pass = QLabel("PASSWORD")
        lbl_pass.setStyleSheet(_lbl_ss)
        self.input_password = QLineEdit()
        self.input_password.setPlaceholderText("Masukkan password")
        self.input_password.setEchoMode(QLineEdit.Password)
        self.input_password.setStyleSheet(_inp_ss)

        # Error
        self.lbl_error = QLabel("")
        self.lbl_error.setStyleSheet(
            f"color: {accent}; font-size: 9pt; background: transparent;"
            " border: none; padding: 0px;"
        )
        self.lbl_error.setAlignment(Qt.AlignCenter)
        self.lbl_error.setWordWrap(True)
        self.lbl_error.hide()

        # Button
        btn_hover    = "#6B1515"
        btn_disabled = "#C8A0A0"
        self.btn_login = QPushButton("MASUK")
        self.btn_login.setObjectName("btn_primary")
        self.btn_login.setStyleSheet(
            f"QPushButton {{ background-color: {accent}; color: #ffffff;"
            " border: none; border-radius: 4px; font-size: 10pt; font-weight: bold;"
            f" letter-spacing: 2px; min-height: 46px; }}"
            f"QPushButton:hover {{ background-color: {btn_hover}; }}"
            f"QPushButton:pressed {{ background-color: #551010; }}"
            f"QPushButton:disabled {{ background-color: {btn_disabled}; color: #BBBBBB; }}"
        )
        self.btn_login.clicked.connect(self.do_login)
        self.input_password.returnPressed.connect(self.do_login)
        self.input_nik.returnPressed.connect(self.do_login)

        # Layout
        layout.addWidget(title)
        layout.addSpacing(4)
        layout.addWidget(subtitle)
        layout.addSpacing(28)
        layout.addWidget(divider)
        layout.addSpacing(24)
        layout.addWidget(lbl_nik)
        layout.addSpacing(6)
        layout.addWidget(self.input_nik)
        layout.addSpacing(16)
        layout.addWidget(lbl_pass)
        layout.addSpacing(6)
        layout.addWidget(self.input_password)
        layout.addSpacing(8)
        layout.addWidget(self.lbl_error)
        layout.addSpacing(20)
        layout.addWidget(self.btn_login)

        outer.addWidget(card)

    def do_login(self):
        nik      = self.input_nik.text().strip()
        password = self.input_password.text().strip()

        if not nik or not password:
            self.lbl_error.setText("NIK dan password tidak boleh kosong.")
            self.lbl_error.show()
            return

        self.btn_login.setText("MEMPROSES...")
        self.btn_login.setEnabled(False)
        self.lbl_error.hide()

        self.worker = LoginWorker(nik, password)
        self.worker.success.connect(self.on_success)
        self.worker.failed.connect(self.on_failed)
        self.worker.start()

    def on_success(self, user):
        self.login_success.emit(user)

    def on_failed(self, message):
        self.lbl_error.setText(message)
        self.lbl_error.show()
        self.btn_login.setText("MASUK")
        self.btn_login.setEnabled(True)

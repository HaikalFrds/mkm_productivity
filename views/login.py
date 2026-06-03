from PySide6.QtWidgets import (
    QWidget, QVBoxLayout,
    QLabel, QLineEdit, QPushButton, QFrame
)
from PySide6.QtCore import Qt, Signal, QThread
from modules.db_auth import verify_login


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
        self.setStyleSheet("QWidget { background-color: #111111; }")
        self.setup_ui()

    def setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setAlignment(Qt.AlignCenter)
        outer.setContentsMargins(0, 0, 0, 0)

        card = QFrame()
        card.setObjectName("login_card")
        card.setFixedWidth(300)
        card.setStyleSheet(
            "QFrame#login_card { background-color: #1a1a1a; border: 1px solid #2e2e2e; border-radius: 0px; }"
        )

        layout = QVBoxLayout(card)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(0)

        # Logo
        title = QLabel("MKM")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            "color: #da291c; font-size: 32pt; font-weight: bold; letter-spacing: 4px;"
            " background: transparent; border: none;"
        )

        subtitle = QLabel("PRODUCTIVITY SYSTEM")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet(
            "color: #555555; font-size: 8pt; letter-spacing: 2px;"
            " background: transparent; border: none;"
        )

        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet("background-color: #2e2e2e; border: none; max-height: 1px;")

        # Fields
        _lbl_ss = (
            "color: #888888; font-size: 9pt; letter-spacing: 1px;"
            " background: transparent; border: none; padding: 0px;"
        )
        _inp_ss = (
            "QLineEdit { background-color: #2a2a2a; border: 1px solid #2e2e2e;"
            " border-radius: 0px; padding: 0 10px; color: #f0f0f0;"
            " font-size: 10pt; min-height: 42px; }"
            "QLineEdit:focus { border: 1px solid #da291c; }"
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
            "color: #da291c; font-size: 9pt; background: transparent;"
            " border: none; padding: 0px;"
        )
        self.lbl_error.setAlignment(Qt.AlignCenter)
        self.lbl_error.setWordWrap(True)
        self.lbl_error.hide()

        # Button
        self.btn_login = QPushButton("MASUK")
        self.btn_login.setObjectName("btn_primary")
        self.btn_login.setStyleSheet(
            "QPushButton { background-color: #da291c; color: #ffffff;"
            " border: none; border-radius: 0px; font-size: 10pt; font-weight: bold;"
            " letter-spacing: 1px; min-height: 44px; }"
            "QPushButton:hover { background-color: #b01e0a; }"
            "QPushButton:disabled { background-color: #3a1a1a; color: #888888; }"
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

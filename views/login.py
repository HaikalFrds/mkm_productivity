import hashlib
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFrame
)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QFont
from modules.db_auth import verify_login


class LoginWorker(QThread):
    success = Signal(dict)
    failed = Signal(str)

    def __init__(self, nik, password):
        super().__init__()
        self.nik = nik
        self.password = password

    def run(self):
        try:
            user = verify_login(self.nik, self.password)
            if user:
                self.success.emit(user)
            else:
                self.failed.emit("NIK atau password salah.")
        except ConnectionError as e:
            self.failed.emit(str(e))


class LoginWindow(QWidget):
    login_success = Signal(dict)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("MKM Productivity System")
        self.setFixedSize(400, 500)
        self.setWindowFlags(Qt.Window)
        self.setup_ui()

    def setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setAlignment(Qt.AlignCenter)

        card = QFrame()
        card.setObjectName("login_card")
        card.setFixedWidth(340)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(16)

        # Title
        title = QLabel("MKM")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 28pt; font-weight: bold; color: #cc0000;")

        subtitle = QLabel("Productivity System")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size: 11pt; color: #888888;")

        # NIK
        lbl_nik = QLabel("NIK")
        lbl_nik.setObjectName("field_label")
        self.input_nik = QLineEdit()
        self.input_nik.setPlaceholderText("Masukkan NIK")

        # Password
        lbl_pass = QLabel("Password")
        lbl_pass.setObjectName("field_label")
        self.input_password = QLineEdit()
        self.input_password.setPlaceholderText("Masukkan password")
        self.input_password.setEchoMode(QLineEdit.Password)

        # Error label
        self.lbl_error = QLabel("")
        self.lbl_error.setStyleSheet("color: #cc4444; font-size: 9pt;")
        self.lbl_error.setAlignment(Qt.AlignCenter)
        self.lbl_error.hide()

        # Login button
        self.btn_login = QPushButton("Masuk")
        self.btn_login.setObjectName("btn_primary")
        self.btn_login.clicked.connect(self.do_login)
        self.input_password.returnPressed.connect(self.do_login)
        self.input_nik.returnPressed.connect(self.do_login)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(8)
        layout.addWidget(lbl_nik)
        layout.addWidget(self.input_nik)
        layout.addWidget(lbl_pass)
        layout.addWidget(self.input_password)
        layout.addWidget(self.lbl_error)
        layout.addSpacing(8)
        layout.addWidget(self.btn_login)

        outer.addWidget(card)

    def do_login(self):
        nik = self.input_nik.text().strip()
        password = self.input_password.text().strip()

        if not nik or not password:
            self.lbl_error.setText("NIK dan password tidak boleh kosong.")
            self.lbl_error.show()
            return

        self.btn_login.setText("Memproses...")
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
        self.btn_login.setText("Masuk")
        self.btn_login.setEnabled(True)
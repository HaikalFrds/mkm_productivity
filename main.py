import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from dotenv import load_dotenv

load_dotenv()
os.environ["QT_FONT_DPI"] = "96"

from views.login import LoginWindow

_login  = None
_window = None


def show_login():
    global _login, _window
    if _window is not None:
        _window.close()
        _window = None
    _login = LoginWindow()
    _login.login_success.connect(on_login_success)
    _login.show()


def on_login_success(user: dict):
    global _login, _window
    from views.main_window import MainWindow
    if _login is not None:
        _login.close()
        _login = None
    _window = MainWindow(user)
    _window.logout_requested.connect(show_login)
    _window.showMaximized()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("assets/icons/icon.ico"))

    with open("styles/style.qss", "r") as f:
        app.setStyleSheet(f.read())

    show_login()
    sys.exit(app.exec())

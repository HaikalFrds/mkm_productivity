import sys
import os
os.environ.setdefault("QT_API", "pyside6")   # harus sebelum qtawesome diimport
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from dotenv import load_dotenv

load_dotenv()
os.environ["QT_FONT_DPI"] = "96"

from database.migrations import initialize_tables
from modules.config import DEV_MODE, DEV_USER, DEV_START_PAGE
from styles.theme import ThemeManager
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

    ThemeManager.load(app)

    initialize_tables()

    if DEV_MODE:
        on_login_success(DEV_USER)
        _window.navigate_to(DEV_START_PAGE)
    else:
        show_login()

    sys.exit(app.exec())

import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from dotenv import load_dotenv

load_dotenv()
os.environ["QT_FONT_DPI"] = "96"

from views.login import LoginWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("assets/icons/icon.ico"))

    # Load stylesheet
    with open("styles/style.qss", "r") as f:
        app.setStyleSheet(f.read())

    def on_login_success(user: dict):
        from views.main_window import MainWindow
        global window
        login.close()
        window = MainWindow(user)
        window.showMaximized()

    login = LoginWindow()
    login.login_success.connect(on_login_success)
    login.show()

    sys.exit(app.exec())
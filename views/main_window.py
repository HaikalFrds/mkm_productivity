import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QFrame, QStackedWidget,
)
from PySide6.QtCore import Qt, QSize, Signal


class MainWindow(QMainWindow):
    logout_requested = Signal()

    def __init__(self, user: dict):
        super().__init__()
        self.user = user
        self.setWindowTitle("MKM Productivity System")
        self.setMinimumSize(900, 600)
        self.setup_ui()
        self.load_pages()
        self.navigate_to("dashboard")

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Sidebar
        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(220)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        # Logo area
        logo_frame = QFrame()
        logo_frame.setStyleSheet("background-color: #FFFFFF; padding: 16px; border-bottom: 1px solid #E8E8E8;")
        logo_layout = QVBoxLayout(logo_frame)
        logo_layout.setContentsMargins(16, 20, 16, 16)
        logo_layout.setSpacing(2)

        lbl_title = QLabel("MKM")
        lbl_title.setObjectName("app_title")
        lbl_title.setStyleSheet("font-size: 18pt; font-weight: bold; color: #da291c; padding: 0;")

        lbl_subtitle = QLabel("Productivity System")
        lbl_subtitle.setObjectName("app_subtitle")
        lbl_subtitle.setStyleSheet("font-size: 9pt; color: #AAAAAA; padding: 0;")

        lbl_user = QLabel(f"👤 {self.user.get('name', self.user.get('nik', ''))}")
        lbl_user.setStyleSheet("font-size: 9pt; color: #888888; padding-top: 8px; background: transparent;")

        logo_layout.addWidget(lbl_title)
        logo_layout.addWidget(lbl_subtitle)
        logo_layout.addWidget(lbl_user)
        sidebar_layout.addWidget(logo_frame)

        # Divider
        div = QFrame()
        div.setFrameShape(QFrame.HLine)
        div.setStyleSheet("background-color: #E8E8E8; max-height: 1px;")
        sidebar_layout.addWidget(div)

        # Nav buttons
        nav_frame = QFrame()
        nav_layout = QVBoxLayout(nav_frame)
        nav_layout.setContentsMargins(0, 8, 0, 8)
        nav_layout.setSpacing(2)

        self.nav_buttons = {}

        self._add_nav_btn(nav_layout, "dashboard", "  Dashboard", "")
        self._add_nav_btn(nav_layout, "input_laporan", "  Input Laporan", "")
        self._add_nav_btn(nav_layout, "riwayat", "  Riwayat Laporan", "")
        self._add_nav_btn(nav_layout, "visualisasi", "  Visualisasi", "")
        self._add_nav_btn(nav_layout, "master_data", "  Master Data", "")

        nav_layout.addStretch()
        sidebar_layout.addWidget(nav_frame, 1)

        # Logout button
        btn_logout = QPushButton("  Logout")
        btn_logout.setObjectName("btn_logout")
        btn_logout.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-top: 1px solid #E8E8E8;
                padding: 12px 16px;
                text-align: left;
                color: #AAAAAA;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #F5F5F5;
                color: #1a1a1a;
            }
        """)
        btn_logout.clicked.connect(self.logout)
        sidebar_layout.addWidget(btn_logout)

        # Content area
        self.content = QFrame()
        self.content.setObjectName("content")
        content_layout = QVBoxLayout(self.content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Top bar
        self.topbar = QFrame()
        self.topbar.setFixedHeight(48)
        self.topbar.setStyleSheet("background-color: #FFFFFF; border-bottom: 1px solid #E0E0E0;")
        topbar_layout = QHBoxLayout(self.topbar)
        topbar_layout.setContentsMargins(20, 0, 20, 0)

        self.lbl_page = QLabel("Dashboard")
        self.lbl_page.setStyleSheet("font-size: 12pt; font-weight: bold; color: #1a1a1a;")
        topbar_layout.addWidget(self.lbl_page)
        topbar_layout.addStretch()

        content_layout.addWidget(self.topbar)

        # Stacked widget
        self.stack = QStackedWidget()
        content_layout.addWidget(self.stack)

        root.addWidget(self.sidebar)
        root.addWidget(self.content, 1)

    def _add_nav_btn(self, layout, page_id, text, icon=""):
        btn = QPushButton(text)
        btn.setObjectName("sidebar")
        btn.setCheckable(False)
        btn.setMinimumHeight(42)
        btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-left: 3px solid transparent;
                padding: 10px 10px 10px 20px;
                text-align: left;
                color: #AAAAAA;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #F5F5F5;
                color: #1a1a1a;
                border-left: 3px solid #E0E0E0;
            }
        """)
        btn.clicked.connect(lambda: self.navigate_to(page_id))
        layout.addWidget(btn)
        self.nav_buttons[page_id] = btn

    def load_pages(self):
        self.pages = {}
        self._page_loaded: set = set()
        for page_id in ["dashboard", "input_laporan", "riwayat", "visualisasi", "master_data"]:
            placeholder = QWidget()
            self.stack.addWidget(placeholder)
            self.pages[page_id] = placeholder

    def _ensure_page_loaded(self, page_id: str):
        if page_id in self._page_loaded:
            return
        if page_id == "dashboard":
            from views.dashboard import DashboardWidget
            widget = DashboardWidget()
        elif page_id == "input_laporan":
            from views.input_laporan import InputLaporanWidget
            widget = InputLaporanWidget(self.user)
        elif page_id == "riwayat":
            from views.riwayat_laporan import RiwayatLaporanWidget
            widget = RiwayatLaporanWidget()
        elif page_id == "visualisasi":
            from views.visualisasi import VisualisasiWidget
            widget = VisualisasiWidget()
        elif page_id == "master_data":
            if self.user.get("role") == "admin":
                from views.master_data import MasterDataWidget
                widget = MasterDataWidget(self.user)
            else:
                widget = QWidget()
                lbl = QLabel("Akses ditolak — halaman ini hanya untuk admin.")
                lbl.setAlignment(Qt.AlignCenter)
                lbl.setStyleSheet("color: #AAAAAA; font-size: 13pt;")
                QVBoxLayout(widget).addWidget(lbl)
                self.nav_buttons["master_data"].setVisible(False)
        else:
            return
        old = self.pages[page_id]
        idx = self.stack.indexOf(old)
        self.stack.removeWidget(old)
        old.deleteLater()
        self.stack.insertWidget(idx, widget)
        self.pages[page_id] = widget
        self._page_loaded.add(page_id)

    def navigate_to(self, page_id: str):
        page_names = {
            "dashboard": "Dashboard",
            "input_laporan": "Input Laporan Harian",
            "riwayat": "Riwayat Laporan",
            "visualisasi": "Visualisasi",
            "master_data": "Master Data",
        }
        self._ensure_page_loaded(page_id)
        if page_id in self.pages:
            self.stack.setCurrentWidget(self.pages[page_id])
            self.lbl_page.setText(page_names.get(page_id, page_id))

        # Update active button style
        for pid, btn in self.nav_buttons.items():
            if pid == page_id:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #F5F5F5;
                        border: none;
                        border-left: 3px solid #da291c;
                        padding: 10px 10px 10px 20px;
                        text-align: left;
                        color: #1a1a1a;
                        font-size: 10pt;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        border: none;
                        border-left: 3px solid transparent;
                        padding: 10px 10px 10px 20px;
                        text-align: left;
                        color: #AAAAAA;
                        font-size: 10pt;
                    }
                    QPushButton:hover {
                        background-color: #F5F5F5;
                        color: #1a1a1a;
                        border-left: 3px solid #E0E0E0;
                    }
                """)

    def logout(self):
        self.logout_requested.emit()
        self.close()
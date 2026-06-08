import os


# Palette definitions
_PALETTES = {
    "light": {
        # Surfaces — Industrial Utilitarian Dark
        "bg_app":      "#111111",
        "bg_sidebar":  "#0d0d0d",
        "bg_logo":     "#111111",
        "bg_card":     "#222222",
        "bg_card2":    "#1a1a1a",
        "bg_input":    "#2a2a2a",
        "bg_btn":      "#2a2a2a",
        "bg_btn_hov":  "#333333",
        "bg_header":   "#111111",
        # Borders
        "border_hi":   "#2e2e2e",
        "border_lo":   "#2e2e2e",
        # Text
        "text_hi":     "#f0f0f0",
        "text_mid":    "#888888",
        "text_lo":     "#555555",
        "text_white":  "#ffffff",
        # Accent
        "accent":      "#da291c",
        "accent_dk":   "#b01e0a",
        "accent_bg":   "#2a1a1a",
        "accent_bdr":  "#4a1a1a",
        # Chart
        "chart_bg":    "#111111",
        "chart_ax":    "#111111",
        "chart_grid":  "#1e1e1e",
        "chart_spine": "#2e2e2e",
        "chart_tick":  "#555555",
        "chart_label": "#888888",
        "chart_line":  "#4a9fd4",
        # Sidebar nav
        "nav_active_bg":   "#252525",
        "nav_active_text": "#ffffff",
        "nav_inactive":    "#555555",
        "nav_hover_bg":    "#252525",
        "nav_hover_bdr":   "#2e2e2e",
        "nav_hover_text":  "#f0f0f0",
    },
}


def fix_calendar(date_edit) -> None:
    """
    Fix QCalendarWidget colors — set stylesheet langsung ke instance-nya
    karena global app QSS tidak bisa override internal calendar widget.
    Panggil setelah setCalendarPopup(True).
    """
    c = _PALETTES["light"]
    cal = date_edit.calendarWidget()
    if cal is None:
        return

    accent    = c["accent"]
    accent_dk = c["accent_dk"]
    sidebar   = c["bg_sidebar"]
    text_hi   = c["text_hi"]
    text_mid  = c["text_mid"]
    border    = c["border_lo"]

    cal.setStyleSheet(f"""
        QCalendarWidget QWidget {{
            background-color: #FFFFFF;
            color: {text_hi};
        }}
        QCalendarWidget QAbstractItemView {{
            background-color: #FFFFFF;
            color: {text_hi};
            selection-background-color: {accent};
            selection-color: #FFFFFF;
            outline: none;
            border: none;
        }}
        QCalendarWidget QAbstractItemView:disabled {{
            color: #C0C0C0;
        }}
        QCalendarWidget QWidget#qt_calendar_navigationbar {{
            background-color: {sidebar};
            padding: 4px 2px;
        }}
        QCalendarWidget QToolButton {{
            background-color: transparent;
            color: {text_hi};
            border: none;
            border-radius: 3px;
            padding: 4px 8px;
            font-weight: bold;
            font-size: 10pt;
            min-width: 0px;
        }}
        QCalendarWidget QToolButton:hover {{
            background-color: {c['bg_btn']};
            color: {text_hi};
        }}
        QCalendarWidget QToolButton::menu-indicator {{
            image: none;
        }}
        QCalendarWidget QHeaderView::section {{
            background-color: #F5F5F5;
            color: {text_mid};
            border: none;
            border-bottom: 1px solid {border};
            padding: 4px 0px;
            font-weight: bold;
            font-size: 8pt;
            text-transform: uppercase;
        }}
        QCalendarWidget QSpinBox {{
            background-color: transparent;
            color: {text_hi};
            border: none;
            font-weight: bold;
            font-size: 10pt;
            selection-background-color: {accent};
            selection-color: #FFFFFF;
        }}
        QCalendarWidget QSpinBox::up-button,
        QCalendarWidget QSpinBox::down-button {{
            width: 0px; height: 0px;
        }}
        QCalendarWidget QMenu {{
            background-color: #FFFFFF;
            color: {text_hi};
            border: 1px solid #C0C0C0;
        }}
        QCalendarWidget QMenu::item:selected {{
            background-color: {accent};
            color: #FFFFFF;
        }}
    """)


class ThemeManager:
    _mode = "light"
    _app  = None

    @classmethod
    def init(cls, app):
        cls._app = app

    @classmethod
    def apply(cls, mode=None):
        qss_path = os.path.join(os.path.dirname(__file__), "light.qss")
        with open(qss_path, "r", encoding="utf-8") as f:
            cls._app.setStyleSheet(f.read())

    @classmethod
    def load(cls, app):
        cls._app = app
        cls.apply()

    @classmethod
    def colors(cls) -> dict:
        """Kembalikan palette dict."""
        return _PALETTES["light"]

    @classmethod
    def c(cls, key: str) -> str:
        """Shortcut: ambil satu warna dari palette."""
        return _PALETTES["light"][key]

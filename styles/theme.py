import os


# Palette definitions
_PALETTES = {
    "light": {
        # Surfaces — Mitsubishi Light (60-30-10)
        "bg_app":      "#F8F9FA",   # 60% — off-white canvas
        "bg_sidebar":  "#FFFFFF",   # sidebar putih bersih
        "bg_logo":     "#FFFFFF",
        "bg_card":     "#FFFFFF",   # card putih
        "bg_card2":    "#F9FAFB",
        "bg_input":    "#FFFFFF",
        "bg_btn":      "#F3F4F6",   # button abu-abu terang
        "bg_btn_hov":  "#D1D5DB",
        "bg_header":   "#F8F9FA",
        # Borders — 30% structural grey
        "border_hi":   "#D1D5DB",
        "border_lo":   "#E5E7EB",
        # Text
        "text_hi":     "#212121",   # primary text — Dark Charcoal
        "text_mid":    "#6B7280",   # secondary text
        "text_lo":     "#9CA3AF",   # muted / placeholder
        "text_white":  "#FFFFFF",
        # Accent — 10% Mitsubishi Red
        "accent":      "#E60012",
        "accent_dk":   "#C0000F",
        "accent_bg":   "#FFF0F0",   # light red bg untuk hover states
        "accent_bdr":  "#FFCDD2",
        # Status colors (pabrik: OK / Warning / NG)
        "status_ok":   "#28A745",   # Aman / Target tercapai
        "status_warn": "#FFC107",   # Warning / Pending
        "status_ng":   "#E60012",   # NG / Loss Time kritis
        # Chart
        "chart_bg":    "#FFFFFF",
        "chart_ax":    "#F8F9FA",
        "chart_grid":  "#F3F4F6",
        "chart_spine": "#D1D5DB",
        "chart_tick":  "#9CA3AF",
        "chart_label": "#6B7280",
        "chart_line":  "#1a6fa8",
        # Sidebar nav
        "nav_active_bg":   "#F8F9FA",
        "nav_active_text": "#212121",
        "nav_inactive":    "#9CA3AF",
        "nav_hover_bg":    "#F8F9FA",
        "nav_hover_bdr":   "#D1D5DB",
        "nav_hover_text":  "#212121",
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
            background-color: #F8F9FA;
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

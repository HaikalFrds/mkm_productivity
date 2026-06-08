"""
modules/icons.py
Centralized icon factory menggunakan qtawesome (FontAwesome 5).
Import modul ini setelah QT_API sudah di-set di main.py.
"""
import os
os.environ.setdefault("QT_API", "pyside6")

import qtawesome as qta
from PySide6.QtCore import QSize

# ── Ukuran standar ────────────────────────────────────────────────────────────
BTN_ICON_SIZE  = QSize(13, 13)   # tombol dengan teks (Add, Del, Edit, Hapus)
NAV_ICON_SIZE  = QSize(10, 10)   # tombol navigasi kecil (prev/next hari)
TOOL_ICON_SIZE = QSize(14, 14)   # toolbar / standalone

# ── Palet warna ───────────────────────────────────────────────────────────────
_GREEN  = "#2e7d32"
_RED    = "#c62828"
_GRAY   = "#6B7280"
_WHITE  = "#FFFFFF"
_DARK   = "#212121"
_ORANGE = "#e67e22"


# ── Icon factories ────────────────────────────────────────────────────────────

def ic_add():
    return qta.icon("fa5s.plus",         color=_GREEN)

def ic_del():
    return qta.icon("fa5s.times",        color=_RED)

def ic_view():
    return qta.icon("fa5s.eye",          color=_GRAY)

def ic_edit():
    return qta.icon("fa5s.pen",          color=_GRAY)

def ic_trash():
    return qta.icon("fa5s.trash-alt",    color=_RED)

def ic_prev():
    return qta.icon("fa5s.chevron-left", color=_GRAY)

def ic_next():
    return qta.icon("fa5s.chevron-right",color=_GRAY)

def ic_refresh():
    return qta.icon("fa5s.sync-alt",     color=_GRAY)

def ic_save():
    return qta.icon("fa5s.save",         color=_WHITE)

def ic_reset():
    return qta.icon("fa5s.undo",         color=_GRAY)

def ic_chart():
    return qta.icon("fa5s.chart-bar",    color=_GRAY)

def ic_filter():
    return qta.icon("fa5s.filter",       color=_GRAY)

def ic_search():
    return qta.icon("fa5s.search",       color=_GRAY)

def ic_close():
    return qta.icon("fa5s.times",        color=_GRAY)

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame,
    QLabel, QComboBox, QPushButton, QSizePolicy,
)
from PySide6.QtCore import Qt, QDate

import matplotlib
matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.ticker as mticker

from modules.db_laporan import get_all_sections, get_loss_time_per_bulan


# ── Styles ────────────────────────────────────────────────────────────────────

# (prev: #252525 card, #1e1e1e input, #303030 border)
_CARD_STYLE = "QFrame { background-color: #222222; border-radius: 0px; }"

_COMBO_STYLE = """
    QComboBox {
        background-color: #2a2a2a; border: 1px solid #2e2e2e;
        border-radius: 0px; padding-left: 8px;
        color: #f0f0f0; font-size: 11px; min-height: 30px;
    }
    QComboBox:focus { border: 1px solid #da291c; }
    QComboBox::drop-down { border: none; width: 24px; }
    QComboBox QAbstractItemView {
        background-color: #1a1a1a; color: #f0f0f0;
        selection-background-color: #2a2a2a;
        border: 1px solid #2e2e2e;
    }
"""

_BTN_TAMPIL = """
    QPushButton {
        background-color: #da291c; color: #ffffff;
        border: none; border-radius: 0px; font-size: 11px; padding: 0 16px;
        min-height: 30px; letter-spacing: 1px; text-transform: uppercase;
    }
    QPushButton:hover { background-color: #b01e0a; }
"""

# ── Category colour map ───────────────────────────────────────────────────────

_CAT_COLORS = {
    "Machine":    "#2196F3",
    "Man":        "#4CAF50",
    "Mdl Chg":    "#AB47BC",
    "Model Change": "#AB47BC",
    "Setting":    "#FF9800",
    "Repair":     "#F44336",
    "Material":   "#FFEB3B",
    "Method":     "#00BCD4",
    "Others":     "#78909C",
    "Lainnya":    "#78909C",
}

_FALLBACK_COLORS = [
    "#E91E63", "#009688", "#FF5722", "#607D8B",
    "#795548", "#3F51B5", "#FFC107", "#8BC34A",
]

_MONTHS = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
           "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]

BG_FIG  = "#282C34"
BG_AXES = "#21252B"
COL_TEXT = "#ABB2BF"
COL_GRID = "#3E4451"
PLAN_COLOR = "#FF4444"


def _cat_color(name: str, used: dict) -> str:
    if name in _CAT_COLORS:
        return _CAT_COLORS[name]
    if name not in used:
        idx = len(used) % len(_FALLBACK_COLORS)
        used[name] = _FALLBACK_COLORS[idx]
    return used[name]


# ── Widget ────────────────────────────────────────────────────────────────────

class VisualisasiWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._sections_loaded = False
        self._setup_ui()

    def showEvent(self, event):
        super().showEvent(event)
        self._load_sections_once()

    def _load_sections_once(self):
        if self._sections_loaded:
            return
        try:
            sections = get_all_sections()
            self.combo_section.blockSignals(True)
            for sid, sname in sections:
                self.combo_section.addItem(sname, sid)
            self.combo_section.blockSignals(False)
            self._sections_loaded = True
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Peringatan", f"Gagal memuat daftar section: {e}")

    # ── UI ────────────────────────────────────────────────────────────────────

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(15, 15, 15, 15)
        outer.setSpacing(12)

        # ── Filter card ───────────────────────────────────────────────────────
        card_f = QFrame()
        card_f.setStyleSheet(_CARD_STYLE)
        fl = QHBoxLayout(card_f)
        fl.setContentsMargins(16, 12, 16, 12)
        fl.setSpacing(10)

        fl.addWidget(_lbl("Section"))
        self.combo_section = QComboBox()
        self.combo_section.setMinimumWidth(165)
        self.combo_section.setStyleSheet(_COMBO_STYLE)
        self.combo_section.addItem("Semua", None)
        fl.addWidget(self.combo_section)

        fl.addWidget(_lbl("Tahun"))
        self.combo_tahun = QComboBox()
        self.combo_tahun.setMinimumWidth(90)
        self.combo_tahun.setStyleSheet(_COMBO_STYLE)
        now = QDate.currentDate().year()
        for y in range(now - 2, now + 1):
            self.combo_tahun.addItem(str(y), y)
        self.combo_tahun.setCurrentIndex(self.combo_tahun.count() - 1)
        fl.addWidget(self.combo_tahun)

        fl.addStretch()

        btn = QPushButton("Tampilkan")
        btn.setMinimumSize(100, 32)
        btn.setStyleSheet(_BTN_TAMPIL)
        btn.clicked.connect(self._tampilkan)
        fl.addWidget(btn)

        outer.addWidget(card_f)

        # ── Stat cards ────────────────────────────────────────────────────────
        stat_row = QHBoxLayout()
        stat_row.setSpacing(12)

        self._lbl_total_loss, c1 = _make_stat_card("Total Loss Time", "— hr", "#da291c")
        self._lbl_biggest_cat, c2 = _make_stat_card("Kategori Terbesar", "—", "#da291c")
        self._lbl_avg_ratio,  c3 = _make_stat_card("Rata-rata Process Ratio", "— %", "#da291c")

        stat_row.addWidget(c1)
        stat_row.addWidget(c2)
        stat_row.addWidget(c3)
        outer.addLayout(stat_row)

        # ── Chart card ────────────────────────────────────────────────────────
        card_c = QFrame()
        card_c.setStyleSheet(_CARD_STYLE)
        cl = QVBoxLayout(card_c)
        cl.setContentsMargins(12, 12, 12, 12)

        self.fig = Figure(figsize=(10, 5), facecolor=BG_FIG)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        cl.addWidget(self.canvas)

        outer.addWidget(card_c, 1)

        self._draw_empty()

    # ── Chart logic ───────────────────────────────────────────────────────────

    def _draw_empty(self):
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        _style_axes(ax, self.fig)
        ax.text(
            0.5, 0.5, "Pilih Section & Tahun, lalu klik Tampilkan",
            ha="center", va="center", transform=ax.transAxes,
            color=COL_TEXT, fontsize=12,
        )
        self.canvas.draw()

    def _tampilkan(self):
        section_id = self.combo_section.currentData()
        tahun      = self.combo_tahun.currentData()
        try:
            data = get_loss_time_per_bulan(section_id, tahun)
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error", f"Gagal memuat data: {e}")
            return
        self._update_stat_cards(data)
        self._update_chart(data, tahun)

    def _update_stat_cards(self, data: list):
        # Total loss time sepanjang tahun
        total_loss = sum(sum(d["loss_by_category"].values()) for d in data)

        # Kategori dengan total loss tertinggi
        cat_totals: dict[str, float] = {}
        for d in data:
            for cat, val in d["loss_by_category"].items():
                cat_totals[cat] = cat_totals.get(cat, 0.0) + val
        biggest = max(cat_totals, key=cat_totals.get) if cat_totals else None

        # Rata-rata process ratio (skip bulan tanpa data)
        ratios = [
            d["process_hour"] / d["total_hour"] * 100
            for d in data if d["total_hour"] > 0
        ]
        avg_ratio = sum(ratios) / len(ratios) if ratios else None

        self._lbl_total_loss.setText(f"{total_loss:.2f} hr" if total_loss > 0 else "—")
        self._lbl_biggest_cat.setText(biggest if biggest else "—")
        self._lbl_avg_ratio.setText(f"{avg_ratio:.1f} %" if avg_ratio is not None else "—")

    def _update_chart(self, data: list, tahun: int):
        self.fig.clear()

        # collect all categories present in data
        all_cats: list[str] = []
        for d in data:
            for k in d["loss_by_category"]:
                if k not in all_cats:
                    all_cats.append(k)

        x      = list(range(12))
        labels = _MONTHS

        # ── Axes ──────────────────────────────────────────────────────────────
        ax_bar = self.fig.add_subplot(111)
        ax_line = ax_bar.twinx()
        _style_axes(ax_bar, self.fig)
        _style_axes_right(ax_line)

        # ── Stacked bars ──────────────────────────────────────────────────────
        bar_w    = 0.55
        bottoms  = [0.0] * 12
        used_dyn: dict = {}

        for cat in all_cats:
            vals = [d["loss_by_category"].get(cat, 0.0) for d in data]
            color = _cat_color(cat, used_dyn)
            ax_bar.bar(x, vals, bar_w, bottom=bottoms, color=color,
                       label=cat, zorder=3)
            bottoms = [b + v for b, v in zip(bottoms, vals)]

        # ── Label total di atas tiap bar ─────────────────────────────────────
        for xi, total in zip(x, bottoms):
            if total > 0:
                ax_bar.text(
                    xi, total + 0.05, f"{total:.2f}",
                    ha="center", va="bottom", fontsize=8,
                    color="white", fontweight="bold", zorder=6,
                )

        # ── Process ratio line ────────────────────────────────────────────────
        ratios = []
        for d in data:
            if d["total_hour"] > 0:
                ratios.append(d["process_hour"] / d["total_hour"] * 100)
            else:
                ratios.append(None)

        ax_line.plot(x, ratios, color="#00E5FF", linewidth=2,
                     marker="o", markersize=5, label="Process Ratio %",
                     zorder=4)

        # add value labels on the line (skip None)
        for xi, rv in zip(x, ratios):
            if rv is not None:
                ax_line.annotate(
                    f"{rv:.1f}%", xy=(xi, rv),
                    xytext=(0, 7), textcoords="offset points",
                    ha="center", fontsize=7.5, color="#00E5FF",
                )

        # ── Plan target line ──────────────────────────────────────────────────
        ax_line.axhline(86, color=PLAN_COLOR, linewidth=1.5,
                        linestyle="--", zorder=5, label="Plan 86%")
        ax_line.text(11.55, 86.8, "86%", color=PLAN_COLOR, fontsize=8,
                     va="bottom", ha="right")

        # ── Axes config ───────────────────────────────────────────────────────
        ax_bar.set_xticks(x)
        ax_bar.set_xticklabels(labels, color=COL_TEXT, fontsize=9)
        ax_bar.set_xlim(-0.6, 11.6)
        ax_bar.set_ylabel("Loss Time (Hour)", color=COL_TEXT, fontsize=9)
        ax_bar.tick_params(axis="y", colors=COL_TEXT, labelsize=8)
        ax_bar.tick_params(axis="x", colors=COL_TEXT)

        ax_line.set_ylim(0, 110)
        ax_line.set_ylabel("Process Ratio (%)", color="#00E5FF", fontsize=9)
        ax_line.tick_params(axis="y", colors="#00E5FF", labelsize=8)
        ax_line.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))

        # ── Title ─────────────────────────────────────────────────────────────
        sec_text = self.combo_section.currentText()
        self.fig.suptitle(
            f"Performance Chart — {sec_text}  |  {tahun}",
            color="white", fontsize=11, fontweight="bold", y=0.98,
        )

        # ── Legend ────────────────────────────────────────────────────────────
        handles_bar, labels_bar = ax_bar.get_legend_handles_labels()
        handles_line, labels_line = ax_line.get_legend_handles_labels()
        ax_bar.legend(
            handles_bar + handles_line, labels_bar + labels_line,
            loc="upper left", fontsize=8,
            facecolor=BG_AXES, edgecolor=COL_GRID,
            labelcolor=COL_TEXT, ncol=min(len(all_cats) + 2, 6),
        )

        self.fig.tight_layout(rect=[0, 0, 1, 0.96])
        self.canvas.draw()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_stat_card(title: str, default_val: str, accent: str) -> tuple:
    """Return (value_QLabel, card_QFrame)."""
    card = QFrame()
    card.setStyleSheet(
        "QFrame { background-color: #252525; border-radius: 0px; }"
    )
    card.setFixedHeight(86)
    lay = QVBoxLayout(card)
    lay.setContentsMargins(16, 10, 16, 10)
    lay.setSpacing(2)

    lbl_title = QLabel(title)
    lbl_title.setStyleSheet(
        "color: #969696; font-size: 10px; background: transparent;"
    )
    lbl_title.setAlignment(Qt.AlignLeft)

    lbl_val = QLabel(default_val)
    lbl_val.setStyleSheet(
        "color: #ffffff; font-size: 18px; font-weight: bold; background: transparent;"
    )
    lbl_val.setAlignment(Qt.AlignLeft)

    accent_line = QFrame()
    accent_line.setFixedHeight(3)
    accent_line.setStyleSheet(
        f"QFrame {{ background-color: {accent}; border-radius: 2px; }}"
    )

    lay.addWidget(lbl_title)
    lay.addWidget(lbl_val)
    lay.addStretch()
    lay.addWidget(accent_line)

    return lbl_val, card


def _lbl(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet("color: #969696; font-size: 11px;")
    return lbl


def _style_axes(ax, fig):
    fig.patch.set_facecolor(BG_FIG)
    ax.set_facecolor(BG_AXES)
    for spine in ax.spines.values():
        spine.set_edgecolor(COL_GRID)
    ax.tick_params(colors=COL_TEXT)
    ax.yaxis.label.set_color(COL_TEXT)
    ax.xaxis.label.set_color(COL_TEXT)
    ax.grid(axis="y", color=COL_GRID, linewidth=0.5, linestyle="--", zorder=0)


def _style_axes_right(ax):
    ax.set_facecolor("none")
    for spine in ax.spines.values():
        spine.set_edgecolor(COL_GRID)

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

from controllers.master_controller import get_all_sections
from controllers.analytics_controller import get_loss_time_per_bulan
from modules.config import TARGET_PROCESS_RATIO


# ── Light-theme style constants (sama dengan input_laporan & dashboard) ───────

_CARD    = "QFrame { background-color: #FFFFFF; border-radius: 0px; border: 1px solid #E5E7EB; }"
_HDR_LBL = ("color: #212121; font-size: 11px; font-weight: bold;"
            " border-left: 2px solid #E60012; padding-left: 8px;"
            " letter-spacing: 1px; text-transform: uppercase;")
_FLD_LBL = "color: #6B7280; font-size: 10px; letter-spacing: 1px;"

_COMBO_STYLE = """
    QComboBox {
        background-color: #FFFFFF; border: 1px solid #D1D5DB;
        border-radius: 0px; padding-left: 8px;
        color: #212121; font-size: 11px; min-height: 30px;
    }
    QComboBox:focus { border: 1px solid #E60012; }
    QComboBox::drop-down { border: none; width: 24px; }
    QComboBox QAbstractItemView {
        background-color: #FFFFFF; color: #212121;
        selection-background-color: #F3F4F6;
        border: 1px solid #D1D5DB;
    }
"""

_BTN_TAMPIL = """
    QPushButton {
        background-color: #E60012; color: #ffffff;
        border: none; border-radius: 0px; font-size: 11px; padding: 0 16px;
        min-height: 30px; letter-spacing: 1px;
    }
    QPushButton:hover { background-color: #C0000F; }
"""

# ── Chart colour constants — light theme ─────────────────────────────────────

BG_FIG   = "#FFFFFF"
BG_AXES  = "#FFFFFF"
COL_TEXT = "#6B7280"
COL_GRID = "#F3F4F6"
PLAN_COLOR = "#E60012"

# ── Category colour map ───────────────────────────────────────────────────────

_CAT_COLORS = {
    "Machine":       "#2196F3",
    "Man":           "#4CAF50",
    "Mdl Chg":       "#AB47BC",
    "Model Change":  "#AB47BC",
    "Setting":       "#FF9800",
    "Repair":        "#F44336",
    "Material":      "#FFEB3B",
    "Method":        "#00BCD4",
    "Others":        "#78909C",
    "Lainnya":       "#78909C",
}

_FALLBACK_COLORS = [
    "#E91E63", "#009688", "#FF5722", "#607D8B",
    "#795548", "#3F51B5", "#FFC107", "#8BC34A",
]

_MONTHS = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
           "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]


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
        outer.setContentsMargins(12, 10, 12, 12)
        outer.setSpacing(8)

        # ── Filter card ───────────────────────────────────────────────────────
        card_f = QFrame()
        card_f.setStyleSheet(
            "QFrame { background-color: #FFFFFF; border-radius: 0px;"
            " border-top: 2px solid #E60012; border-bottom: 1px solid #E5E7EB; }"
        )
        fl = QHBoxLayout(card_f)
        fl.setContentsMargins(12, 8, 12, 8)
        fl.setSpacing(8)

        fl.addWidget(_lbl("Section"))
        self.combo_section = QComboBox()
        self.combo_section.setMinimumWidth(165)
        self.combo_section.setMinimumHeight(28)
        self.combo_section.setStyleSheet(_COMBO_STYLE)
        self.combo_section.addItem("Semua", None)
        fl.addWidget(self.combo_section)

        def _vsep():
            s = QFrame(); s.setFrameShape(QFrame.VLine)
            s.setFixedWidth(1); s.setFixedHeight(22)
            s.setStyleSheet("background-color: #D1D5DB; border: none;")
            return s

        fl.addSpacing(4); fl.addWidget(_vsep()); fl.addSpacing(4)

        fl.addWidget(_lbl("Tahun"))
        self.combo_tahun = QComboBox()
        self.combo_tahun.setMinimumWidth(90)
        self.combo_tahun.setMinimumHeight(28)
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
        stat_row.setSpacing(8)

        self._lbl_total_loss, c1 = _make_stat_card("Total Loss Time",       "— hr")
        self._lbl_biggest_cat, c2 = _make_stat_card("Kategori Terbesar",     "—")
        self._lbl_avg_ratio,  c3  = _make_stat_card("Rata-rata Process Ratio","— %")

        stat_row.addWidget(c1)
        stat_row.addWidget(c2)
        stat_row.addWidget(c3)
        outer.addLayout(stat_row)

        # ── Chart card ────────────────────────────────────────────────────────
        card_c = QFrame()
        card_c.setStyleSheet(_CARD)
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
            color="#9CA3AF", fontsize=12,
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
        total_loss = sum(sum(d["loss_by_category"].values()) for d in data)

        cat_totals: dict[str, float] = {}
        for d in data:
            for cat, val in d["loss_by_category"].items():
                cat_totals[cat] = cat_totals.get(cat, 0.0) + val
        biggest = max(cat_totals, key=cat_totals.get) if cat_totals else None

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

        all_cats: list[str] = []
        for d in data:
            for k in d["loss_by_category"]:
                if k not in all_cats:
                    all_cats.append(k)

        x      = list(range(12))
        labels = _MONTHS

        ax_bar  = self.fig.add_subplot(111)
        ax_line = ax_bar.twinx()
        _style_axes(ax_bar, self.fig)
        _style_axes_right(ax_line)

        # ── Stacked bars ──────────────────────────────────────────────────────
        bar_w   = 0.55
        bottoms = [0.0] * 12
        used_dyn: dict = {}

        for cat in all_cats:
            vals  = [d["loss_by_category"].get(cat, 0.0) for d in data]
            color = _cat_color(cat, used_dyn)
            ax_bar.bar(x, vals, bar_w, bottom=bottoms, color=color,
                       label=cat, zorder=3, alpha=0.9)
            bottoms = [b + v for b, v in zip(bottoms, vals)]

        # ── Label total di atas tiap bar ─────────────────────────────────────
        for xi, total in zip(x, bottoms):
            if total > 0:
                ax_bar.text(
                    xi, total + 0.02, f"{total:.2f}",
                    ha="center", va="bottom", fontsize=8,
                    color="#212121", fontweight="bold", zorder=6,
                )

        # ── Process ratio line ────────────────────────────────────────────────
        ratios = []
        for d in data:
            ratios.append(d["process_hour"] / d["total_hour"] * 100
                          if d["total_hour"] > 0 else None)

        ax_line.plot(x, ratios, color="#1a6fa8", linewidth=2,
                     marker="o", markersize=5, markerfacecolor="#FFFFFF",
                     markeredgecolor="#1a6fa8", markeredgewidth=1.5,
                     label="Process Ratio %", zorder=4)

        for xi, rv in zip(x, ratios):
            if rv is not None:
                ax_line.annotate(
                    f"{rv:.1f}%", xy=(xi, rv),
                    xytext=(0, 7), textcoords="offset points",
                    ha="center", fontsize=7.5, color="#1a6fa8",
                )

        # ── Plan target line ──────────────────────────────────────────────────
        ax_line.axhline(TARGET_PROCESS_RATIO, color=PLAN_COLOR, linewidth=1.5,
                        linestyle="--", zorder=5, alpha=0.6,
                        label=f"Plan {TARGET_PROCESS_RATIO:.0f}%")
        ax_line.text(11.55, TARGET_PROCESS_RATIO + 0.8, f"{TARGET_PROCESS_RATIO:.0f}%",
                     color=PLAN_COLOR, fontsize=8, va="bottom", ha="right", fontweight="bold")

        # ── Axes config ───────────────────────────────────────────────────────
        ax_bar.set_xticks(x)
        ax_bar.set_xticklabels(labels, color=COL_TEXT, fontsize=9)
        ax_bar.set_xlim(-0.6, 11.6)
        ax_bar.set_ylabel("Loss Time (Hour)", color=COL_TEXT, fontsize=9)
        ax_bar.tick_params(axis="y", colors=COL_TEXT, labelsize=8)
        ax_bar.tick_params(axis="x", colors=COL_TEXT)

        ax_line.set_ylim(0, 110)
        ax_line.set_ylabel("Process Ratio (%)", color="#1a6fa8", fontsize=9)
        ax_line.tick_params(axis="y", colors="#1a6fa8", labelsize=8)
        ax_line.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))

        # ── Title ─────────────────────────────────────────────────────────────
        sec_text = self.combo_section.currentText()
        self.fig.suptitle(
            f"Performance Chart — {sec_text}  |  {tahun}",
            color="#212121", fontsize=11, fontweight="bold", y=0.98,
        )

        # ── Legend ────────────────────────────────────────────────────────────
        handles_bar,  labels_bar  = ax_bar.get_legend_handles_labels()
        handles_line, labels_line = ax_line.get_legend_handles_labels()
        ax_bar.legend(
            handles_bar + handles_line, labels_bar + labels_line,
            loc="upper left", fontsize=8,
            facecolor="#FFFFFF", edgecolor="#E5E7EB",
            labelcolor=COL_TEXT, ncol=min(len(all_cats) + 2, 6),
        )

        self.fig.tight_layout(rect=[0, 0, 1, 0.96])
        self.canvas.draw()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_stat_card(title: str, default_val: str) -> tuple:
    """Return (value_QLabel, card_QFrame) — light theme, sama dengan dashboard."""
    card = QFrame()
    card.setStyleSheet(
        "QFrame { background-color: #FFFFFF; border-radius: 0px;"
        " border: 1px solid #E5E7EB; border-top: 3px solid #E60012; }"
    )
    card.setFixedHeight(86)
    lay = QVBoxLayout(card)
    lay.setContentsMargins(16, 10, 16, 10)
    lay.setSpacing(2)

    lbl_title = QLabel(title)
    lbl_title.setStyleSheet(
        "color: #6B7280; font-size: 10px; letter-spacing: 1px;"
        " background: transparent; border: none;"
    )
    lbl_title.setAlignment(Qt.AlignLeft)

    lbl_val = QLabel(default_val)
    lbl_val.setStyleSheet(
        "color: #212121; font-size: 18px; font-weight: bold;"
        " background: transparent; border: none;"
    )
    lbl_val.setAlignment(Qt.AlignLeft)

    lay.addWidget(lbl_title)
    lay.addWidget(lbl_val)
    lay.addStretch()

    return lbl_val, card


def _lbl(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(_FLD_LBL)
    return lbl


def _style_axes(ax, fig):
    fig.patch.set_facecolor(BG_FIG)
    ax.set_facecolor(BG_AXES)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#D1D5DB")
    ax.spines["bottom"].set_color("#D1D5DB")
    ax.tick_params(colors=COL_TEXT)
    ax.yaxis.label.set_color(COL_TEXT)
    ax.xaxis.label.set_color(COL_TEXT)
    ax.grid(axis="y", color=COL_GRID, linewidth=0.5, linestyle="--", zorder=0)
    ax.set_axisbelow(True)


def _style_axes_right(ax):
    ax.set_facecolor("none")
    ax.spines["top"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.spines["right"].set_color("#1a6fa8")

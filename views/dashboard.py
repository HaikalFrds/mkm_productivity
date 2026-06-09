import matplotlib
matplotlib.use("QtAgg")
import mplcursors
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QSizePolicy,
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor

from controllers.dashboard_controller import get_dashboard_data, get_monthly_loss_by_group
from modules.config import TARGET_PROCESS_RATIO
from modules.icons import ic_refresh, TOOL_ICON_SIZE
from modules.view_optimizer import LazyViewMixin


# ── Constants ────────────────────────────────────────────────────────────────

_MONTHS  = ["Jan","Feb","Mar","Apr","Mei","Jun","Jul","Agu","Sep","Okt","Nov","Des"]
_DAYS_ID = ["Senin","Selasa","Rabu","Kamis","Jumat","Sabtu","Minggu"]

_GROUPS = [
    ("#cc3333", "Production"),
    ("#2255aa", "Maintenance"),
    ("#e67e22", "PPC"),
    ("#27ae60", "Quality Control"),
    ("#8e44ad", "Production Engineering"),
]

# ── Light-theme style constants (sama dengan input_laporan) ──────────────────
_CARD    = "QFrame { background-color: #FFFFFF; border-radius: 0px; border: 1px solid #E5E7EB; }"
_HDR_LBL = ("color: #212121; font-size: 11px; font-weight: bold;"
            " border-left: 2px solid #E60012; padding-left: 8px;"
            " letter-spacing: 1px; text-transform: uppercase;")
_FLD_LBL = "color: #6B7280; font-size: 10px; letter-spacing: 1px;"

_TABLE_SS = """
    QTableWidget {
        background-color: #FFFFFF; border: 1px solid #D1D5DB; gridline-color: #F3F4F6;
    }
    QTableWidget::item {
        color: #212121; padding: 4px 8px;
        background-color: #FFFFFF; border-bottom: 1px solid #F3F4F6;
    }
    QTableWidget::item:alternate { background-color: #F9FAFB; }
    QTableWidget::item:selected  { background-color: #F3F4F6; }
    QHeaderView::section {
        background-color: #F8F9FA; color: #6B7280; border: none;
        border-bottom: 1px solid #D1D5DB; border-right: 1px solid #E5E7EB;
        padding: 5px 8px; font-weight: bold; font-size: 10px;
        text-transform: uppercase; letter-spacing: 1px;
    }
"""


# ── Chart helpers ─────────────────────────────────────────────────────────────

def _style_ax(fig, ax):
    """Light theme untuk axes — konsisten dengan warna app."""
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#FFFFFF")
    ax.tick_params(axis="both", colors="#6B7280", labelsize=8)
    ax.spines["left"].set_color("#D1D5DB")
    ax.spines["bottom"].set_color("#D1D5DB")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.yaxis.grid(True, color="#F3F4F6", linewidth=0.5, linestyle="--")
    ax.set_axisbelow(True)


def _style_twin(ax2):
    """Light theme untuk secondary (twinx) axis."""
    ax2.tick_params(axis="y", colors="#27AE60", labelsize=8)
    ax2.spines["right"].set_color("#27AE60")
    ax2.spines["top"].set_visible(False)
    ax2.spines["left"].set_visible(False)
    ax2.spines["bottom"].set_visible(False)
    ax2.set_facecolor("none")
    ax2.yaxis.set_label_position("right")
    ax2.yaxis.tick_right()


# ── StatCard ─────────────────────────────────────────────────────────────────

class _StatCard(QFrame):
    def __init__(self, title: str, init_val: str, subtitle: str, accent: str):
        super().__init__()
        self.setFixedHeight(88)
        self.setStyleSheet(
            "QFrame { background-color: #FFFFFF; border-radius: 0px;"
            " border: 1px solid #E5E7EB; border-top: 3px solid #E60012; }"
        )
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 10, 14, 10)
        lay.setSpacing(1)

        lbl_t = QLabel(title)
        lbl_t.setStyleSheet(
            "color: #6B7280; font-size: 9px; letter-spacing: 1px;"
            " text-transform: uppercase; background: transparent; border: none;"
        )

        self._val = QLabel(init_val)
        self._val.setStyleSheet(
            "color: #212121; font-size: 26px; font-weight: bold;"
            " background: transparent; border: none;"
        )

        lbl_s = QLabel(subtitle)
        lbl_s.setStyleSheet(
            "color: #9CA3AF; font-size: 9px; background: transparent; border: none;"
        )

        lay.addWidget(lbl_t)
        lay.addWidget(self._val)
        lay.addWidget(lbl_s)
        lay.addStretch()

    def set_value(self, v: str):
        self._val.setText(v)


# ── DashboardWidget ───────────────────────────────────────────────────────────

class DashboardWidget(LazyViewMixin, QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    # UI

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 10, 12, 12)
        outer.setSpacing(8)

        outer.addLayout(self._build_header())
        outer.addLayout(self._build_stat_row())
        outer.addWidget(self._build_main_chart_card(), stretch=3)
        outer.addLayout(self._build_bottom_row(), stretch=2)

    # Header bar

    def _build_header(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)

        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setFixedWidth(1); sep.setFixedHeight(16)
        sep.setStyleSheet("background-color: #D1D5DB; border: none;")

        self._lbl_date = QLabel()
        self._lbl_date.setStyleSheet("color: #6B7280; font-size: 11px;")
        self._refresh_date()

        btn = QPushButton("Refresh")
        btn.setIcon(ic_refresh()); btn.setIconSize(TOOL_ICON_SIZE)
        btn.setFixedSize(88, 28)
        btn.setStyleSheet(
            "QPushButton { background-color: #F3F4F6; color: #6B7280;"
            "  border: 1px solid #D1D5DB; font-size: 11px; border-radius: 0px; }"
            "QPushButton:hover { background-color: #D1D5DB; color: #212121; }"
        )
        btn.clicked.connect(self.load_data)

        row.addSpacing(4)
        row.addWidget(sep)
        row.addSpacing(8)
        row.addWidget(self._lbl_date)
        row.addStretch()
        row.addWidget(btn)
        return row

    def _refresh_date(self):
        today = QDate.currentDate()
        self._lbl_date.setText(
            f"{_DAYS_ID[today.dayOfWeek()-1]}, "
            f"{today.toString('d')} {_MONTHS[today.month()-1]} {today.toString('yyyy')}"
        )

    # Stat row

    def _build_stat_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(8)
        self._c_laporan  = _StatCard("LAPORAN HARI INI",      "0",      "laporan harian",    "#E60012")
        self._c_loss_hr  = _StatCard("LOSS TIME HARI INI",    "0.00 H", "jam terbuang",      "#e67e22")
        self._c_process  = _StatCard("PROCESS RATIO BLN INI", "— %",    "efisiensi produksi","#27AE60")
        self._c_loss_bln = _StatCard("TOTAL LOSS BLN INI",    "0.00 H", "akumulasi bulanan", "#27ae60")
        for c in (self._c_laporan, self._c_loss_hr, self._c_process, self._c_loss_bln):
            row.addWidget(c)
        return row

    # Main chart

    def _build_main_chart_card(self) -> QFrame:
        card = QFrame()
        card.setStyleSheet(_CARD)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(6)

        hdr = QHBoxLayout()
        lbl = QLabel("PERFORMANCE — Loss Time per Bulan + Process Ratio")
        lbl.setStyleSheet(_HDR_LBL)
        self._lbl_year = QLabel()
        self._lbl_year.setStyleSheet(_FLD_LBL)
        hdr.addWidget(lbl); hdr.addStretch(); hdr.addWidget(self._lbl_year)
        lay.addLayout(hdr)

        self._fig = Figure(facecolor="#FFFFFF")
        self._fig.subplots_adjust(left=0.07, right=0.93, top=0.88, bottom=0.13)
        self._ax1 = self._fig.add_subplot(111)
        self._ax2 = self._ax1.twinx()
        _style_ax(self._fig, self._ax1)
        _style_twin(self._ax2)

        self._canvas = FigureCanvas(self._fig)
        self._canvas.setMinimumHeight(220)
        self._canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        lay.addWidget(self._canvas)
        return card

    # Bottom row

    def _build_bottom_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(8)
        row.addWidget(self._build_top3_card(), stretch=2)
        row.addWidget(self._build_recent_card(), stretch=3)
        return row

    def _build_top3_card(self) -> QFrame:
        card = QFrame()
        card.setStyleSheet(_CARD)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(6)

        lbl = QLabel("THE BIG THREE — Loss Bulan Ini")
        lbl.setStyleSheet(_HDR_LBL)
        lay.addWidget(lbl)

        self._fig3 = Figure(facecolor="#FFFFFF")
        self._fig3.subplots_adjust(left=0.30, right=0.88, top=0.88, bottom=0.14)
        self._ax3 = self._fig3.add_subplot(111)
        _style_ax(self._fig3, self._ax3)

        self._canvas3 = FigureCanvas(self._fig3)
        self._canvas3.setMinimumHeight(130)
        self._canvas3.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        lay.addWidget(self._canvas3)
        return card

    def _build_recent_card(self) -> QFrame:
        card = QFrame()
        card.setStyleSheet(_CARD)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(6)

        lbl = QLabel("LAPORAN TERBARU")
        lbl.setStyleSheet(_HDR_LBL)
        lay.addWidget(lbl)

        self._tbl = QTableWidget()
        self._tbl.setColumnCount(4)
        self._tbl.setHorizontalHeaderLabels(["Tanggal", "Shop", "Loss (H)", "Status"])
        hh = self._tbl.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.Stretch)
        hh.setSectionResizeMode(2, QHeaderView.Fixed)
        hh.setSectionResizeMode(3, QHeaderView.Fixed)
        self._tbl.setColumnWidth(2, 80)
        self._tbl.setColumnWidth(3, 90)
        self._tbl.verticalHeader().setVisible(False)
        self._tbl.setEditTriggers(QTableWidget.NoEditTriggers)
        self._tbl.setSelectionBehavior(QTableWidget.SelectRows)
        self._tbl.setAlternatingRowColors(True)
        self._tbl.setStyleSheet(_TABLE_SS)
        lay.addWidget(self._tbl)
        return card

    # Events

    def _on_first_show(self):
        self.load_data()

    def _on_show(self):
        self.load_data()  # dashboard selalu fresh — data hari ini bisa berubah

    # Data

    def load_data(self):
        self._refresh_date()
        year = QDate.currentDate().year()
        self._lbl_year.setText(f"Tahun {year}")

        try:
            today = get_dashboard_data()
        except Exception:
            today = {"report_count": 0, "loss_today": 0.0, "categories": [], "recent": []}

        try:
            monthly = get_monthly_loss_by_group(year)
        except Exception:
            monthly = []

        self._update_stats(today, monthly)
        self._update_main_chart(monthly)
        self._update_top3(today.get("categories", []))
        self._update_recent(today.get("recent", []))

    def _update_stats(self, today: dict, monthly: list):
        self._c_laporan.set_value(str(today.get("report_count", 0)))
        self._c_loss_hr.set_value(f"{today.get('loss_today', 0.0):.2f} H")

        process_ratio = today.get("process_ratio")
        if process_ratio is not None:
            self._c_process.set_value(f"{process_ratio:.1f} %")
        else:
            self._c_process.set_value("— %")

        if monthly:
            m = monthly[QDate.currentDate().month() - 1]
            total = m.get("total_hour", 0.0)
            loss  = m.get("loss_total", 0.0)
            if total > 0:
                self._c_loss_bln.set_value(f"{loss:.2f} H")
                return
        cats = today.get("categories", [])
        self._c_loss_bln.set_value(f"{sum(c['hours'] for c in cats):.2f} H")

    def _update_main_chart(self, monthly: list):
        ax1, ax2 = self._ax1, self._ax2
        ax1.cla(); ax2.cla()
        _style_ax(self._fig, ax1)
        _style_twin(ax2)

        x = list(range(12))
        has_data = monthly and any(
            any(v > 0 for v in m.get("by_group", {}).values()) for m in monthly
        )

        if has_data:
            bottoms   = [0.0] * 12
            max_total = 0.0
            for color, gname in _GROUPS:
                heights = [monthly[i]["by_group"].get(gname, 0.0) for i in range(12)]
                ax1.bar(x, heights, bottom=bottoms, color=color,
                        label=gname, width=0.45, alpha=0.92, zorder=3)
                bottoms = [b + h for b, h in zip(bottoms, heights)]
            max_total = max(bottoms) if bottoms else 1.0

            self._cursor = mplcursors.cursor(ax1, hover=mplcursors.HoverMode.Transient)

            @self._cursor.connect("add")
            def _on_bar_hover(sel):
                x_idx = int(round(sel.target[0]))
                if 0 <= x_idx < 12:
                    month_name = _MONTHS[x_idx]
                    m = monthly[x_idx]
                    total_loss = sum(m.get("by_group", {}).values())
                    pct        = m.get("process_pct", 0.0)
                    total_hour = m.get("total_hour", 0.0)
                    lines = [f"\U0001F4C5 {month_name}"]
                    for _, gname in _GROUPS:
                        val = m.get("by_group", {}).get(gname, 0.0)
                        if val > 0:
                            lines.append(f"  {gname}: {val:.2f} H")
                    lines.append(f"  ─────────────────")
                    lines.append(f"  Total Loss: {total_loss:.2f} H")
                    lines.append(f"  Total Hour: {total_hour:.2f} H")
                    lines.append(f"  Process Ratio: {pct:.1f}%")
                    sel.annotation.set_text("\n".join(lines))
                    sel.annotation.get_bbox_patch().set(fc="#FFFFFF", alpha=0.95, ec="#E60012", lw=1)
                    sel.annotation.set_color("#212121")
                    sel.annotation.set_fontsize(8)

            ax1.set_ylim(0, max_total * 1.5)

            pcts = [monthly[i]["process_pct"] for i in range(12)]
            px   = [i for i, p in enumerate(pcts) if monthly[i]["total_hour"] > 0]
            py   = [pcts[i] for i in px]
            if px:
                ax2.plot(px, py, color="#27AE60", linewidth=1.8,
                         marker="o", markersize=4, markerfacecolor="#FFFFFF",
                         markeredgecolor="#27AE60", markeredgewidth=1.5,
                         zorder=6, label="Process %")
                line_objs = ax2.get_lines()
                if line_objs:
                    self._cursor2 = mplcursors.cursor(line_objs[0], hover=mplcursors.HoverMode.Transient)

                    @self._cursor2.connect("add")
                    def _on_line_hover(sel):
                        x_idx = int(round(sel.target[0]))
                        if 0 <= x_idx < 12:
                            pct   = monthly[x_idx]["process_pct"]
                            total = monthly[x_idx]["total_hour"]
                            sel.annotation.set_text(
                                f"\U0001F4C5 {_MONTHS[x_idx]}\n"
                                f"  Process Ratio: {pct:.1f}%\n"
                                f"  Total Hour: {total:.2f} H"
                            )
                            sel.annotation.get_bbox_patch().set(fc="#FFFFFF", alpha=0.95, ec="#27AE60", lw=1)
                            sel.annotation.set_color("#212121")
                            sel.annotation.set_fontsize(8)

                for xi, yi in zip(px, py):
                    ax2.annotate(f"{yi:.0f}%",
                                 xy=(xi, yi),
                                 xytext=(0, 8), textcoords="offset points",
                                 ha="center", fontsize=7, color="#27AE60",
                                 fontweight="bold", zorder=7)

            ax2.axhline(y=TARGET_PROCESS_RATIO, color="#E60012", linestyle="--",
                        linewidth=1.0, alpha=0.6, zorder=4,
                        label=f"Target {TARGET_PROCESS_RATIO:.0f}%")
            ax2.text(11.6, TARGET_PROCESS_RATIO + 2, f"{TARGET_PROCESS_RATIO:.0f}%",
                     fontsize=8, color="#E60012", ha="left", va="bottom", fontweight="bold")

        else:
            ax1.set_ylim(0, 10)
            ax1.text(0.5, 0.5, "Belum ada data untuk tahun ini",
                     transform=ax1.transAxes, ha="center", va="center",
                     color="#9CA3AF", fontsize=11)

        ax1.set_xlim(-0.5, 11.5)
        ax1.set_xticks(x)
        ax1.set_xticklabels(_MONTHS, fontsize=8, color="#6B7280")
        ax1.set_ylabel("Loss (H)", fontsize=8, color="#6B7280", labelpad=4)
        ax2.set_ylim(0, 115)
        ax2.set_ylabel("Process (%)", fontsize=8, color="#27AE60", labelpad=4)

        if has_data:
            h1, l1 = ax1.get_legend_handles_labels()
            h2, l2 = ax2.get_legend_handles_labels()
            ax1.legend(
                h1 + h2, l1 + l2,
                loc="upper left", fontsize=7, ncol=3,
                framealpha=0.0, facecolor="none",
                labelcolor="#6B7280", edgecolor="none",
            )

        self._canvas.draw()

    def _update_top3(self, categories: list):
        ax = self._ax3
        ax.cla()
        _style_ax(self._fig3, ax)

        top3 = [c for c in sorted(categories, key=lambda c: c["hours"], reverse=True)
                if c["hours"] > 0][:3]

        if top3:
            names  = [c["group"] for c in top3]
            vals   = [c["hours"] for c in top3]
            colors = [next((col for col, gn in _GROUPS if gn == n), "#6B7280") for n in names]
            ypos   = list(range(len(top3)))
            max_v  = max(vals)

            ax.barh(ypos, vals, color=colors, alpha=0.85, height=0.4, zorder=3)

            self._cursor3 = mplcursors.cursor(ax, hover=mplcursors.HoverMode.Transient)

            @self._cursor3.connect("add")
            def _on_top3_hover(sel):
                y_idx = int(round(sel.target[1]))
                if 0 <= y_idx < len(top3):
                    g = top3[y_idx]
                    sel.annotation.set_text(
                        f"  {g['group']}\n"
                        f"  Loss: {g['hours']:.2f} H"
                    )
                    sel.annotation.get_bbox_patch().set(fc="#FFFFFF", alpha=0.95, ec="#E60012", lw=1)
                    sel.annotation.set_color("#212121")
                    sel.annotation.set_fontsize(8)

            ax.set_yticks(ypos)
            ax.set_yticklabels(names, fontsize=8.5, color="#6B7280")
            for i, v in enumerate(vals):
                ax.text(v + max_v * 0.03, i, f"{v:.2f} H",
                        va="center", fontsize=8, color="#6B7280")
            ax.set_xlim(0, max_v * 1.45)
            ax.set_ylim(-0.5, len(top3) - 0.5)
            ax.xaxis.grid(True, color="#F3F4F6", linewidth=0.5)
            ax.set_axisbelow(True)
        else:
            ax.set_xlim(0, 1); ax.set_ylim(0, 1)
            ax.set_xticks([]); ax.set_yticks([])
            ax.text(0.5, 0.5, "Tidak ada data",
                    transform=ax.transAxes, ha="center", va="center",
                    color="#9CA3AF", fontsize=10)

        ax.set_title("Top 3 Groups (Bln Ini)", fontsize=9, color="#6B7280", pad=5)
        ax.spines["bottom"].set_color("#D1D5DB")
        self._canvas3.draw()

    def _update_recent(self, recent: list):
        tbl = self._tbl
        tbl.setRowCount(len(recent))
        for row, r in enumerate(recent):
            date_str = (r["date"].strftime("%d %b %Y")
                        if hasattr(r["date"], "strftime") else str(r["date"]))
            tbl.setItem(row, 0, QTableWidgetItem(date_str))
            tbl.setItem(row, 1, QTableWidgetItem(r["shop"]))
            tbl.setItem(row, 2, QTableWidgetItem(f"{r['loss']:.2f}"))
            status = r.get("status") or "draft"
            it = QTableWidgetItem(status)
            it.setTextAlignment(Qt.AlignCenter)
            it.setForeground(
                QColor("#27ae60") if status == "approved" else QColor("#e67e22")
            )
            tbl.setItem(row, 3, it)
            tbl.setRowHeight(row, 30)

    def refresh_data(self, *_):
        self.load_data()

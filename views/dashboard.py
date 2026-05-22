import pyqtgraph as pg

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QTableWidget,
    QTableWidgetItem, QHeaderView, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont


class StatCard(QFrame):
    def __init__(self, title, value, subtitle="", color="#E60012"):
        super().__init__()
        self.setObjectName("statCard")
        self.setMinimumHeight(100)
        self.setStyleSheet(f"""
            #statCard {{
                background-color: rgb(40, 44, 52);
                border-radius: 10px;
                border-left: 4px solid {color};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)

        title_label = QLabel(title)
        title_label.setStyleSheet("color: rgb(150, 150, 150); font-size: 11px;")

        self.value_label = QLabel(str(value))
        self.value_label.setStyleSheet("color: #ffffff; font-size: 24px; font-weight: bold;")

        subtitle_label = QLabel(subtitle)
        subtitle_label.setStyleSheet("color: rgb(130, 130, 130); font-size: 10px;")

        layout.addWidget(title_label)
        layout.addWidget(self.value_label)
        layout.addWidget(subtitle_label)

    def update_value(self, value):
        self.value_label.setText(str(value))


class DashboardWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        header = QLabel("Dashboard Produktivitas")
        header.setStyleSheet("color: #ffffff; font-size: 16px; font-weight: bold;")
        main_layout.addWidget(header)

        # Row 1: Stat Cards
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(12)

        self.card_laporan = StatCard(
            "Total Laporan Hari Ini", "0",
            "laporan harian", "#E60012"
        )
        self.card_losstime = StatCard(
            "Total Loss Time", "0.00 H",
            "jam terbuang", "#f39c12"
        )
        self.card_produktivitas = StatCard(
            "Produktivitas", "0%",
            "dari target 87%", "#27ae60"
        )

        cards_layout.addWidget(self.card_laporan)
        cards_layout.addWidget(self.card_losstime)
        cards_layout.addWidget(self.card_produktivitas)
        main_layout.addLayout(cards_layout)

        # Row 2: Chart + Tabel
        content_layout = QHBoxLayout()
        content_layout.setSpacing(12)

        chart_frame = QFrame()
        chart_frame.setStyleSheet("""
            QFrame {
                background-color: rgb(40, 44, 52);
                border-radius: 10px;
            }
        """)
        chart_layout = QVBoxLayout(chart_frame)
        chart_layout.setContentsMargins(12, 12, 12, 12)

        chart_title = QLabel("Loss Time per Kategori (Bulan Ini)")
        chart_title.setStyleSheet("color: #ffffff; font-size: 13px; font-weight: bold;")
        chart_layout.addWidget(chart_title)

        self.chart = self.create_chart()
        chart_layout.addWidget(self.chart)

        table_frame = QFrame()
        table_frame.setStyleSheet("""
            QFrame {
                background-color: rgb(40, 44, 52);
                border-radius: 10px;
            }
        """)
        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(12, 12, 12, 12)

        table_title = QLabel("Laporan Terbaru")
        table_title.setStyleSheet("color: #ffffff; font-size: 13px; font-weight: bold; margin-bottom: 8px;")
        table_layout.addWidget(table_title)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Tanggal", "Section", "Loss Time", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: transparent;
                border: none;
                gridline-color: rgb(55, 60, 70);
            }
            QTableWidget::item {
                color: rgb(200, 200, 200);
                padding: 6px;
                background-color: rgb(45, 49, 58);
            }
            QTableWidget::item:selected {
                background-color: rgb(100, 110, 125);
                color: white;
            }
            QHeaderView::section {
                background-color: rgb(33, 37, 43);
                color: rgb(150, 150, 150);
                border: none;
                border-bottom: 1px solid rgb(55, 60, 70);
                padding: 6px;
                font-weight: bold;
            }
        """)
        self.load_table_data()
        table_layout.addWidget(self.table)

        content_layout.addWidget(chart_frame, stretch=3)
        content_layout.addWidget(table_frame, stretch=2)
        main_layout.addLayout(content_layout)

    def create_chart(self):
        pg.setConfigOption('background', (40, 44, 52))
        pg.setConfigOption('foreground', (200, 200, 200))

        plot = pg.PlotWidget()
        plot.setMinimumHeight(280)
        plot.showGrid(x=False, y=True, alpha=0.2)
        plot.getAxis('bottom').setStyle(tickFont=QFont("Segoe UI", 9))
        plot.getAxis('left').setStyle(tickFont=QFont("Segoe UI", 9))
        plot.getPlotItem().hideButtons()
        plot.setMouseEnabled(x=False, y=False)
        plot.setMenuEnabled(False)

        kategori = ["Repair", "Machine", "Setting", "Quality", "Supply", "Man", "Trial"]
        values = [2.5, 1.8, 1.2, 0.9, 0.7, 0.5, 0.3]
        colors = [
            (230, 50, 50),
            (200, 80, 50),
            (180, 100, 50),
            (160, 120, 50),
            (140, 140, 50),
            (100, 160, 50),
            (70, 180, 50),
        ]

        for i, (val, color) in enumerate(zip(values, colors)):
            bar = pg.BarGraphItem(
                x=[i], height=[val], width=0.6,
                brush=pg.mkBrush(*color, 200),
                pen=pg.mkPen(*color, width=1)
            )
            plot.addItem(bar)

        ticks = [(i, kategori[i]) for i in range(len(kategori))]
        plot.getAxis('bottom').setTicks([ticks])
        plot.setLabel('left', 'Loss Time (H)')

        return plot

    def load_table_data(self):
        dummy_data = [
            ("18 Mei 2026", "Rear Axle", "2.24 H", "Draft"),
            ("17 Mei 2026", "Welding CO2", "1.50 H", "Approved"),
            ("16 Mei 2026", "Machining", "0.75 H", "Approved"),
            ("15 Mei 2026", "Rear Axle", "3.10 H", "Draft"),
            ("14 Mei 2026", "Welding CO2", "1.20 H", "Approved"),
        ]

        self.table.setRowCount(len(dummy_data))
        for row, (tanggal, section, loss, status) in enumerate(dummy_data):
            self.table.setItem(row, 0, QTableWidgetItem(tanggal))
            self.table.setItem(row, 1, QTableWidgetItem(section))
            self.table.setItem(row, 2, QTableWidgetItem(loss))

            status_item = QTableWidgetItem(status)
            if status == "Approved":
                status_item.setForeground(QColor("#27ae60"))
            else:
                status_item.setForeground(QColor("#f39c12"))
            self.table.setItem(row, 3, status_item)

    def refresh_data(self, laporan_count=0, loss_time=0.0, produktivitas=0.0):
        self.card_laporan.update_value(str(laporan_count))
        self.card_losstime.update_value(f"{loss_time:.2f} H")
        self.card_produktivitas.update_value(f"{produktivitas:.1f}%")

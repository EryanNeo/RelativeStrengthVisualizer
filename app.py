from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget,
    QComboBox, QLabel, QHBoxLayout, QCheckBox, QPushButton
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import sys
import mplcursors

from data_fetch import get_collections, get_data, make_data, sector_map

class MplCanvas(FigureCanvas):
    def __init__(self):
        self.fig = Figure(figsize=(19, 16))
        self.ax = self.fig.add_subplot(111)
        super().__init__(self.fig)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Relative Strength Viewer")
        self.setGeometry(0, 0, 1920, 1080)

        self.stock_list = get_collections()
        if "NIFTY 50" not in self.stock_list:
            self.stock_list.insert(0, "NIFTY 50")
        self.stock_list.sort()

        self.color_list = ['blue', 'red', 'green', 'orange', 'purple', 'brown', 'black']
        self.plot_controls = []
        self.auto_offset = 0

        main_layout = QVBoxLayout()
        top_controls = QHBoxLayout()
        nav_layout = QHBoxLayout()
        controls_row = QHBoxLayout()

        # Sector Mode
        self.sector_mode_checkbox = QCheckBox("Sector Mode")
        self.sector_mode_checkbox.stateChanged.connect(self.handle_sector_mode)

        self.sector_combo = QComboBox()
        self.sector_combo.addItems(sorted(sector_map.keys()))
        self.sector_combo.setEnabled(False)
        self.sector_combo.currentIndexChanged.connect(self.populate_sector_comboboxes)

        top_controls.addWidget(self.sector_mode_checkbox)
        top_controls.addWidget(self.sector_combo)

        # Auto Populate controls
        self.auto_mode_checkbox = QCheckBox("Auto Populate Mode")
        self.auto_mode_checkbox.stateChanged.connect(self.handle_auto_mode)

        self.prev_button = QPushButton("← Prev")
        self.next_button = QPushButton("Next →")
        self.prev_button.clicked.connect(self.prev_batch)
        self.next_button.clicked.connect(self.next_batch)

        nav_layout.addWidget(self.auto_mode_checkbox)
        nav_layout.addWidget(self.prev_button)
        nav_layout.addWidget(self.next_button)

        # Stock controls
        for i in range(7):
            pair_layout = QHBoxLayout()
            checkbox = QCheckBox()
            combobox = QComboBox()
            combobox.addItems(self.stock_list)

            checkbox.setChecked(i == 0)
            if i == 0:
                combobox.setCurrentText("NIFTY 50")

            checkbox.stateChanged.connect(self.update_chart)
            combobox.currentIndexChanged.connect(self.update_chart)

            pair_layout.addWidget(combobox)
            pair_layout.addWidget(checkbox)

            wrapper = QWidget()
            wrapper.setLayout(pair_layout)

            controls_row.addWidget(wrapper)
            self.plot_controls.append((checkbox, combobox))

        self.canvas = MplCanvas()

        main_layout.addLayout(top_controls)
        main_layout.addLayout(nav_layout)
        main_layout.addLayout(controls_row)
        main_layout.addWidget(self.canvas)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # Initial plot
        self.update_chart()

    def handle_sector_mode(self, state):
        is_checked = state == 2
        self.sector_combo.setEnabled(is_checked)

        if is_checked:
            self.auto_mode_checkbox.setChecked(False)
            self.plot_controls[0][1].setCurrentText("NIFTY 50")
            self.plot_controls[0][1].setEnabled(False)
            self.plot_controls[0][0].setChecked(True)

            for i in range(1, 7):
                self.plot_controls[i][1].setEnabled(False)

            self.populate_sector_comboboxes()
        else:
            self.sector_combo.setEnabled(False)
            self.plot_controls[0][1].setEnabled(True)
            for i in range(1, 7):
                self.plot_controls[i][1].setEnabled(True)

    def populate_sector_comboboxes(self):
        sector = self.sector_combo.currentText()
        stocks = sector_map.get(sector, [])

        for i in range(1, 7):
            combobox = self.plot_controls[i][1]
            checkbox = self.plot_controls[i][0]
            if i - 1 < len(stocks):
                combobox.setCurrentText(stocks[i - 1])
                checkbox.setChecked(True)
            else:
                combobox.setCurrentIndex(0)
                checkbox.setChecked(False)

        self.update_chart()

    def handle_auto_mode(self, state):
        if state:
            self.sector_mode_checkbox.setChecked(False)
            self.plot_controls[0][1].setCurrentText("NIFTY 50")
            self.plot_controls[0][1].setEnabled(False)
            self.plot_controls[0][0].setChecked(True)

            for i in range(1, 7):
                self.plot_controls[i][1].setEnabled(False)
                self.plot_controls[i][0].setChecked(True)

            self.populate_auto_comboboxes()
        else:
            self.plot_controls[0][1].setEnabled(True)
            for i in range(1, 7):
                self.plot_controls[i][1].setEnabled(True)

    def populate_auto_comboboxes(self):
        start = self.auto_offset
        end = start + 6

        slice_stocks = [s for s in self.stock_list if s != "NIFTY 50"]
        visible_stocks = slice_stocks[start:end]

        for i in range(1, 7):
            combobox = self.plot_controls[i][1]
            checkbox = self.plot_controls[i][0]
            if i - 1 < len(visible_stocks):
                combobox.setCurrentText(visible_stocks[i - 1])
                checkbox.setChecked(True)
            else:
                combobox.setCurrentIndex(0)
                checkbox.setChecked(False)

        self.update_chart()

    def next_batch(self):
        if not self.auto_mode_checkbox.isChecked():
            return
        max_offset = len(self.stock_list) - 1 - 6
        if self.auto_offset + 6 <= max_offset:
            self.auto_offset += 6
            self.populate_auto_comboboxes()

    def prev_batch(self):
        if not self.auto_mode_checkbox.isChecked():
            return
        if self.auto_offset >= 6:
            self.auto_offset -= 6
            self.populate_auto_comboboxes()

    def update_chart(self):
        self.canvas.ax.clear()
        lines = []

        for i, (checkbox, combobox) in enumerate(self.plot_controls):
            if checkbox.isChecked():
                key = combobox.currentText()
                df = get_data(key)
                df = make_data(df)

                if df and "date" in df[0] and "baseChange" in df[0]:
                    dates = [row["date"] for row in df]
                    values = [row["baseChange"] for row in df]

                    line, = self.canvas.ax.plot(
                        dates,
                        values,
                        label=key,
                        color=self.color_list[i % len(self.color_list)],
                        linewidth=2,
                        linestyle="--" if key == "NIFTY 50" else "-"
                    )
                    lines.append(line)

        self.canvas.ax.set_title("Base Change Comparison")
        self.canvas.ax.set_xlabel("Date")
        self.canvas.ax.set_ylabel("Base Change")
        self.canvas.ax.legend()
        self.canvas.ax.grid(True)

        mplcursors.cursor(lines, hover=True)
        self.canvas.draw()


# Run the app
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec())

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget,
    QComboBox, QLabel, QHBoxLayout, QCheckBox
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import sys
import mplcursors

from data_fetch import get_collections, get_data, make_data

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
        self.stock_list.sort()
        self.color_list = ['blue', 'red', 'green', 'orange', 'purple']
        self.plot_controls = []

            # Layouts
        main_layout = QVBoxLayout()
        controls_row = QHBoxLayout()

        self.plot_controls = []

        for i in range(5):
            pair_layout = QHBoxLayout()
            # pair_layout.setSpacing(-50)  # Or even 0 if you want it tighter
            # pair_layout.setContentsMargins(0, 0, 0, 0)
            checkbox = QCheckBox()
            combobox = QComboBox()
            combobox.addItems(self.stock_list)

            checkbox.setChecked(i == 0)  # Only first visible
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

        main_layout.addLayout(controls_row)
        main_layout.addWidget(self.canvas)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)



        # Initial plot
        self.update_chart()

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

        # Add tooltips
        mplcursors.cursor(lines, hover=True)

        self.canvas.draw()


        
# Run the app
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    # app.showFullScreen()  # 👈 Fullscreen mode on launch
    window.showMaximized()
    sys.exit(app.exec())



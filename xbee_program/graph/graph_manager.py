from PyQt5.QtWidgets import QWidget, QVBoxLayout
from collections import deque
import pyqtgraph as pg

# 커스텀 x축
class TimeAxisItem(pg.AxisItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.timestamps = []

    def set_timestamps(self, timestamps):
        self.timestamps = timestamps

    def tickStrings(self, values, scale, spacing):
        return [self.timestamps[int(v)] if 0 <= int(v) < len(self.timestamps) else '' for v in values]

class SingleGraphManager(QWidget):
    def __init__(self, title, unit, color="blue", max_points=100, y_range=(0, 30)):
        super().__init__()
        self.unit = unit
        self.max_points = max_points
        self.timestamps = deque(maxlen=max_points)
        self.values = deque(maxlen=max_points)

        self.time_axis = TimeAxisItem(orientation='bottom')
        self.plot_widget = pg.PlotWidget(axisItems={'bottom': self.time_axis}, title=title)
        self.plot_widget.setBackground('w')
        self.plot_widget.setLabel('left', unit, **{'color': '#000', 'font-size': '10pt'})
        self.plot_widget.setLabel('bottom', '시간', **{'color': '#000', 'font-size': '10pt'})
        self.plot_widget.getAxis('left').setPen(pg.mkPen(color='black'))
        self.plot_widget.getAxis('bottom').setPen(pg.mkPen(color='black'))
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)

        # 🔥 여백 제거
        self.plot_widget.setContentsMargins(0, 0, 0, 0)
        self.plot_widget.getPlotItem().layout.setContentsMargins(0, 0, 0, 0)

        pen = pg.mkPen(color=color, width=2)
        symbol_brush = pg.mkBrush(color=color)
        self.plot = self.plot_widget.plot([], [], pen=pen, symbol='o', symbolBrush=symbol_brush, symbolSize=6)

        layout = QVBoxLayout()
        layout.addWidget(self.plot_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.fixed_y_range = y_range

    def update_graph(self, value, timestamp_str=None):
        self.values.append(value)
        if timestamp_str:
            self.timestamps.append(timestamp_str[11:19])  # HH:MM:SS
        else:
            self.timestamps.append("")

        x = list(range(len(self.values)))
        y = list(self.values)

        self.plot.setData(x, y)
        self.time_axis.set_timestamps(list(self.timestamps))

        # ✅ 자동 줌인 (데이터 범위에 맞게 확대)
        self.plot_widget.enableAutoRange(axis='x', enable=True)
        self.plot_widget.enableAutoRange(axis='y', enable=True)

    def clear(self):
        self.values.clear()
        self.timestamps.clear()
        self.plot.clear()

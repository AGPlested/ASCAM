# pylint: disable=E0611
from PySide2.QtWidgets import (
    QVBoxLayout,
    QWidget,
)

import pyqtgraph as pg
from ascam.utils import clear_qt_layout


class PlotFrame(QWidget):
    def __init__(self, main):
        super().__init__()
        self.main = main

        # qt attributes
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # plot variables
        self.show_piezo = True
        self.show_command = False
        self.show_grid = True

        self.init_plots()

    def init_plots(self):
        self.trace_plot = pg.PlotWidget(name=f"trace")
        self.trace_plot.setBackground('w')
        self.trace_plot.setLabel('left', 'Current', f'{self.main.data.trace_unit}')
        ind = int(self.show_command)
        self.layout.insertWidget(ind, self.trace_plot)

        if self.show_piezo:
            self.piezo_plot = pg.PlotWidget(name=f"piezo")
            self.piezo_plot.setLabel('left', 'Piezo', f'{self.main.data.piezo_unit}')
            self.piezo_plot.setBackground('w')
            self.piezo_plot.setLabel('bottom', 'time', f'{self.main.data.time_unit}')
            self.piezo_plot.setXLink(self.trace_plot)
            ind = 1 + int(self.show_command)
            self.layout.insertWidget(ind, self.piezo_plot)
        else:
            self.trace_plot.setLabel('bottom', 'time', f'{self.main.data.time_unit}')

        if self.show_command:
            self.command_plot = pg.PlotWidget(name=f"command")
            self.command_plot.setBackground('w')
            self.command_plot.setLabel('left', 'Command', f'{self.main.data.command_unit}')
            self.command_plot.setXLink(self.trace_plot)
            self.layout.insertWidget(0, self.command_plot)

        if self.show_grid:
            self.trace_plot.showGrid(x=True, y=True)
            if self.show_piezo:
                self.piezo_plot.showGrid(x=True, y=True)
            if self.show_command:
                self.command_plot.showGrid(x=True, y=True)

    def togggle_grid(self):
        clear_qt_layout(self.layout)
        self.show_grid = not self.show_grid
        self.init_plots()
        self.plot_episode()

    def toggle_command(self):
        clear_qt_layout(self.layout)
        self.show_command = not self.show_command
        self.init_plots()
        self.plot_episode()

    def toggle_piezo(self):
        clear_qt_layout(self.layout)
        self.show_piezo = not self.show_piezo
        self.init_plots()
        self.plot_episode()

    def clear_plots(self):
        self.trace_plot.clear()
        if self.show_command:
            self.command_plot.clear()
        if self.show_piezo:
            self.piezo_plot.clear()

    def plot_episode(self):
        self.clear_plots()

        pen = pg.mkPen(color='b')
        self.trace_plot.plot(self.main.data.time, self.main.data.trace, pen=pen)
        if self.main.data.idealization is not None:
            id_pen = pg.mkPen(color='o')
            self.trace_plot.plot(self.main.data.time, self.main.data.idealization, pen=id_pen)
        if self.show_command:
            self.command_plot.plot(self.main.data.time, self.main.data.command, pen=pen)
        if self.show_piezo:
            self.piezo_plot.plot(self.main.data.time, self.main.data.piezo, pen=pen)

import logging

# pylint: disable=E0611
from PySide2 import QtCore 
from PySide2.QtWidgets import QWidget, QGridLayout
import numpy as np
import pyqtgraph as pg

from ascam.utils import clear_qt_layout


debug_logger = logging.getLogger("ascam.debug")


ORANGE = (255, 153, 0)


class PlotFrame(QWidget):
    def __init__(self, main):
        super().__init__()
        self.main = main

        # qt attributes
        self.layout = QGridLayout()
        self.setLayout(self.layout)

        # plot variables
        self.show_piezo = True
        self.show_command = False
        self.show_grid = True
        self.hist_x_range = None
        self.hist_y_max = None

        self.init_plots()
        self.init_hist()

    def init_plots(self):
        self.trace_plot = pg.PlotWidget(name=f"trace")
        self.trace_plot.setBackground("w")
        self.trace_plot.setLabel("left", "Current", units="A")
        ind = int(self.show_command)
        self.layout.addWidget(self.trace_plot, ind, 0, )

        if self.show_piezo:
            self.piezo_plot = pg.PlotWidget(name=f"piezo")
            self.piezo_plot.setLabel("left", "Piezo", units="V")
            self.piezo_plot.setBackground("w")
            self.piezo_plot.setLabel("bottom", "time", units="s")
            self.piezo_plot.setXLink(self.trace_plot)
            ind = 1 + int(self.show_command)
            self.layout.addWidget(self.piezo_plot, ind, 0, )
        else:
            self.trace_plot.setLabel("bottom", "time", units="s")

        if self.show_command:
            self.command_plot = pg.PlotWidget(name=f"command")
            self.command_plot.setBackground("w")
            self.command_plot.setLabel("left", "Command", units="V")
            self.command_plot.setXLink(self.trace_plot)
            self.layout.addWidget(self.command_plot, 0, 0)

        if self.show_grid:
            self.trace_plot.showGrid(x=True, y=True)
            if self.show_piezo:
                self.piezo_plot.showGrid(x=True, y=True)
            if self.show_command:
                self.command_plot.showGrid(x=True, y=True)

        self.amp_lines = []
        self.theta_lines = []

    def init_hist(self):
        self.hist = pg.PlotWidget()
        row = int(self.show_command)
        self.layout.addWidget(self.hist, row, 1, )
        self.hist.setLabel("right", "Current", units="A")
        self.hist.getAxis('left').setTicks([])
        self.hist.setBackground("w")
        self.hist.setYLink(self.trace_plot)
        if self.show_grid:
            self.hist.showGrid(x=True, y=True)

    def plot_all(self):
        self.clear_plots()
        self.clear_hist()
        self.plot_episode()
        self.draw_series_hist()
        self.draw_episode_hist()

    def update_plots(self):
        self.update_episode()
        self.update_episode_hist()

    def update_episode(self):
        self.clear_plots()
        self.plot_episode()

    def update_episode_hist(self):
        heights, bins, = self.main.data.episode_hist(density=True)[:2]
        self.episode_hist.setData(bins,heights)

    def draw_episode_hist(self):
        pen = pg.mkPen(color='b')
        heights, bins, = self.main.data.episode_hist(density=True)[:2]
        self.episode_hist = pg.PlotDataItem(bins,heights,stepMode=True,pen=pen)
        self.hist.addItem(self.episode_hist)
        self.hist.getPlotItem().invertX(True)
        self.episode_hist.rotate(90)
        y_max = self.hist.getAxis('bottom').range[1]
        if self.hist_y_max is not None:
            y_max = self.hist_y_max
        self.hist.getAxis('bottom').setRange(0, y_max)
        if self.hist_x_range is not None:
            self.hist.getAxis('right').setRange(*self.hist_x_range)

    def draw_series_hist(self):
        pen = pg.mkPen(color=(200,50,50))
        heights, bins, = self.main.data.series_hist(density=True)[:2]
        self.series_hist = pg.PlotDataItem(bins,heights,stepMode=True,pen=pen)
        self.hist.addItem(self.series_hist)
        self.hist.getPlotItem().invertX(True)
        self.series_hist.rotate(90)
        self.hist_y_max = self.hist.getAxis('bottom').range[1]
        self.hist_x_range = self.hist.getAxis('right').range
        self.hist.getAxis('bottom').setRange(0, self.hist_y_max)

    def plot_episode(self):
        pen = pg.mkPen(color="b")
        self.trace_plot.plot(
            self.main.data.episode.time, self.main.data.episode.trace, pen=pen
        )
        if self.hist_x_range is not None:
            self.trace_plot.getAxis('left').setRange(*self.hist_x_range)
            self.hist.setYLink(self.trace_plot)
        if self.main.data.episode.idealization is not None:
            id_pen = pg.mkPen(color=ORANGE)
            self.trace_plot.plot(
                self.main.data.episode.id_time,
                self.main.data.episode.idealization,
                pen=id_pen,
            )
        if self.show_command:
            self.command_plot.plot(
                self.main.data.episode.time, self.main.data.episode.command, pen=pen
            )
        if self.show_piezo:
            self.piezo_plot.plot(
                self.main.data.episode.time, self.main.data.episode.piezo, pen=pen
            )

    def plot_theta_lines(self, thetas):
        pen = pg.mkPen(color="r", style=QtCore.Qt.DashLine)
        thetas = np.asarray(thetas)
        self.clear_theta_lines()
        self.theta_lines = []
        time = self.main.data.episode.time
        for theta in thetas:
            self.theta_lines.append(
                self.trace_plot.plot(time, np.ones(len(time)) * theta, pen=pen)
            )

    def plot_amp_lines(self, amps):
        debug_logger.debug(f"plotting amps at {amps}")
        pen = pg.mkPen(color=ORANGE, style=QtCore.Qt.DashLine)
        self.clear_amp_lines()
        self.amp_lines = []
        time = self.main.data.episode.time
        for amp in amps:
            self.amp_lines.append(
                self.trace_plot.plot(time, np.ones(len(time)) * amp, pen=pen)
            )

    def clear_hist(self):
        self.hist.clear()

    def clear_plots(self):
        self.trace_plot.clear()
        if self.show_command:
            self.command_plot.clear()
        if self.show_piezo:
            self.piezo_plot.clear()

    def clear_amp_lines(self):
        for a in self.amp_lines:
            self.trace_plot.removeItem(a)

    def clear_theta_lines(self):
        for a in self.theta_lines:
            self.trace_plot.removeItem(a)

    def togggle_grid(self):
        clear_qt_layout(self.layout)
        self.show_grid = not self.show_grid
        self.init_plots()
        self.init_hist()
        self.plot_episode()
        self.draw_series_hist()
        self.draw_episode_hist()

    def toggle_command(self):
        clear_qt_layout(self.layout)
        self.show_command = not self.show_command
        self.init_plots()
        self.init_hist()
        self.plot_episode()
        self.draw_series_hist()
        self.draw_episode_hist()

    def toggle_piezo(self):
        clear_qt_layout(self.layout)
        self.show_piezo = not self.show_piezo
        self.init_plots()
        self.init_hist()
        self.plot_episode()
        self.draw_series_hist()
        self.draw_episode_hist()

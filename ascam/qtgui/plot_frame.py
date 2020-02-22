import logging

# pylint: disable=E0611
from PySide2 import QtCore
from PySide2.QtWidgets import (
    QVBoxLayout,
    QWidget,
)
import numpy as np
import pyqtgraph as pg

from ascam.utils import clear_qt_layout


debug_logger = logging.getLogger("ascam.debug")


ORANGE=(255,153,0)


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
        self.trace_plot.setLabel('left', 'Current', units='A') 
        ind = int(self.show_command)
        self.layout.insertWidget(ind, self.trace_plot)

        if self.show_piezo:
            self.piezo_plot = pg.PlotWidget(name=f"piezo")
            self.piezo_plot.setLabel('left', 'Piezo', units='V')
            self.piezo_plot.setBackground('w')
            self.piezo_plot.setLabel('bottom', 'time', units='s')
            self.piezo_plot.setXLink(self.trace_plot)
            ind = 1 + int(self.show_command)
            self.layout.insertWidget(ind, self.piezo_plot)
        else:
            self.trace_plot.setLabel('bottom', 'time', units='s')

        if self.show_command:
            self.command_plot = pg.PlotWidget(name=f"command")
            self.command_plot.setBackground('w')
            self.command_plot.setLabel('left', 'Command', units='V')
            self.command_plot.setXLink(self.trace_plot)
            self.layout.insertWidget(0, self.command_plot)

        if self.show_grid:
            self.trace_plot.showGrid(x=True, y=True)
            if self.show_piezo:
                self.piezo_plot.showGrid(x=True, y=True)
            if self.show_command:
                self.command_plot.showGrid(x=True, y=True)
        
        self.amp_lines = []
        self.theta_lines = []

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
        self.trace_plot.plot(self.main.data.episode.time, self.main.data.episode.trace, pen=pen)
        if self.main.data.episode.idealization is not None:
            id_pen = pg.mkPen(color=ORANGE)
            self.trace_plot.plot(self.main.data.episode.time, self.main.data.episode.idealization, pen=id_pen)
        if self.show_command:
            self.command_plot.plot(self.main.data.episode.time,
                    self.main.data.episode.command, pen=pen)
        if self.show_piezo:
            self.piezo_plot.plot(self.main.data.episode.time,
                    self.main.data.episode.piezo, pen=pen)

    def plot_theta_lines(self, thetas):
        pen = pg.mkPen(color='r', style=QtCore.Qt.DashLine)
        thetas = np.asarray(thetas)
        self.clear_theta_lines()
        self.theta_lines = []
        time = self.main.data.episode.time
        for theta in thetas:
            self.theta_lines.append(self.trace_plot.plot(time, np.ones(len(time))*theta, pen=pen))

    def plot_amp_lines(self, amps):
        debug_logger.debug(f"plotting amps at {amps}")
        pen = pg.mkPen(color=ORANGE, style=QtCore.Qt.DashLine)
        self.clear_amp_lines()
        self.amp_lines = []
        time = self.main.data.episode.time
        for amp in amps:
            self.amp_lines.append(self.trace_plot.plot(time, np.ones(len(time))*amp, pen=pen))

    def clear_amp_lines(self):
        for a in self.amp_lines:
            self.trace_plot.removeItem(a)

    def clear_theta_lines(self):
        for a in self.theta_lines:
            self.trace_plot.removeItem(a)

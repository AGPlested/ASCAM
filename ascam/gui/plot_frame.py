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
        self.show_grid = True
        self.hist_x_range = None
        self.hist_y_range = None

        self.tc_tracking = False

        self.init_plots()
        self.init_hist()

        self.amp_lines = []
        self.amp_hist_lines = []
        self.theta_lines = []
        self.theta_hist_lines = []

    @property
    def show_command(self):
        return self.main.show_command.isChecked() and self.main.data.has_command

    @show_command.setter
    def show_command(self, val):
        self._show_command = val

    @property
    def show_piezo(self):
        debug_logger.debug(f"data has piezo = {self.main.data.has_piezo}")
        return self.main.show_piezo.isChecked() and self.main.data.has_piezo

    @show_piezo.setter
    def show_piezo(self, val):
        self._show_piezo = val

    def init_plots(self):
        self.trace_plot = pg.PlotWidget(viewBox=CustomViewBox(self), name=f"trace")
        self.trace_plot.setBackground("w")
        self.trace_plot.setLabel("left", "Current", units="A")
        ind = int(self.show_command)
        self.layout.addWidget(self.trace_plot, ind, 0)
        self.layout.setRowStretch(ind, 2)
        self.layout.setColumnStretch(0, 2)
        self.layout.setColumnStretch(1, 1)

        if self.show_piezo:
            self.piezo_plot = pg.PlotWidget(viewBox=CustomViewBox(self), name=f"piezo")
            self.piezo_plot.setLabel("left", "Piezo", units="V")
            self.piezo_plot.setBackground("w")
            self.piezo_plot.setLabel("bottom", "time", units="s")
            self.piezo_plot.setXLink(self.trace_plot)
            ind = 1 + int(self.show_command)
            self.layout.addWidget(self.piezo_plot, ind, 0)
            self.layout.setRowStretch(ind, 1)
        else:
            self.piezo_plot = None
            self.trace_plot.setLabel("bottom", "time", units="s")

        if self.show_command:
            self.command_plot = pg.PlotWidget(
                viewBox=CustomViewBox(self), name=f"command"
            )
            self.command_plot.setBackground("w")
            self.command_plot.setLabel("left", "Command", units="V")
            self.command_plot.setXLink(self.trace_plot)
            self.layout.addWidget(self.command_plot, 0, 0)
            self.layout.setRowStretch(0, 1)
        else:
            self.command_plot = None

        if self.show_grid:
            self.trace_plot.showGrid(x=True, y=True)
            if self.show_piezo:
                self.piezo_plot.showGrid(x=True, y=True)
            if self.show_command:
                self.command_plot.showGrid(x=True, y=True)

    def init_hist(self):
        self.hist = pg.PlotWidget(viewBox=CustomViewBox(self))
        row = int(self.show_command)
        self.layout.addWidget(self.hist, row, 1)
        self.hist.setLabel("right", "Current", units="A")
        self.hist.getAxis("left").setTicks([])
        self.hist.setBackground("w")
        self.hist.setYLink(self.trace_plot)
        if self.show_grid:
            self.hist.showGrid(x=True, y=True)

    def plot_all(self):
        debug_logger.debug(f"redoing all plots for {self.main.data.current_datakey}")
        self.clear_plots()
        self.clear_hist()
        self.draw_series_hist()
        self.draw_episode_hist()
        self.plot_episode()

    def update_plots(self):
        self.update_episode()
        self.update_episode_hist()

    def update_episode(self):
        self.clear_plots()
        self.plot_episode()
        try:
            self.plot_tc_params()
        except AttributeError:
            pass

    def update_episode_hist(self):
        heights, bins, = self.main.data.episode_hist()[:2]
        heights = np.asarray(heights, dtype=np.float)
        heights /= np.max(heights)
        self.episode_hist.setData(bins, heights)

    def draw_episode_hist(self):
        pen = pg.mkPen(color="b")
        heights, bins, = self.main.data.episode_hist()[:2]
        heights = np.asarray(heights, dtype=np.float)
        heights /= np.max(heights)
        self.episode_hist = pg.PlotDataItem(bins, heights, stepMode=True, pen=pen)
        self.hist.addItem(self.episode_hist)  # ignoreBounds=True?
        self.hist.getPlotItem().invertX(True)
        self.episode_hist.rotate(90)
        y_max = self.hist.getAxis("bottom").range
        if self.hist_y_range is not None:
            y_max = self.hist_y_range[1]
        self.hist.getAxis("bottom").setRange(0, y_max)
        if self.hist_x_range is not None:
            self.hist.getAxis("right").setRange(*self.hist_x_range)

    def draw_series_hist(self):
        pen = pg.mkPen(color=(200, 50, 50))
        heights, bins, = self.main.data.series_hist()[:2]
        heights = np.asarray(heights, dtype=np.float)
        heights /= np.max(heights)
        self.series_hist = pg.PlotDataItem(bins, heights, stepMode=True, pen=pen)
        self.hist.addItem(self.series_hist)
        self.hist.getPlotItem().invertX(True)
        self.series_hist.rotate(90)
        self.hist_y_range = self.hist.getAxis("bottom").range
        self.hist_x_range = self.hist.getAxis("right").range
        self.hist.getAxis("bottom").setRange(0, self.hist_y_range[1])

    def plot_episode(self):
        debug_logger.debug(
            f"plotting episode {self.main.data.episode.n_episode} of series {self.main.data.current_datakey}"
        )
        pen = pg.mkPen(color="b")
        self.trace_plot.plot(
            self.main.data.episode.time, self.main.data.episode.trace, pen=pen
        )
        try:
            id_pen = pg.mkPen(color=ORANGE)
            self.trace_plot.plot(
                self.main.tc_frame.time(),
                self.main.tc_frame.idealization(),
                # self.main.data.episode.id_time,
                # self.main.data.episode.idealization,
                pen=id_pen,
            )
        except AttributeError as e:
            debug_logger.debug("cannot plot idealization")
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
        self.theta_hist_lines = []
        time = self.main.data.episode.time
        hist_x = np.arange(
            np.min([*self.hist_y_range]), np.max([*self.hist_y_range]), 0.1
        )
        for theta in thetas:
            self.theta_lines.append(
                self.trace_plot.plot(time, np.ones(len(time)) * theta, pen=pen)
            )
            self.theta_hist_lines.append(
                self.hist.plot(hist_x, np.ones(len(hist_x)) * theta, pen=pen)
            )

    def plot_amp_lines(self, amps):
        debug_logger.debug(f"plotting amps at {amps}")
        pen = pg.mkPen(color=ORANGE, style=QtCore.Qt.DashLine)
        self.clear_amp_lines()
        self.amp_lines = []
        self.amp_hist_lines = []
        time = self.main.data.episode.time
        hist_x = np.arange(
            np.min([*self.hist_y_range]), np.max([*self.hist_y_range]), 0.1
        )
        for amp in amps:
            self.amp_lines.append(
                self.trace_plot.plot(time, np.ones(len(time)) * amp, pen=pen)
            )
            self.amp_hist_lines.append(
                self.hist.plot(hist_x, np.ones(len(hist_x)) * amp, pen=pen)
            )

    def plot_tc_params(self):
        amps, thresh, resolution, intrp_factor = self.main.tc_frame.get_params()
        if self.main.tc_frame.current_tab.show_amp_check.isChecked():
            self.plot_amp_lines(amps)
        else:
            self.clear_amp_lines()
        if self.main.tc_frame.current_tab.show_threshold_check.isChecked():
            self.plot_theta_lines(thresh)
        else:
            self.clear_theta_lines()

    def clear_hist(self):
        debug_logger.debug(f"clearing histogram")
        self.hist.clear()

    def clear_plots(self):
        debug_logger.debug(f"clearing plots")
        self.trace_plot.clear()
        if self.show_command and self.command_plot is not None:
            self.command_plot.clear()
        if self.show_piezo and self.piezo_plot is not None:
            self.piezo_plot.clear()

    def clear_amp_lines(self):
        for a in self.amp_lines:
            self.trace_plot.removeItem(a)
        for a in self.amp_hist_lines:
            self.hist.removeItem(a)

    def clear_theta_lines(self):
        for a in self.theta_lines:
            self.trace_plot.removeItem(a)
        for a in self.theta_hist_lines:
            self.hist.removeItem(a)

    def togggle_grid(self):
        clear_qt_layout(self.layout)
        self.show_grid = not self.show_grid
        self.init_plots()
        self.init_hist()
        self.plot_episode()
        self.draw_series_hist()
        self.draw_episode_hist()

    def toggle_command(self):
        debug_logger.debug("toggling command plot")
        clear_qt_layout(self.layout)
        self.init_plots()
        self.init_hist()
        self.plot_episode()
        self.draw_series_hist()
        self.draw_episode_hist()

    def toggle_piezo(self):
        debug_logger.debug("toggling piezo plot")
        clear_qt_layout(self.layout)
        self.init_plots()
        self.init_hist()
        self.plot_episode()
        self.draw_series_hist()
        self.draw_episode_hist()


class CustomViewBox(pg.ViewBox):
    def __init__(self, parent, *args, **kwds):
        pg.ViewBox.__init__(self, *args, **kwds)
        self.setMouseMode(self.PanMode)
        self.parent = parent
        self.setMouseEnabled(x=True, y=False)
        self.setAutoVisible(x=False, y=True)

    def mouseClickEvent(self, ev):
        if ev.button() == QtCore.Qt.RightButton:
            self.autoRange()
            self.enableAutoRange(x=False, y=True)
            self.setAutoVisible(x=False, y=True)
        ev.accept()

    def mouseDragEvent(self, ev, axis=1):
        if ev.button() == QtCore.Qt.LeftButton:
            self.setMouseEnabled(x=True, y=True)
            if self.parent.tc_tracking:
                pos = self.mapSceneToView(ev.pos()).y()
                self.parent.main.tc_frame.track_cursor(pos)
            elif ev.modifiers() == QtCore.Qt.ControlModifier:
                self.setMouseMode(self.RectMode)
                pg.ViewBox.mouseDragEvent(self, ev)
            else:
                self.setMouseMode(self.PanMode)
                pg.ViewBox.mouseDragEvent(self, ev)
        else:
            pg.ViewBox.mouseDragEvent(self, ev)
        ev.accept()
        self.setMouseEnabled(x=True, y=False)

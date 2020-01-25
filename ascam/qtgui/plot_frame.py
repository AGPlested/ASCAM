from PySide2.QtWidgets import (QListWidget, QLabel, QHBoxLayout, QVBoxLayout, 
        QGridLayout, QWidget, QPushButton, QMainWindow, QApplication, QToolBar, 
        QStatusBar)

import pyqtgraph as pg
import numpy as np


class PlotFrame(QWidget):
    def __init__(self, main):
        super().__init__()
        
        self.main = main

        self.trace_plot = pg.PlotWidget(name=f"trace")
        self.piezo_plot = pg.PlotWidget(name=f"piezo")
        self.command_plot = pg.PlotWidget(name=f"command")
        # self.trace_plot = pg.PlotWidget(name=f"Current {self.main.data.trace_unit}")
        # self.piezo_plot = pg.PlotWidget(name=f"Piezo Voltage {self.main.data.piezo_unit}")
        # self.command_plot = pg.PlotWidget(name=f"Command Voltage {self.main.data.command_unit}")

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.command_plot)
        self.layout.addWidget(self.trace_plot)
        self.layout.addWidget(self.piezo_plot)

        self.setLayout(self.layout)

    def clear_plots(self):
        self.trace_plot.clear()
        self.command_plot.clear()
        self.piezo_plot.clear()

    def plot_episode(self, n):
        self.clear_plots()
        episode = self.main.data.series[n]
        self.trace_plot.plot(episode.time, episode.trace)
        self.command_plot.plot(episode.time, episode.command)
        self.piezo_plot.plot(episode.time, episode.piezo)


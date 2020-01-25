from PySide2.QtWidgets import (QListWidget, QLabel, QHBoxLayout, QVBoxLayout, 
        QGridLayout, QWidget, QPushButton, QMainWindow, QApplication, QToolBar, 
        QStatusBar)

import pyqtgraph as pg
import numpy as np


class PlotFrame(QWidget):
    def __init__(self):
        super().__init__()

        x = np.arange(-3*np.pi, 3*np.pi, 0.1)
        y = np.sinc(x)

        plot_widget = pg.PlotWidget(name='test')
        plot_widget.plot(x,y)

        self.layout = QVBoxLayout()
        self.layout.addWidget(plot_widget)

        self.setLayout(self.layout)

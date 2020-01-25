# from PySide2.QtCore import Qt
from PySide2.QtWidgets import (QListWidget, QLabel, QHBoxLayout, QVBoxLayout,
        QGridLayout, QWidget, QPushButton, QMainWindow, QApplication, QToolBar,
        QStatusBar, QFileDialog)
from PySide2.QtGui import QPalette, QColor
# from PyQt5.QtWidgets import (QListWidget, QLabel, QHBoxLayout, QVBoxLayout, QGridLayout, QWidget, 
#         QPushButton, QMainWindow, QApplication, QToolBar, QStatusBar)
# from PyQt5.QtGui import QPalette, QColor

# from PySide2.QtCharts import QtCharts

from ascam.qtgui.export_fa_dialog import ExportFADialog
from ascam.qtgui.export_file_dialog import ExportFileDialog
from ascam.qtgui.filter_frame import FilterFrame
from ascam.qtgui.baseline_frame import BaselineFrame
from ascam.qtgui.plot_frame import PlotFrame
from ascam.qtgui.episode_frame import EpisodeFrame
from ascam.qtgui.idealization_frame import IdealizationFrame

from ascam.core.recording import Recording


class Color(QLabel):
    def __init__(self, color, text, *args, **kwargs):
        super(Color, self).__init__(text, *args, **kwargs)
        self.setAutoFillBackground(True)

        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(color))
        self.setPalette(palette)


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.setWindowTitle("cuteSCAM")

        self.central_layout = QGridLayout()
        self.central_widget = QWidget()
        self.central_widget.setLayout(self.central_layout)
        self.setCentralWidget(self.central_widget)

        self._create_widgets()

        self._create_menu()

    def _create_menu(self):
        self.file_menu = self.menuBar().addMenu("File")
        self.file_menu.addAction('Open File', self.open_file)
        self.file_menu.addAction('Save', self.save_to_file)
        self.file_menu.addAction('Export', lambda: ExportFileDialog())
        self.file_menu.addAction('Export Idealization', self.export_idealization)
        self.file_menu.addAction('Export Events', self.export_events)
        self.file_menu.addAction('Export First Activation', lambda: ExportFADialog())
        self.file_menu.addSeparator()
        self.file_menu.addAction('Quit', self.close)

        self.processing_menu = self.menuBar().addMenu("Processing")
        self.processing_menu.addAction("Baseline Correction", lambda: BaselineFrame())
        self.processing_menu.addAction("Filter", lambda: FilterFrame())

        self.analysis_menu = self.menuBar().addMenu("Analysis")
        self.analysis_menu.addAction("Idealize", self.launch_idealization)
        self.analysis_menu.addAction("First Activation", self.launch_fa_analysis)

        self.plot_menu = self.menuBar().addMenu("Plots")
        self.plot_menu.addAction
        self.histogram_menu = self.menuBar().addMenu("Histogram")

    def _create_widgets(self):
        # self.plot_frame = QVBoxLayout()
        self.plot_frame = PlotFrame()
        self.central_layout.addWidget(self.plot_frame, 1, 2)
        # self.central_layout.addLayout(self.plot_frame, 1, 2)
        # self.plot_frame.addWidget(Color("blue", "plot"))

        self.ep_frame = EpisodeFrame(self)
        self.central_layout.addWidget(self.ep_frame, 1, 3)

    def open_file(self):
        filename = QFileDialog.getOpenFileName(self)[0]
        self.data = Recording.from_file(filename)
        self.ep_frame.populate(self.data)

    def save_to_file(self):
        pass

    def export_events(self):
        pass

    def export_idealization(self):
        pass

    def launch_idealization(self):
        self.tc_frame = IdealizationFrame()
        self.tc_frame.show()
        self.central_layout.addWidget(self.tc_frame, 1, 1)
    
    def launch_fa_analysis(self):
        pass

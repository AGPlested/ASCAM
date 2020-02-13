import logging

# pylint: disable=E0611
from PySide2.QtWidgets import QGridLayout, QWidget, QMainWindow, QFileDialog, QAction


from ascam.qtgui import ExportFADialog
from ascam.qtgui import ExportFileDialog
from ascam.qtgui import FilterFrame
from ascam.qtgui import BaselineFrame
from ascam.qtgui import PlotFrame
from ascam.qtgui import EpisodeFrame
from ascam.qtgui import IdealizationFrame
from ascam.qtgui import FirstActivationFrame

from ascam.core.recording import Recording


ana_logger = logging.getLogger("ascam.analysis")
debug_logger = logging.getLogger("ascam.debug")


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        debug_logger.debug("MainWindow initializing")

        self.setWindowTitle("cuteSCAM")

        self.central_layout = QGridLayout()
        self.central_widget = QWidget()
        self.central_widget.setLayout(self.central_layout)
        self.setCentralWidget(self.central_widget)

        self.data = Recording()

        self.create_widgets()

        self.create_menu()

    def create_menu(self):
        debug_logger.debug("MainWindow creating menus")
        self.file_menu = self.menuBar().addMenu("File")
        self.file_menu.addAction("Open File", self.open_file)
        self.file_menu.addAction("Save", self.save_to_file)
        self.file_menu.addAction("Export", lambda: ExportFileDialog())
        self.file_menu.addAction("Export Idealization", self.export_idealization)
        self.file_menu.addAction("Export Events", self.export_events)
        self.file_menu.addAction("Export First Activation", lambda: ExportFADialog())
        self.file_menu.addSeparator()
        self.file_menu.addAction("Quit", self.close)

        self.processing_menu = self.menuBar().addMenu("Processing")
        self.processing_menu.addAction(
            "Baseline Correction", lambda: BaselineFrame(self)
        )
        self.processing_menu.addAction("Filter", lambda: FilterFrame(self))

        self.analysis_menu = self.menuBar().addMenu("Analysis")
        self.analysis_menu.addAction("Idealize", self.launch_idealization)
        self.analysis_menu.addAction("First Activation", self.launch_fa_analysis)

        self.plot_menu = self.menuBar().addMenu("Plots")
        show_piezo = QAction('Show Piezo Voltage', self.plot_menu, checkable=True)
        show_piezo.triggered.connect(self.plot_frame.toggle_piezo)
        self.plot_menu.addAction(show_piezo)
        show_piezo.setChecked(True)
        show_command = QAction('Show Command Voltage', self.plot_menu, checkable=True)
        show_command.triggered.connect(self.plot_frame.toggle_command)
        self.plot_menu.addAction(show_command)

        # self.histogram_menu = self.menuBar().addMenu("Histogram")

    def create_widgets(self):
        self.plot_frame = PlotFrame(self)
        self.central_layout.addWidget(self.plot_frame, 1, 2)

        self.ep_frame = EpisodeFrame(self)
        self.central_layout.addWidget(self.ep_frame, 1, 3)

    def open_file(self):
        filename = QFileDialog.getOpenFileName(self)[0]
        self.data = Recording.from_file(filename)
        self.ep_frame.populate()
        self.ep_frame.setFocus()

    def save_to_file(self):
        pass

    def export_events(self):
        pass

    def export_idealization(self):
        pass

    def launch_idealization(self):
        self.tc_frame = IdealizationFrame(self)
        self.tc_frame.show()
        self.central_layout.addWidget(self.tc_frame, 1, 1)

    def launch_fa_analysis(self):
        self.fa_frame = FirstActivationFrame(self)
        self.fa_frame.show()
        self.central_layout.addWidget(self.fa_frame, 2, 2)

from PySide2 import QtGui, QtCore
from PySide2.QtWidgets import (
        QTextEdit, QDialog, QVBoxLayout, QHBoxLayout, QCheckBox,
        QLabel, QLineEdit, QPushButton, QComboBox)
import pyqtgraph as pg

from ascam.constants import TIME_UNIT_FACTORS

class TextEdit(QTextEdit):
    def __init__(self, *args, **kwargs):
        QTextEdit.__init__(self, *args, **kwargs)
        self.document().modificationChanged.connect(self.updateMaxHeight)

    def updateMaxHeight(self, *args):
        # the +2 is a bit hacky, but it's there to avoid the appearance of
        # scrollbars when then widget is initialized
        self.setMaximumHeight(self.document().size().height()+2)

    def resizeEvent(self, e):
        QTextEdit.resizeEvent(self, e)
        self.updateMaxHeight()


class CustomViewBox(pg.ViewBox):
    def __init__(self, parent=None, n_bins=None, amp=None, time_unit='ms'):
        # self.setRectMode() # Set mouse mode to rect for convenient zooming
        super().__init__()
        self.parent = parent
        self.amp = amp
        self.n_bins = n_bins
        self.time_unit = time_unit
        self.exportDialog = None
        self.menu = None # Override pyqtgraph ViewBoxMenu
        self.menu = self.get_menu() # Create the menu

    def raiseContextMenu(self, ev):
        if not self.menuEnabled():
            return
        menu = self.get_menu()
        menu = self.scene().addParentContextMenus(self, menu, ev)
        menu.removeAction(menu.actions()[-2])  # remove the "Plot Options" menu item
        
        pos  = ev.screenPos()
        menu.popup(QtCore.QPoint(pos.x(), pos.y()))

    def open_hist_config(self):
        self.hist_config = EventHistConfig(self)
        self.hist_config.show()

    def get_menu(self):
        if self.menu is None:
            self.menu = QtGui.QMenu()
            self.viewAll = QtGui.QAction("View All", self.menu)
            self.viewAll.triggered.connect(self.autoRange)
            self.menu.addAction(self.viewAll)

            self.hist_config_item = QtGui.QAction("Configure Histogram", self.menu)
            self.hist_config_item.triggered.connect(self.open_hist_config)
            self.menu.addAction(self.hist_config_item)
        return self.menu


class EventHistConfig(QDialog):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.create_widgets()

    def create_widgets(self):
        row = QHBoxLayout()
        label = QLabel("Number of bins:")
        row.addWidget(label)
        self.n_bins = QLineEdit(str(self.parent.n_bins))
        row.addWidget(self.n_bins)
        self.layout.addLayout(row)

        # row = QHBoxLayout()
        # label = QLabel('Binning Formula')
        # row.addWidget(label)
        # self.n_bins = QLineEdit()
        # row.addWidget(self.n_bins)
        # self.layout.addLayout(row)

        row = QHBoxLayout()
        label = QLabel('Time Unit')
        row.addWidget(label)
        self.time_unit = QComboBox()
        self.time_unit.addItems(TIME_UNIT_FACTORS.keys())
        self.time_unit.setCurrentText(self.parent.time_unit)
        row.addWidget(self.time_unit)
        self.layout.addLayout(row)

        row = QHBoxLayout()
        label = QLabel('Square Root Counts')
        row.addWidget(label)
        self.root_counts = QCheckBox()
        self.root_counts.setChecked(True)
        self.root_counts.stateChanged.connect(self.set_root_counts)
        row.addWidget(self.root_counts)
        self.layout.addLayout(row)

        row = QHBoxLayout()
        label = QLabel('Log10 Dwell Times')
        row.addWidget(label)
        self.log_times = QCheckBox()
        self.log_times.setChecked(True)
        self.log_times.stateChanged.connect(self.set_log_times)
        row.addWidget(self.log_times)
        self.layout.addLayout(row)

#         row = QHBoxLayout()
#         label = QLabel('Time Transform')
#         row.addWidget(label)
#         # self.time_unit = QComboBox()
#         # self.time_unit.addItems(TIME_UNIT_FACTORS.keys())
#         # row.addWidget(self.time_unit)
#         self.layout.addLayout(row)

#         row = QHBoxLayout()
#         label = QLabel('Count Transform')
#         row.addWidget(label)
#         # self.time_unit = QComboBox()
#         # self.time_unit.addItems(TIME_UNIT_FACTORS.keys())
#         # row.addWidget(self.time_unit)
#         self.layout.addLayout(row)

        row = QHBoxLayout()
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.ok_click)
        row.addWidget(ok_button)
        cancel_button = QPushButton("cancel")
        cancel_button.clicked.connect(self.close)
        row.addWidget(cancel_button)
        self.layout.addLayout(row)

    def set_root_counts(self, val):
        print(val)

    def set_log_times(self, val):
        pass

    def ok_click(self):
        self.parent.parent.update_hist(
                amp=self.parent.amp,
                n_bins = int(self.n_bins.text()),
                time_unit=self.time_unit.currentText()
                )
        self.close()


import logging

from PySide2 import QtGui, QtCore
from PySide2.QtWidgets import (
        QLayout,
    QWidget,
    QTextEdit,
    QTableView,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QCheckBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
)
import pyqtgraph as pg

from ..constants import TIME_UNIT_FACTORS
from ..utils import clear_qt_layout

debug_logger = logging.getLogger("ascam.debug")


class TextEdit(QTextEdit):
    def __init__(self, *args, **kwargs):
        QTextEdit.__init__(self, *args, **kwargs)
        self.document().modificationChanged.connect(self.updateMaxHeight)

    def updateMaxHeight(self, *args):
        # the +2 is a bit hacky, but it's there to avoid the appearance of
        # scrollbars when then widget is initialized
        self.setMaximumHeight(self.document().size().height() + 2)

    def resizeEvent(self, e):
        QTextEdit.resizeEvent(self, e)
        self.updateMaxHeight()


class HistogramViewBox(pg.ViewBox):
    def __init__(
        self,
        histogram=None,
        histogram_frame=None,
        n_bins=None,
        amp=None,
        time_unit="ms",
        log_times=True,
        root_counts=True,
    ):
        # self.setRectMode() # Set mouse mode to rect for convenient zooming
        super().__init__()
        self.histogram = histogram
        self.histogram_frame = histogram_frame
        self.menu = None  # Override pyqtgraph ViewBoxMenu
        self.menu = self.get_menu()  # Create the menu

    def raiseContextMenu(self, ev):
        if not self.menuEnabled():
            return
        menu = self.get_menu()
        menu = self.scene().addParentContextMenus(self, menu, ev)
        menu.removeAction(menu.actions()[-2])  # remove the "Plot Options" menu item

        pos = ev.screenPos()
        menu.popup(QtCore.QPoint(pos.x(), pos.y()))

    def open_hist_config(self):
        self.hist_config = EventHistConfig(self.histogram_frame, self.histogram)
        self.hist_config.show()

    def open_nbins_dialog(self):
        self.hist_config = NBinsDialog(self.histogram)
        self.hist_config.show()

    def get_menu(self):
        if self.menu is None:
            self.menu = QtGui.QMenu()

            self.viewAll = QtGui.QAction("View All", self.menu)
            self.viewAll.triggered.connect(self.autoRange)
            self.menu.addAction(self.viewAll)

            self.n_bins_dialog = QtGui.QAction("Number of Bins", self.menu)
            self.n_bins_dialog.triggered.connect(self.open_nbins_dialog)
            self.menu.addAction(self.n_bins_dialog)

            self.menu.addSeparator()
            self.hist_config_item = QtGui.QAction("Configure Histogram", self.menu)
            self.hist_config_item.triggered.connect(self.open_hist_config)
            self.menu.addAction(self.hist_config_item)
        return self.menu


class NBinsDialog(QDialog):
    """Configuration dialog for the number of bins used in a histogram, this config is particular to
    the histogram that the right click event belongs to."""

    def __init__(self, histogram):
        super().__init__()
        self.histogram = histogram
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.create_widgets()
        self.show()

    def create_widgets(self):
        row = QHBoxLayout()
        label = QLabel("Number of bins:")
        row.addWidget(label)
        self.n_bins_entry = QLineEdit(str(self.histogram.n_bins))
        row.addWidget(self.n_bins_entry)
        self.layout.addLayout(row)

        row = QHBoxLayout()
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.ok_click)
        row.addWidget(ok_button)

        cancel_button = QPushButton("cancel")
        cancel_button.clicked.connect(self.close)
        row.addWidget(cancel_button)
        self.layout.addLayout(row)

    def ok_click(self):
        self.histogram.n_bins = int(self.n_bins_entry.text())
        self.histogram.update_hist()
        self.close()


class EventHistConfig(QDialog):
    """Configuration Dialog for the event histograms. The options in this dialog apply to all histogram.
    """

    def __init__(self, histogram_frame=None, histogram=None):
        super().__init__()
        self.histogram = histogram
        self.histogram_frame = histogram_frame
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.create_widgets()

    def create_widgets(self):
        row = QHBoxLayout()
        label = QLabel("Time Unit")
        row.addWidget(label)
        self.time_unit = QComboBox()
        self.time_unit.addItems(TIME_UNIT_FACTORS.keys())
        self.time_unit.setCurrentText(self.histogram.time_unit)
        row.addWidget(self.time_unit)
        self.layout.addLayout(row)

        row = QHBoxLayout()
        label = QLabel("Square Root Counts")
        row.addWidget(label)
        self.root_counts = QCheckBox()
        self.root_counts.setChecked(self.histogram.root_counts)
        row.addWidget(self.root_counts)
        self.layout.addLayout(row)

        row = QHBoxLayout()
        label = QLabel("Log10 Dwell Times")
        row.addWidget(label)
        self.log_times = QCheckBox()
        self.log_times.setChecked(self.histogram.log_times)
        row.addWidget(self.log_times)
        self.layout.addLayout(row)
        row = QHBoxLayout()
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.ok_click)
        row.addWidget(ok_button)

        cancel_button = QPushButton("cancel")
        cancel_button.clicked.connect(self.close)
        row.addWidget(cancel_button)
        self.layout.addLayout(row)

    def ok_click(self):
        clear_qt_layout(self.histogram_frame.layout)

        n_bins = {h.amp: h.n_bins for h in self.histogram_frame.histograms}
        self.histogram_frame.create_histograms(
            log_times=self.log_times.isChecked(),
            root_counts=self.root_counts.isChecked(),
            time_unit=self.time_unit.currentText(),
            n_bins=n_bins,
        )
        self.close()


class TableFrame(QDialog):
    def __init__(self, parent, data, header, trace_unit=None, 
                 time_unit=None, title=None, height=800, width=500):
        super().__init__()
        self.parent = parent
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.setGeometry(parent.x() + width / 4, parent.y() + height / 3, width, height)

        
        table = TableModel(data, header, trace_unit, time_unit)
        table_view = QTableView()
        table_view.setModel(table)

        self.layout.addWidget(table_view)
        self.setModal(False)
        if title is None:
            title = header
        self.setWindowTitle(title)
        self.show()


class TableModel(QtCore.QAbstractTableModel):
    def __init__(self, data, header, trace_unit=None, time_unit=None):
        super().__init__()
        self._data = data
        self._header = header

    def data(self, index, role):
        if role == QtCore.Qt.DisplayRole:
            # See below for the nested-list data structure.
            # .row() indexes into the outer list,
            # .column() indexes into the sub-list
            if index.row() == 0:
                return self._header[index.column()]
            return self._data[index.row() - 1][index.column()]

    def rowCount(self, index):
        return len(self._data)

    def columnCount(self, index):
        return len(self._data[0])


class VerticalContainerWidget(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.create_widgets()

    def create_widets(self):
        raise NotImplementedError

    def add_row(self, *items):
        row = QHBoxLayout()
        for item in items:
            if isinstance(item, QWidget):
                row.addWidget(item)
            elif isinstance(item, QLayout):
                row.addLayout(item)
            else:
                raise TypeError(f"Cannot add {item} to a row layout.")
        self.layout.addLayout(row)

        

class EntryWidget(VerticalContainerWidget):
    def __init__(self, parent):

        super().__init__(parent)

    @property
    def trace_unit(self):
        if hasattr(self, 'trace_unit_entry'):
            return self.trace_unit_entry.currentText()
        return None

    @trace_unit.setter
    def trace_unit(self, val):
        if hasattr(self, 'trace_unit_entry'):
            self.trace_unit_entry.setCurrentText(val)

    @property
    def time_unit(self):
        if hasattr(self, 'time_unit_entry'):
            return self.time_unit_entry.currentText()
        return None

    @time_unit.setter
    def time_unit(self, val):
        if hasattr(self, 'time_unit_entry'):
            self.time_unit_entry.setCurrentText(val)


import logging

# pylint: disable=no-name-in-module
from PySide2.QtCore import QAbstractTableModel, Qt
from PySide2 import QtWidgets
from PySide2.QtWidgets import (
        QDialog,
    QTableView,
    QSpacerItem,
    QGridLayout,
    QTabWidget,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QCheckBox,
    QLineEdit,
    QToolButton,
    QTabBar,
    QPushButton,
    QLabel,
)

from ascam.utils import string_to_array #, array_to_string


debug_logger = logging.getLogger("ascam.debug")


class IdealizationFrame(QWidget):
    def __init__(self, main):
        super().__init__()

        self.main = main
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.create_widgets()

    def create_widgets(self):
        self.tab_frame = IdealizationTabFrame(self.main)
        self.layout.addWidget(self.tab_frame)

        self.calc_button = QPushButton("Calculate idealization")
        self.calc_button.clicked.connect(self.calculate)
        self.layout.addWidget(self.calc_button)
        self.events_button = QPushButton("Create Table of Events")
        self.events_button.clicked.connect(self.get_events)
        self.layout.addWidget(self.events_button)

        # self.apply_button = QPushButton("Apply")
        # self.apply_button.clicked.connect(self.apply)
        # self.layout.addWidget(self.apply_button)

        self.close_button = QPushButton("Close Tab")
        self.close_button.clicked.connect(self.close_tab)
        self.layout.addWidget(self.close_button)

        self.layout.addItem(
            QSpacerItem(
                20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding
            )
        )

    def close_tab(self):
        if self.tab_frame.count() > 1:
            self.tab_frame.removeTab(self.tab_frame.currentIndex())

    def get_events(self):
        EventTableFrame(self)

    def calculate(self):
        amps = string_to_array(self.tab_frame.currentWidget().amp_entry.text())
        thresh = string_to_array(self.tab_frame.currentWidget().threshold_entry.text())
        res_string = self.tab_frame.currentWidget().res_entry.text()

        if res_string.strip():
            resolution = int(res_string)
        else:
            resolution = None
        intrp_string = self.tab_frame.currentWidget().intrp_entry.text()

        if intrp_string.strip():
            intrp_factor = int(intrp_string)
        else:
            intrp_factor = 1

        self.main.data.idealize_episode(amps, thresh, resolution, intrp_factor)
        self.main.plot_frame.plot_episode()

    def apply(self):
        pass


class IdealizationTabFrame(QTabWidget):
    def __init__(self, main):
        super().__init__()
        self.main = main

        self.tabs = [IdealizationTab(self)]
        self.addTab(self.tabs[0], "1")

        self.insertTab(1, QWidget(), "")
        self.new_button = QToolButton()
        self.new_button.setText("+")
        self.new_button.clicked.connect(self.add_tab)
        self.tabBar().setTabButton(1, QTabBar.RightSide, self.new_button)

        self.setTabsClosable(True)
        self.tabBar().tabCloseRequested.connect(self.removeTab)

    def add_tab(self):
        title = str(self.count())
        debug_logger.debug(f"adding new tab with number {title}")
        tab = IdealizationTab(self)
        self.tabs.append(tab)
        self.insertTab(self.count() - 1, tab, title)


class IdealizationTab(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        # layout.addWidget(QLabel("Idealize me baby"))
        # button = QPushButton("bye")
        # button.clicked.connect(lambda *args: self.close())
        # layout.addWidget(button)
        self.create_widgets()

    def create_widgets(self):
        row_one = QHBoxLayout()
        amp_label = QLabel("Amplitudes")
        row_one.addWidget(amp_label)
        show_amp_check = QCheckBox("Show")
        row_one.addWidget(show_amp_check)
        neg_check = QCheckBox("Negative Values")
        row_one.addWidget(neg_check)
        self.layout.addLayout(row_one)

        self.amp_entry = QLineEdit()
        self.layout.addWidget(self.amp_entry)

        row_three = QHBoxLayout()
        threshold_label = QLabel("Amplitudes")
        row_three.addWidget(threshold_label)
        show_threshold_check = QCheckBox("Show")
        row_three.addWidget(show_threshold_check)
        auto_thresholds = QCheckBox("Automatic")
        row_three.addWidget(auto_thresholds)
        self.layout.addLayout(row_three)

        self.threshold_entry = QLineEdit()
        self.layout.addWidget(self.threshold_entry)

        row_four = QHBoxLayout()
        res_label = QLabel("Resolution")
        row_four.addWidget(res_label)
        use_res = QCheckBox("Apply")
        row_four.addWidget(use_res)
        self.layout.addLayout(row_four)

        self.res_entry = QLineEdit()
        self.layout.addWidget(self.res_entry)

        row_six = QHBoxLayout()
        intrp_label = QLabel("Interpolation")
        row_six.addWidget(intrp_label)
        interpolate = QCheckBox("Apply")
        row_six.addWidget(interpolate)
        self.layout.addLayout(row_six)

        self.intrp_entry = QLineEdit()
        self.layout.addWidget(self.intrp_entry)


class EventTableFrame(QDialog):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.setWindowTitle("Events")
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.create_table()

        self.layout.addWidget(self.event_table)
        self.exec_()

    def create_table(self):
        events = self.parent.main.data.get_events()
        self.q_event_table = EventTableModel(events)
        self.event_table = QTableView()
        self.event_table.setModel(self.q_event_table)


class EventTableModel(QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        # super(TableModel, self).__init__()
        self._data = data

        self._header = [
            f"Amplitude [{self.main.data.trace_unit}]",
            f"Duration [{self.main.data.time_unit}]",
            f"t_start",
            "t_stop",
            "Episode #",
        ]
    def data(self, index, role):
        if role == Qt.DisplayRole:
            # See below for the nested-list data structure.
            # .row() indexes into the outer list,
            # .column() indexes into the sub-list
            if index.row() == 0:
                return self._header[index.column()]
            return self._data[index.row()-1][index.column()]

    def rowCount(self, index):
        return len(self._data)

    def columnCount(self, index):
        return len(self._data[0])


class FirstActivationFrame(QWidget):
    def __init__(self, main):
        super().__init__()
        self.main = main

        self.layout = QGridLayout()
        self.setLayout(self.layout)

        self.create_widgets()

    def create_widgets(self):
        threshold_button = QPushButton("Set threshold")
        threshold_entry = QLineEdit()
        self.layout.addWidget(threshold_button, 1, 1)
        self.layout.addWidget(threshold_entry, 1, 2)

        mark_button = QPushButton("Mark events manually")
        jump_checkbox = QCheckBox("Click jumps to next episode:")
        self.layout.addWidget(mark_button, 2, 1)
        self.layout.addWidget(jump_checkbox, 2, 2)

        finish_button = QPushButton("Finish")
        cancel_button = QPushButton("Cancel")
        self.layout.addWidget(finish_button, 3, 1)
        self.layout.addWidget(cancel_button, 3, 2)

import logging

import numpy as np
import pyqtgraph as pg
from PySide2.QtCore import QAbstractTableModel, Qt
from PySide2.QtWidgets import (
        QSizePolicy,
        QSpacerItem,
    QComboBox,
    QFileDialog,
    QDialog,
    QTableView,
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

from ascam.utils import string_to_array, array_to_string, update_number_in_string
from ascam.constants import TIME_UNIT_FACTORS, CURRENT_UNIT_FACTORS
from ascam.core import IdealizationCache
from ascam.utils.widgets import TextEdit, HistogramViewBox

debug_logger = logging.getLogger("ascam.debug")


class FirstActivationFrame(QWidget):
    def __init__(self, main):
        super().__init__()
        self.main = main

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.main.plot_frame.plot_fa_threshold(0)

        self.create_widgets()
        self.main.ep_frame.ep_list.currentItemChanged.connect(self.on_episode_click, type=Qt.QueuedConnection)

    def on_episode_click(self, item, *args):
        thresh = float(self.threshold_entry.text()) 
        thresh /= CURRENT_UNIT_FACTORS[self.trace_unit.currentText()]
        self.main.plot_frame.plot_fa_threshold(thresh)
        if self.drag_threshold_button.isChecked():
            self.main.plot_frame.fa_thresh_line.sigDragged.connect(self.drag_fa_threshold)
        self.set_threshold()

    def create_widgets(self):
        row = QHBoxLayout()
        self.threshold_button = QPushButton("Set threshold")
        self.threshold_button.clicked.connect(self.set_threshold)
        row.addWidget(self.threshold_button)
        self.drag_threshold_button = QToolButton()
        self.drag_threshold_button.setText("Draggable")
        self.drag_threshold_button.setCheckable(True)
        self.drag_threshold_button.clicked.connect(self.toggle_dragging_threshold)
        row.addWidget(self.drag_threshold_button)
        self.trace_unit = QComboBox()
        self.trace_unit.addItems(list(CURRENT_UNIT_FACTORS.keys()))
        self.trace_unit.setCurrentIndex(1)
        row.addWidget(self.trace_unit)
        self.threshold_entry = QLineEdit()
        row.addWidget(self.threshold_entry)
        self.layout.addLayout(row)

        row = QHBoxLayout()
        self.manual_marking_toggle = QToolButton()
        self.manual_marking_toggle.setCheckable(True)
        self.manual_marking_toggle.setText("Mark events manually")
        self.manual_marking_toggle.clicked.connect(self.toggle_manual_marking)
        row.addWidget(self.manual_marking_toggle)
        self.jump_checkbox = QCheckBox("Click jumps to next episode")
        self.jump_checkbox.stateChanged.connect(self.toggle_click_auto_jump)
        row.addWidget(self.jump_checkbox)
        self.layout.addLayout(row)

        row = QHBoxLayout()
        finish_button = QPushButton("Finish")
        finish_button.clicked.connect(self.click_finish)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.click_cancel)
        row.addWidget(finish_button)
        row.addWidget(cancel_button)
        self.layout.addLayout(row)

    def toggle_dragging_threshold(self, *args):
        if self.drag_threshold_button.isChecked():
            self.main.plot_frame.fa_thresh_line.sigDragged.connect(self.drag_fa_threshold)
            self.main.plot_frame.fa_thresh_line.setMovable(True)
            self.main.plot_frame.plots_are_draggable = False
        else:
            self.main.ep_frame.ep_list.currentItemChanged.disconnect(self.change_episode)
            self.main.plot_frame.plots_are_draggable = True
            self.main.plot_frame.fa_thresh_line.setMovable(False)

    def toggle_manual_marking(self):
        raise NotImplementedError

    def drag_fa_threshold(self):
        self.threshold_entry.setText(str(self.main.plot_frame.fa_thresh_line.value()*CURRENT_UNIT_FACTORS[self.trace_unit.currentText()]))
        self.click_set_threshold()

    def toggle_click_auto_jump(self):
        raise NotImplementedError

    def click_set_threshold(self):
        thresh = float(self.threshold_entry.text()) 
        thresh /= CURRENT_UNIT_FACTORS[self.trace_unit.currentText()]
        debug_logger.debug(f"setting first activation threshold at {thresh}")
        self.main.data.detect_fa(thresh)
        self.main.plot_frame.fa_thresh_line.setValue(thresh)
        self.main.plot_frame.plot_fa_line(self.main.data.episode.first_activation)

    def click_cancel(self):
        for e in self.main.data.series:
            e.first_activation = None
        self.main.plot_frame.clear_fa()
        self.main.plot_frame.clear_fa_threshold()
        self.main.ep_frame.ep_list.currentItemChanged.disconnect(self.change_episode)
        self.close()

    def click_finish(self):
        self.main.plot_frame.clear_fa()
        self.main.plot_frame.clear_fa_threshold()
        self.main.ep_frame.ep_list.currentItemChanged.disconnect(self.change_episode)
        self.close()

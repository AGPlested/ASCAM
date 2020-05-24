import logging

import pyqtgraph as pg
from PySide2 import QtCore
from PySide2.QtWidgets import (
    QComboBox,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QCheckBox,
    QLineEdit,
    QToolButton,
    QPushButton,
)

from ascam.constants import CURRENT_UNIT_FACTORS, GREEN

debug_logger = logging.getLogger("ascam.debug")


class FirstActivationFrame(QWidget):
    def __init__(self, main):
        super().__init__()
        self.main = main

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.main.plot_frame.plot_fa_threshold(0)

        self.marking_indicator = None

        self.create_widgets()
        self.main.ep_frame.ep_list.currentItemChanged.connect(
            self.on_episode_click, type=QtCore.Qt.QueuedConnection
        )

        self.threshold = 0
        self.set_threshold()

    @property
    def marking_indicator(self):
        return self.main.plot_frame.marking_indicator

    @marking_indicator.setter
    def marking_indicator(self, val):
        self.main.plot_frame.marking_indicator = val

    @property
    def threshold(self):
        thresh = float(self.threshold_entry.text())
        return thresh / CURRENT_UNIT_FACTORS[self.trace_unit.currentText()]

    @threshold.setter
    def threshold(self, val):
        self.threshold_entry.setText(
            str(val * CURRENT_UNIT_FACTORS[self.trace_unit.currentText()])
        )

    def create_widgets(self):
        row = QHBoxLayout()
        self.threshold_button = QPushButton("Set threshold")
        self.threshold_button.clicked.connect(self.click_set_threshold)
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
        self.threshold_entry.setText("0")
        self.threshold_entry.returnPressed.connect(self.click_set_threshold)
        row.addWidget(self.threshold_entry)
        self.layout.addLayout(row)

        row = QHBoxLayout()
        self.manual_marking_toggle = QToolButton()
        self.manual_marking_toggle.setCheckable(True)
        self.manual_marking_toggle.setText("Mark events manually")
        self.manual_marking_toggle.clicked.connect(self.toggle_manual_marking)
        self.manual_marking_toggle.clicked.connect(self.toggle_jump_checkbox)
        row.addWidget(self.manual_marking_toggle)
        self.jump_checkbox = QCheckBox("Click jumps to next episode")
        self.jump_checkbox.setEnabled(False)
        self.jump_checkbox.stateChanged.connect(self.toggle_click_auto_jump)
        row.addWidget(self.jump_checkbox)
        self.layout.addLayout(row)

        row = QHBoxLayout()
        finish_button = QPushButton("Finish")
        finish_button.clicked.connect(self.clean_up_and_close)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.click_cancel)
        row.addWidget(finish_button)
        row.addWidget(cancel_button)
        self.layout.addLayout(row)

    def on_episode_click(self, item, *args):
        self.main.plot_frame.plot_fa_threshold(self.threshold)
        if self.drag_threshold_button.isChecked():
            self.main.plot_frame.fa_thresh_hist_line.sigDragged.connect(
                self.drag_fa_threshold_hist
            )
            self.main.plot_frame.fa_thresh_hist_line.setMovable(True)

            self.main.plot_frame.fa_thresh_line.sigDragged.connect(
                self.drag_fa_threshold
            )
            self.main.plot_frame.fa_thresh_line.setMovable(True)
        if self.manual_marking_toggle.isChecked():
            self.main.plot_frame.draw_fa_marking_indicator()
            self.main.plot_frame.trace_plot.scene().sigMouseMoved.connect(
                self.drag_manual_indicator
            )
            self.main.plot_frame.trace_plot.scene().sigMouseClicked.connect(
                self.mark_fa_manually
            )
        self.set_threshold()

    def drag_manual_indicator(self, pos):
        mousePoint = self.main.plot_frame.trace_viewbox.mapSceneToView(pos)
        # self.marking_label.setText(f"({mousePoint.x():.5g}, {mousePoint.y():.5g})")
        # time = self.main.data.episode.time
        # pos_percentage = mousePoint.x() / (time[-1] - time[0])
        # self.curve_point.setPos(pos_percentage)
        self.marking_indicator.setPos(mousePoint.x())

    def toggle_dragging_threshold(self, *args):
        if self.drag_threshold_button.isChecked():
            self.clean_up_marking()
            self.manual_marking_toggle.setChecked(False)
            self.main.plot_frame.fa_thresh_hist_line.sigDragged.connect(
                self.drag_fa_threshold_hist
            )
            self.main.plot_frame.fa_thresh_hist_line.setMovable(True)
            self.main.plot_frame.fa_thresh_line.sigDragged.connect(
                self.drag_fa_threshold
            )
            self.main.plot_frame.fa_thresh_line.setMovable(True)
            self.main.plot_frame.plots_are_draggable = False
        else:
            self.clean_up_thresh_dragging()
            self.main.plot_frame.plots_are_draggable = True

    def toggle_manual_marking(self):
        if self.manual_marking_toggle.isChecked():
            self.drag_threshold_button.setChecked(False)
            self.clean_up_thresh_dragging()

            self.main.plot_frame.draw_fa_marking_indicator()
            self.main.plot_frame.trace_plot.scene().sigMouseMoved.connect(
                self.drag_manual_indicator
            )
            self.main.plot_frame.trace_plot.scene().sigMouseClicked.connect(
                self.mark_fa_manually
            )
            self.main.plot_frame.plots_are_draggable = False

        else:
            self.clean_up_marking()
            self.main.plot_frame.plots_are_draggable = True

    def clean_up_marking(self):
        if self.marking_indicator is not None:
            self.main.plot_frame.trace_plot.removeItem(self.marking_indicator)
        try:
            self.main.plot_frame.trace_plot.scene().sigMouseMoved.disconnect(
                self.drag_manual_indicator
            )
            self.main.plot_frame.trace_plot.scene().sigMouseClicked.disconnect(
                self.mark_fa_manually
            )
        except RuntimeError as error:
            if "Failed to disconnect signal" in str(error):
                pass
            else:
                raise RuntimeError(error)

    def clean_up_thresh_dragging(self):
        self.main.plot_frame.fa_thresh_hist_line.setMovable(False)
        self.main.plot_frame.fa_thresh_line.setMovable(False)
        try:
            self.main.plot_frame.fa_thresh_hist_line.sigDragged.disconnect(
                self.drag_fa_threshold
            )
            self.main.ep_frame.ep_list.currentItemChanged.disconnect(
                self.on_episode_click
            )
        except RuntimeError as error:
            if "Failed to disconnect signal" in str(error):
                pass
            else:
                raise RuntimeError(error)

    def mark_fa_manually(self, evt):
        if evt.button() == QtCore.Qt.MouseButton.LeftButton:
            self.main.data.episode.first_activation = self.marking_indicator.value()
            self.main.plot_frame.plot_fa_line()
            self.main.data.episode.manual_first_activation = True

    def drag_fa_threshold_hist(self):
        self.main.plot_frame.fa_thresh_line.setValue(
            self.main.plot_frame.fa_thresh_hist_line.value()
        )
        self.threshold_entry.setText(
            str(
                self.main.plot_frame.fa_thresh_hist_line.value()
                * CURRENT_UNIT_FACTORS[self.trace_unit.currentText()]
            )
        )
        self.set_threshold()

    def drag_fa_threshold(self):
        self.main.plot_frame.fa_thresh_hist_line.setValue(
            self.main.plot_frame.fa_thresh_line.value()
        )
        self.threshold_entry.setText(
            str(
                self.main.plot_frame.fa_thresh_line.value()
                * CURRENT_UNIT_FACTORS[self.trace_unit.currentText()]
            )
        )
        self.set_threshold()

    def toggle_jump_checkbox(self):
        if self.manual_marking_toggle.isChecked():
            self.jump_checkbox.setEnabled(True)
        else:
            self.jump_checkbox.setEnabled(False)

    def toggle_click_auto_jump(self, state):
        if state:
            self.main.plot_frame.trace_plot.scene().sigMouseClicked.connect(
                self.click_auto_jump
            )
        else:
            self.main.plot_frame.trace_plot.scene().sigMouseClicked.disconnect(
                self.click_auto_jump
            )

    def click_auto_jump(self):
        self.main.ep_frame.ep_list.setCurrentRow(self.main.data.current_ep_ind + 1)
        self.main.plot_frame.draw_fa_marking_indicator()
        self.main.plot_frame.trace_plot.scene().sigMouseMoved.connect(
            self.drag_manual_indicator
        )
        self.main.plot_frame.trace_plot.scene().sigMouseClicked.connect(
            self.mark_fa_manually
        )

    def set_threshold(self):
        self.main.data.detect_fa(self.threshold)
        self.main.plot_frame.plot_fa_line()

    def click_set_threshold(self):
        debug_logger.debug(f"setting first activation threshold at {self.threshold}")
        self.set_threshold()
        self.main.plot_frame.fa_thresh_line.setValue(self.threshold)
        self.main.plot_frame.fa_thresh_hist_line.setValue(self.threshold)

    def click_cancel(self):
        for episode in self.main.data.series:
            episode.first_activation = None
            episode.manual_first_activation = False
        self.clean_up_and_close()

    def clean_up_and_close(self):
        self.main.plot_frame.clear_fa()
        self.main.plot_frame.clear_fa_threshold()
        self.main.plot_frame.plots_are_draggable = True
        self.main.ep_frame.ep_list.currentItemChanged.disconnect(self.on_episode_click)
        self.close()

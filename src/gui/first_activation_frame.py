import logging

import pyqtgraph as pg

from PySide2 import QtCore
from PySide2.QtWidgets import (
    QLabel,
    QComboBox
    QWidget,      #added by subsets revision
    QVBoxLayout,  #added by subsets revision
    QHBoxLayout,  #added by subsets revision
    QCheckBox,
    QLineEdit,
    QToolButton,
    QPushButton,
)


#from ..gui import ExportFADialog            #vague?
from ..utils import round_off_tables
from ..gui.io_widgets import ExportFADialog, ExportFEDialog

from ..utils.widgets import EntryWidget, TableFrame
from ..constants import CURRENT_UNIT_FACTORS

debug_logger = logging.getLogger("ascam.debug")


class FirstActivationFrame(EntryWidget):
    def __init__(self, main):
        super().__init__(main)
        self.main = main
        self.setFixedWidth(250)

        self.main.plot_frame.plot_fa_threshold(0)

        self.marking_indicator = None

        self.main.ep_frame.ep_list.currentItemChanged.connect(
            self.on_episode_click, type=QtCore.Qt.QueuedConnection
        )

        self.threshold = 0
        self.find_first_events = False
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
        return thresh / CURRENT_UNIT_FACTORS[self.trace_unit]

    @threshold.setter
    def threshold(self, val):
        self.threshold_entry.setText(
            f"{val * CURRENT_UNIT_FACTORS[self.trace_unit]:.3f}"
        )

    def create_widgets(self):
        self.drag_threshold_button = QLabel("First Activation Threshold:")
        self.add_row(self.drag_threshold_button)

        self.trace_unit_entry = QComboBox()
        self.trace_unit_entry.addItems(list(CURRENT_UNIT_FACTORS.keys()))
        self.trace_unit_entry.setCurrentIndex(1)
        self.threshold_entry = QLineEdit()
        self.threshold_entry.setText("0")
        self.threshold_entry.returnPressed.connect(self.set_threshold)
        self.drag_threshold_button = QToolButton()
        self.drag_threshold_button.setText("Draggable")
        self.drag_threshold_button.setCheckable(True)
        self.drag_threshold_button.toggled.connect(self.toggle_dragging_threshold)
        self.add_row(
            self.trace_unit_entry, self.threshold_entry, self.drag_threshold_button
        )

        self.first_events_toggle = QToolButton()
        self.first_events_toggle.setCheckable(True)
        self.first_events_toggle.setText("Find first events")
        self.first_events_toggle.toggled.connect(self.toggle_first_events)
        self.add_row(self.first_events_toggle)

        self.threshold_button = QPushButton("Set threshold")
        self.threshold_button.clicked.connect(self.set_threshold)
        self.add_row(self.threshold_button)

        self.manual_marking_toggle = QToolButton()
        self.manual_marking_toggle.setCheckable(True)
        self.manual_marking_toggle.setText("Mark events manually")
        self.manual_marking_toggle.toggled.connect(self.toggle_manual_marking)
        self.manual_marking_toggle.toggled.connect(self.toggle_jump_checkbox)
        self.add_row(self.manual_marking_toggle)

        self.jump_checkbox = QCheckBox("Click jumps to next episode")
        self.jump_checkbox.setEnabled(False)
        self.jump_checkbox.stateChanged.connect(self.toggle_click_auto_jump)
        self.add_row(self.jump_checkbox)

        show_table_button = QPushButton("Show First Activation Table")
        show_table_button.clicked.connect(self.show_first_activation_table)
        self.add_row(show_table_button)

        show_event_table_button = QPushButton("Show First Event Table")
        show_event_table_button.clicked.connect(self.show_first_event_table)
        self.add_row(show_event_table_button)

        export_button = QPushButton("Export First Activation Table")
        export_button.clicked.connect(self.export_first_activation)
        self.add_row(export_button)

        export_first_events_button = QPushButton("Export First Events Table")
        export_first_events_button.clicked.connect(self.export_first_events)
        self.add_row(export_first_events_button)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.click_cancel)
        self.add_row(cancel_button)

        self.layout.addSpacing(400)

    def export_first_activation(self):
        self.main.data.detect_fa(self.threshold)
        ExportFADialog(self.main)

    def export_first_events(self):
        self.main.data.get_first_events(self.threshold)
        ExportFEDialog(self.main)

    def show_first_activation_table(self):
        debug_logger.debug("creating first activation table")
        self.main.data.detect_fa(self.threshold)

        self.table_frame = TableFrame(
            self,
            data=self.main.data.create_first_activation_table(
                trace_unit=self.trace_unit
            ),
            header=[
                "Episode Number",
                f"First Activation Time [{self.time_unit}]",
                f"Current [{self.trace_unit}]",
            ],
            trace_unit=self.trace_unit,
            time_unit=self.time_unit,
            title=f"First activations in {self.main.data.current_datakey}",
            width=400,
        )

    def show_first_event_table(self):
        debug_logger.debug("Creating first event table")
        self.main.data.get_first_events(self.threshold)
        table_data = self.main.data.create_first_event_table(
                time_unit=self.time_unit,
            )
        header = ["Episode Number", "First state"]
        for i in range(int(len(table_data)/2)):
            header.append(f"S{i}-start [{self.time_unit}]")
            header.append(f"S{i}-duration [{self.time_unit}]")
        self.fe_table_frame = TableFrame(
            self,
            data=table_data,
            header=header,
            time_unit=self.time_unit,
            title=f"First events of each state",
            width=1000,
        )

    def on_episode_click(self, item, *args):
        self.main.plot_frame.plot_fa_threshold(self.threshold)
        if self.manual_marking_toggle.isChecked():
            self.main.plot_frame.draw_fa_marking_indicator()
        self.set_threshold()

    def drag_manual_indicator(self, pos):
        mousePoint = self.main.plot_frame.trace_viewbox.mapSceneToView(pos)
        self.marking_indicator.setPos(mousePoint.x())

    def toggle_dragging_threshold(self, *args):
        debug_logger.debug(
            f"toggling dragging treshold to {self.drag_threshold_button.isChecked()}"
        )
        if self.drag_threshold_button.isChecked():
            self.main.plot_frame.fa_tracking = True
            self.manual_marking_toggle.setChecked(False)
        else:
            self.main.plot_frame.fa_tracking = False

    def toggle_manual_marking(self):
        if self.manual_marking_toggle.isChecked():
            self.drag_threshold_button.setChecked(False)

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
        debug_logger.debug("cleaning up FA marking")
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

    def mark_fa_manually(self, evt):
        debug_logger.debug(
            f"manually marked episode {self.main.data.episode().n_episode}"
            f"at t={self.marking_indicator.value()}"
        )
        if evt.button() == QtCore.Qt.MouseButton.LeftButton:
            self.main.data.episode().first_activation = self.marking_indicator.value()
            self.main.plot_frame.plot_fa_line()
            self.main.data.episode().manual_first_activation = True

    def drag_fa_threshold_hist(self, pos):
        self.threshold = pos
        self.set_threshold()

    def drag_fa_threshold(self, pos):
        self.threshold = pos
        self.set_threshold()

    def toggle_jump_checkbox(self):
        if self.manual_marking_toggle.isChecked():
            self.jump_checkbox.setEnabled(True)
        else:
            self.jump_checkbox.setChecked(False)
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

    def toggle_first_events(self):
        self.find_first_events = not self.find_first_events

    def click_auto_jump(self):
        debug_logger.debug("auto jumping to next episode")
        self.main.ep_frame.ep_list.setCurrentRow(self.main.data.next_episode_ind())
        self.main.plot_frame.draw_fa_marking_indicator()

    def set_threshold(self):
        if self.find_first_events:
            self.main.data.get_first_events(self.threshold)
        else:
            self.main.data.detect_fa(self.threshold)
        self.main.plot_frame.plot_fa_line()
        self.main.plot_frame.plot_fa_threshold(self.threshold)

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
        self.main.fa_frame = None
        self.close()

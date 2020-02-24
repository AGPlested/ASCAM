import logging

# pylint: disable=E0611
from PySide2.QtWidgets import (QWidget, QListWidget, QVBoxLayout, QSizePolicy, 
                               QComboBox)


debug_logger = logging.getLogger("ascam.debug")


class EpisodeFrame(QWidget):
    def __init__(self, main, *args, **kwargs):
        super(EpisodeFrame, self).__init__(*args, **kwargs)
        self.main = main
        # self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.create_widgets()
        
    def create_widgets(self):
        self.series_selection = QComboBox()
        self.series_selection.setDuplicatesEnabled(False)
        self.series_selection.addItems(self.main.data.keys())
        self.series_selection.currentTextChanged.connect(self.switch_series)
        self.layout.addWidget(self.series_selection)

        self.ep_list = EpisodeList(self)
        self.layout.addWidget(self.ep_list)

    def switch_series(self, datakey):
        self.main.data.current_datakey = datakey
        self.main.plot_frame.plot_all()

    def update_combo_box(self):
        self.series_selection.clear()
        self.series_selection.addItems(self.main.data.keys())


class EpisodeList(QListWidget):
    """Widget holding the scrollable list of episodes and the episode list
    selection"""

    def __init__(self, parent, *args, **kwargs):
        super(EpisodeList, self).__init__(*args, **kwargs)
        self.parent = parent
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.populate()

        self.currentItemChanged.connect(self.on_item_click)

    def on_item_click(self, item, previous):  # pylint: disable=unused-argument
        self.parent.main.data.current_ep_ind = self.row(item)
        try:
            self.parent.main.tc_frame.idealize_episode()
        except AttributeError:
            pass
        self.parent.main.plot_frame.update_plots()

    def populate(self):
        self.clear()
        if self.parent.main.data is not None:
            n_eps = len(self.parent.main.data.series)
            debug_logger.debug("inserting data")
            self.addItems([f"Episode {i+1}" for i in range(n_eps)])
        self.setCurrentRow(0)

import logging

# pylint: disable=E0611
from PySide2.QtWidgets import QListWidget, QVBoxLayout, QSizePolicy


debug_logger = logging.getLogger("ascam.debug")


class EpisodeFrame(QListWidget):
    """Widget holding the scrollable list of episodes and the episode list
    selection"""

    def __init__(self, main, *args, **kwargs):
        super(EpisodeFrame, self).__init__(*args, **kwargs)
        self.main = main
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.populate()

        self.currentItemChanged.connect(self.on_item_click)

    def on_item_click(self, item, previous):  # pylint: disable=unused-argument
        self.main.data.current_ep_ind = self.row(item)
        self.main.tc_frame.idealize_episode()
        self.main.plot_frame.update_plots()

    def populate(self):
        self.clear()
        if self.main.data is not None:
            n_eps = len(self.main.data.series)
            debug_logger.debug("inserting data")
            self.addItems([f"Episode {i+1}" for i in range(n_eps)])
        self.setCurrentRow(0)

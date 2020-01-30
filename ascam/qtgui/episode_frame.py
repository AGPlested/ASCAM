import logging

from PySide2.QtWidgets import (
    QListWidget,
    QLabel,
    QHBoxLayout,
    QVBoxLayout,
    QGridLayout,
    QWidget,
    QPushButton,
    QMainWindow,
    QApplication,
    QToolBar,
    QStatusBar,
)


class EpisodeFrame(QListWidget):
    """Widget holding the scrollable list of episodes and the episode list 
    selection"""

    def __init__(self, main, *args, **kwargs):
        super(EpisodeFrame, self).__init__(*args, **kwargs)
        self.main = main
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.populate()

        self.currentItemChanged.connect(self.on_item_click)

    def on_item_click(self, item, previous):
        self.main.plot_frame.plot_episode(self.row(item))

    def populate(self, data=None):
        self.clear()
        if data is not None:
            logging.debug("inserting data")
            self.addItems([f"Episode {i+1}" for i in range(len(data.series))])

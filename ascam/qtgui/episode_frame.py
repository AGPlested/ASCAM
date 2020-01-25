from PySide2.QtWidgets import (QListWidget, QLabel, QHBoxLayout, QVBoxLayout, 
        QGridLayout, QWidget, QPushButton, QMainWindow, QApplication, QToolBar, 
        QStatusBar)


class EpisodeFrame(QListWidget):
    """Widget holding the scrollable list of episodes and the episode list 
    selection"""
    def __init__(self, parent, *args, **kwargs):
        super(EpisodeFrame, self).__init__(*args, **kwargs)
        self.parent = parent
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.populate()

    def populate(self):
        for i in range(10):
            self.insertItem(i, round((i+1)/2)*"Red")
    #     button = QPushButton("cute button")
    #     button.clicked.connect(self.parent.add_tc)
    #     self.layout.addWidget(button)
    #     self.layout.addWidget(Color("red", "episodes"))


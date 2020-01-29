import logging

from PySide2.QtWidgets import ( QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
QPushButton, QLabel)


debug_logger = logging.getLogger("ascam.debug")


class IdealizationFrame(QTabWidget):

    def __init__(self):
        super(IdealizationFrame, self).__init__()

        self.tabs = [IdealizationTab(self)]
        self.addTab(self.tabs[0], "1")

        new_tab_button = QWidget()
        self.addTab(new_tab_button, "+")

        self.tabBarClicked.connect(self.new_tab)

    def new_tab(self, index):
        if index == len(self.tabs):
            self.add_tab()

    def add_tab(self):
        title = str(len(self.tabs)+1)
        debug_logger.debug(f"adding new tab with number {title}")
        tab = IdealizationTab(self)
        self.tabs.append(tab)
        self.insertTab(len(self.tabs)-1, tab, title)


class IdealizationTab(QWidget):

    def __init__(self, parent):
        super().__init__()
        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.addWidget(QLabel("Idealize me baby"))
        button = QPushButton("bye")
        button.clicked.connect(lambda *args: self.close())
        layout.addWidget(button)
        

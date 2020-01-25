from PySide2.QtWidgets import ( QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
QPushButton, QLabel)


class IdealizationFrame(QTabWidget):

    def __init__(self):
        super(IdealizationFrame, self).__init__()

        self.tabs = [QWidget()]
        self.tab_init(self.tabs[0])

    def tab_init(self, tab, title=None):
        if title is None:
            title = str(len(self.tabs))
        self.addTab(tab, title)
        layout = QVBoxLayout()
        tab.setLayout(layout)
        layout.addWidget(QLabel("Idealize me baby"))
        button = QPushButton("bye")
        button.clicked.connect(lambda *args: self.close())
        layout.addWidget(button)

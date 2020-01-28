from PySide2.QtWidgets import QDialog, QLineEdit, QVBoxLayout


class FilterFrame(QDialog):

    def __init__(self, main):
        super().__init__()
        self.setWindowTitle("Filter") 
        layout = QVBoxLayout()

        freq_entry = QLineEdit("1000")

        self.setLayout(layout)
        layout.addWidget(freq_entry)
        self.exec_()


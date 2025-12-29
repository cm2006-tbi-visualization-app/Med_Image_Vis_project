# 12)

from PyQt5 import QtWidgets, uic
import sys

class Ui(QtWidgets.QMainWindow):
    def __init__(self):
        super(Ui, self).__init__()
        uic.loadUi('<your layout ui file>', self) # 10)

        # 13)

        # 16, 17)

        self.show()

        # 14)

app = QtWidgets.QApplication(sys.argv)
window = Ui()
app.exec_()


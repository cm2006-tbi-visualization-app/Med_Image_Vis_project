import threading
import sys
import time

from PyQt5.QtWidgets import (QMainWindow, QPushButton, QVBoxLayout, QFrame, QApplication)


class Application(QMainWindow):

    def __init__(self):
        super(Application, self).__init__()
        
        self.counter = 0
        self.counter2 = 0

        # button
        self.button = QPushButton()
        # 1) ... 
        self.button.setText("click me :D")
        self.button.clicked.connect(self.when_clicked)


        # button2
        self.button2 = QPushButton()
        # 1) ...
        self.button2.setText("click me too >:D")
        self.button2.clicked.connect(self.when_clicked2)

        # layout
        self.layout = QVBoxLayout()
        # 2) ...
        self.layout.addWidget(self.button)

        self.layout.addWidget(self.button2)

        # frame & central widget
        self.frame = QFrame()
        # 3) ...
        self.frame.setLayout(self.layout)

        self.setCentralWidget(self.frame)

    def when_clicked(self):
        # 4) ...
        print("yo")
        self.counter+=1
        self.button.setText(self.counter.__str__())

    def when_clicked2(self):
        # 4) ...
        print("yo2")
        self.counter2+=1
        self.button2.setText(self.counter2.__str__())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Application()
    window.show()
    sys.exit(app.exec_())


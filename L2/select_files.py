import sys
from PyQt5 import QtWidgets, uic

# You'll also need these later:
from PyQt5.QtWidgets import QFileDialog

class SelectFilesWindow(QtWidgets.QDialog):  # Or QMainWindow if you used that
    def __init__(self):
        super().__init__()

        # This line loads your .ui file and connects all widgets
        uic.loadUi("select_files.ui", self)

        # After this line, you can access widgets by their objectName
        # For example: self.btn_browse_head, self.lineEdit_head_path, etc.
        # Connect browse buttons
        self.btn_browse_head.clicked.connect(self.browse_head_file)
        self.btn_browse_stripped.clicked.connect(self.browse_stripped_file)
        self.btn_browse_strain.clicked.connect(self.browse_strain_file)

        # Connect processing button
        self.calculate_strain_button.clicked.connect(self.start_processing)

        self.strip_head_button.clicked.connect(self.strip_head)

        # Connect visualization button
        self.visualize_button.clicked.connect(self.open_visualizer)


    def browse_head_file(self):
        # This will run when btn_browse_head is clicked
        pass

    def browse_stripped_file(self):
        pass

    def browse_strain_file(self):
        pass

    def start_processing(self):
        pass
    def strip_head(self):
        pass
    def open_visualizer(self):
        pass

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    # Create and show your pipeline window
    window = SelectFilesWindow()
    window.show()

    sys.exit(app.exec_())
import sys
from PyQt5.QtWidgets import QApplication, QDialog
from untitled import Ui_Dialog  # Import the generated UI class

class MyDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        # Connect signals manually (optional, already handled by QDialogButtonBox)
        self.ui.buttonBox.accepted.connect(self.on_ok)
        self.ui.buttonBox.rejected.connect(self.on_cancel)

    def on_ok(self):
        print("OK clicked")
        self.accept()  # Close dialog with Accepted status

    def on_cancel(self):
        print("Cancel clicked")
        self.reject()  # Close dialog with Rejected status

if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = MyDialog()

    # Show the dialog and get the result
    result = dialog.exec_()

    if result == QDialog.Accepted:
        print("Dialog accepted!")
    else:
        print("Dialog rejected!")

    sys.exit(0)

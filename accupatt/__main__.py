import sys

from PyQt5.QtWidgets import QApplication

from accupatt.windows.mainWindow import MainWindow
from accupatt.windows.loadCards import LoadCards

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = MainWindow()
    sys.exit(app.exec_())
import sys

from PyQt6.QtWidgets import QApplication

from accupatt.windows.mainWindow import MainWindow

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = MainWindow()
    sys.exit(app.exec())

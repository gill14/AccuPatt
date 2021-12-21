import sys

from PyQt5.QtWidgets import QApplication

from accupatt.windows.mainWindow import MainWindow
from accupatt.windows.loadCards import LoadCards

if __name__ == '__main__':
    app = QApplication(sys.argv)
    #file = '/Users/gill14/OneDrive - University of Illinois - Urbana/AccuProjects/Python Projects/Scan.png'
    #card_names = ['test1','test2']
    #w = LoadCards(file, card_names)
    w = MainWindow()
    sys.exit(app.exec_())
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtCore as qtc
from PyQt5 import QtGui as qtg
from PyQt5 import uic

Ui_Form, baseclass = uic.loadUiType('editFlyin.ui')

class EditFlyin(baseclass):

    applied = qtc.pyqtSignal(str)

    def __init__(self, currentDirectory, appInfo, parent = None):
        super().__init__()
        # Your code will go here
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.appInfo = appInfo
        self.ui.labelPath.setText(currentDirectory)
        self.ui.lineEditName.setText(appInfo.flyin_name)
        self.ui.lineEditLocation.setText(appInfo.flyin_location)
        self.ui.lineEditDate.setText(appInfo.flyin_date)
        self.ui.lineEditAnalyst.setText(appInfo.flyin_analyst)

        self.ui.buttonEditFolder.clicked.connect(self.editFolder)
        self.ui.dateEdit.dateChanged.connect(self.editDate)

        self.ui.buttonBox.accepted.connect(self.on_applied)
        self.ui.buttonBox.rejected.connect(self.reject)

        # Your code ends here
        self.show()

    def editFolder(self):
        folderpath = qtw.QFileDialog.getExistingDirectory(self, 'Select Folder')
        self.ui.labelPath.setText(folderpath)

    def editDate(self, date):
        self.ui.lineEditDate.setText(date.toString('d MMM yyyy'))

    def on_applied(self):
        #save to this appInfoInstance from fields
        newDir = self.ui.labelPath.text()
        self.appInfo.flyin_name = self.ui.lineEditName.text()
        self.appInfo.flyin_location = self.ui.lineEditLocation.text()
        self.appInfo.flyin_date = self.ui.lineEditDate.text()
        self.appInfo.flyin_analyst = self.ui.lineEditAnalyst.text()

        self.applied.emit(newDir)

        self.accept

if __name__ == '__main__':
    app = QtGui.QApplication([])
    gui = NewWindow()
    gui.show()
    app.exec_()

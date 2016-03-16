__all__ = ['main']

from PyQt4 import QtGui
import player
import connect

class PlayerApp(QtGui.QMainWindow, player.Ui_MainWindow):
    def __init__(self, parent=None):
        super(PlayerApp, self).__init__(parent)
        self.setupUi(self)

        # hook up menu
        self.action_Connect.triggered.connect(self.connect)
        self.action_Quit.triggered.connect(QtGui.qApp.quit)

    def connect(self):
        dialog = QtGui.QDialog()
        dialog.ui = connect.Ui_ConnectDialog()
        dialog.ui.setupUi(self)
        dialog.show()

        

def main():
    app = QtGui.QApplication([])
    form = PlayerApp()
    form.show()
    app.exec_()

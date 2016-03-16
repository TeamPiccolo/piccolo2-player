__all__ = ['main']

from PyQt4 import QtGui
import player

class PlayerApp(QtGui.QMainWindow, player.Ui_MainWindow):
    def __init__(self, parent=None):
        super(PlayerApp, self).__init__(parent)
        self.setupUi(self)


def main():
    app = QtGui.QApplication([])
    form = PlayerApp()
    form.show()
    app.exec_()

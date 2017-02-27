# Copyright 2014-2016 The Piccolo Team
#
# This file is part of piccolo2-player.
#
# piccolo2-player is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# piccolo2-player is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with piccolo2-player.  If not, see <http://www.gnu.org/licenses/>.

__all__ = ['ScheduleDialog']

from PyQt4 import QtGui, QtCore
import spectralist_ui
import datetime

class SpectraListDialog(QtGui.QDialog,spectralist_ui.Ui_SpectraListDialog):
    def __init__(self,parent=None,fileList=[]):
        super(SpectraListDialog, self).__init__(parent)
        self.setupUi(self)

        self._fileList = fileList
        self._fileList.sort()

        self.displayList(ftype='light')

        self.lightButton.toggled.connect(lambda:self.btnstate(self.lightButton))
        self.darkButton.toggled.connect(lambda:self.btnstate(self.darkButton))
        self.bothButton.toggled.connect(lambda:self.btnstate(self.bothButton))

    def btnstate(self,b):
        if b.isChecked():
            self.displayList(ftype=b.text())


    def displayList(self,ftype='both'):
        self.listWidget.clear()
        if ftype=='both':
            fl = self._fileList
        else:
            fl = []
            for f in self._fileList:
                if f.endswith('.'+ftype):
                    fl.append(f)
        self.listWidget.addItems(fl)
        self.listWidget.setCurrentRow(len(fl)-1)

    @staticmethod
    def getSpectrum(parent=None,fileList=[]):
        dialog = SpectraListDialog(parent,fileList)
        result = dialog.exec_()

        if result == QtGui.QDialog.Accepted:
            return str(dialog.listWidget.currentItem().text())
        else:
            return None

if __name__ == '__main__':
    import argparse
    from piccolo2.client import PiccoloJSONRPCClient


    parser = argparse.ArgumentParser()
    parser.add_argument('-u','--piccolo-url',metavar='URL',default='http://localhost:8080',help='set the URL of the piccolo server, default http://localhost:8080')
    args = parser.parse_args()
    
    piccolo = PiccoloJSONRPCClient(args.piccolo_url)

    fileList = piccolo.piccolo.getSpectraList(outDir='spectra')
    

    app = QtGui.QApplication([])

    print SpectraListDialog.getSpectrum(fileList=fileList)


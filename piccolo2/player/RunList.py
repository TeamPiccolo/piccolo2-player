# Copyright 2014-2017 The Piccolo Team
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

__all__ = ['RunListDialog']

from PyQt4 import QtGui, QtCore
import runlist_ui
import datetime

class RunListDialog(QtGui.QDialog,runlist_ui.Ui_RunListDialog):
    def __init__(self,parent=None,runList=[]):
        super(RunListDialog, self).__init__(parent)
        self.setupUi(self)

        self._runList = runList
        self.displayList()

    def displayList(self):
        self.listWidget.clear()
        self.listWidget.addItems(self._runList)
        self.listWidget.setCurrentRow(len(self._runList)-1)

    @staticmethod
    def getRun(parent=None,runList=[]):
        dialog = RunListDialog(parent,runList)
        result = dialog.exec_()

        if result == QtGui.QDialog.Accepted:
            run = dialog.listWidget.currentItem()
            if run is not None:
                return str(run.text())
        
        return None

if __name__ == '__main__':
    import argparse
    from piccolo2.client import PiccoloJSONRPCClient


    parser = argparse.ArgumentParser()
    parser.add_argument('-u','--piccolo-url',metavar='URL',default='http://localhost:8080',help='set the URL of the piccolo server, default http://localhost:8080')
    args = parser.parse_args()
    
    piccolo = PiccoloJSONRPCClient(args.piccolo_url)

    runList = piccolo.piccolo.getRunList()
    

    app = QtGui.QApplication([])

    print runList
    
    print RunListDialog.getRun(runList=runList)


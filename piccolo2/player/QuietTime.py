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

__all__ = ['QuietTimeDialog']

from PyQt4 import QtGui, QtCore
import quiettime_ui
import datetime

class QuietTimeDialog(QtGui.QDialog,quiettime_ui.Ui_QuietTimeDialog):
    def __init__(self,parent=None,start_time=None,end_time=None):
        super(QuietTimeDialog, self).__init__(parent)
        self.setupUi(self)

        if start_time is not None:
            self.startTimeEdit.setTime(QtCore.QTime.fromString(start_time))
        if end_time is not None:
            self.endTimeEdit.setTime(QtCore.QTime.fromString(end_time))
        
        if start_time is not None and end_time is not None:
            self.enableQuietTime.setCheckState(2)
        else:
            self.startTimeEdit.setEnabled(False)
            self.endTimeEdit.setEnabled(False)
        self.enableQuietTime.stateChanged.connect(self.handleQuietTime)

    def handleQuietTime(self):
        if self.enableQuietTime.checkState()==2:
            self.startTimeEdit.setEnabled(True)
            self.endTimeEdit.setEnabled(True)
        else:
            self.startTimeEdit.setEnabled(False)
            self.endTimeEdit.setEnabled(False)

        
    @property
    def start(self):
        if self.enableQuietTime.checkState()==2:
            return self.startTimeEdit.time().toPyTime().isoformat()

    @property
    def end(self):
        if self.enableQuietTime.checkState()==2:
            return self.endTimeEdit.time().toPyTime().isoformat()

    @staticmethod
    def getQuietTime(parent=None,start_time=None,end_time=None):
        dialog = QuietTimeDialog(parent,start_time=start_time,end_time=end_time)
        result = dialog.exec_()
        
        if result == QtGui.QDialog.Accepted:
            return (dialog.start,dialog.end)
        

if __name__ == '__main__':
    app = QtGui.QApplication([])
    
    print QuietTimeDialog.getQuietTime()

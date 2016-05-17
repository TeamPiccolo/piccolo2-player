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
import schedule_ui
import datetime

class ScheduleDialog(QtGui.QDialog,schedule_ui.Ui_ScheduleDialog):
    def __init__(self,parent=None):
        super(ScheduleDialog, self).__init__(parent)
        self.setupUi(self)

        now = QtCore.QDateTime(datetime.datetime.now())

        self.startTimeEdit.setMinimumDateTime(now)
        self.endTimeEdit.setMinimumDateTime(now)

    @property
    def start(self):
        return self.startTimeEdit.dateTime().toPyDateTime().isoformat()
    
    @property
    def interval(self):
        if self.repeatSchedule.checkState()==2:
            t = self.intervalEdit.time().toPyTime()
            return float(t.hour*3600+t.minute*60+t.second)

    @property
    def end(self):
        if self.repeatSchedule.checkState()==2:
            return self.endTimeEdit.dateTime().toPyDateTime().isoformat()

    @staticmethod
    def getSchedule(parent=None):
        dialog = ScheduleDialog(parent)
        result = dialog.exec_()
        
        if result == QtGui.QDialog.Accepted:
            return (dialog.start,dialog.interval,dialog.end)
        else:
            return (None,None,None)


if __name__ == '__main__':
    app = QtGui.QApplication([])
    
    print ScheduleDialog.getSchedule()


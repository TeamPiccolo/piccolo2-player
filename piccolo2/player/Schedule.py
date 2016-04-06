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


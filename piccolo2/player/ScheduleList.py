__all__ = ['PiccoloSchedule','ScheduleListDialog']

from PyQt4 import QtGui, QtCore
import schedulelist
import datetime

class PiccoloSchedule(QtGui.QStandardItemModel):
    def __init__(self,*args,**keywords):

        QtGui.QStandardItemModel.__init__(self,*args,**keywords)

        self._piccolo = None
        self.itemChanged.connect(self.suspendJob)

    def piccoloConnect(self,piccolo):
        self._piccolo = piccolo

        self.setHorizontalHeaderLabels(['job ID','job','start','interval','end','suspended'])
        
        self.update()
        
    def addJob(self,jid):
        data = self._piccolo.scheduler.getJob(jid=jid)
        job = '{1}.{0}('.format(*data['job'][:2])
        for k in data['job'][2]:
            job += '{0}={1},'.format(k,data['job'][2][k])
        if job.endswith(','):
            job = job[:-1]
        job += ')'

        row = []
        for r in  [str(data['jid']),job,data['at_time'],str(data['interval']),data['end_time']]:
            row.append(QtGui.QStandardItem(r))
        suspended = QtGui.QStandardItem(data['suspended'])
        suspended.setCheckable(True)
        if data['suspended']:
            suspended.setCheckState(2)
        row.append(suspended)
        self.appendRow(row)

    def update(self):
        if self._piccolo == None:
            return
        njobs = self._piccolo.scheduler.njobs()
        for i in range(self.rowCount(),njobs):
            self.addJob(i)
            
        for i in range(njobs):
            if self._piccolo.scheduler.suspended(jid=int(self.item(i,0).text())):
                self.item(i,5).setCheckState(2)
            else:
                self.item(i,5).setCheckState(0)

    def suspendJob(self,event):
        r = event.row()
        suspend = event.checkState()==2
        jid = int(self.item(r,0).text())
        if event.checkState()==2:
            self._piccolo.scheduler.suspend(jid=jid)
        else:
            self._piccolo.scheduler.unsuspend(jid=jid)

class ScheduleListDialog(QtGui.QDialog,schedulelist.Ui_ScheduleListWindow):
    def __init__(self,parent=None,scheduledJobs=None):
        super(ScheduleListDialog,self).__init__(parent)
        self.setupUi(self)

        self._scheduledJobs = scheduledJobs
        self.tableView.setModel(self._scheduledJobs)
        self.update()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        # check every second
        self.timer.start(1000)

    def update(self):
        self._scheduledJobs.update()

        TIMEFORMAT = "%Y-%m-%dT%H:%M:%S"
        now = datetime.datetime.now()
        for i in range(self._scheduledJobs.rowCount()):
            if self.tableView.isRowHidden(i):
                continue
            hide = False
            if len(self._scheduledJobs.item(i,4).text())>0:
                if now > datetime.datetime.strptime(str(self._scheduledJobs.item(i,4).text()),TIMEFORMAT):
                    hide = True
            else:
                if len(self._scheduledJobs.item(i,2).text())>0:
                    interval = float(self._scheduledJobs.item(i,3).text())
                    if interval<1.e-6 and now > datetime.datetime.strptime(str(self._scheduledJobs.item(i,2).text()),TIMEFORMAT):
                        hide = True
            if hide:
                self.tableView.hideRow(i)

        self.tableView.resizeColumnsToContents()
        

if __name__ == '__main__':
    import argparse
    from piccolo_client import PiccoloJSONRPCClient


    parser = argparse.ArgumentParser()
    parser.add_argument('-u','--piccolo-url',metavar='URL',default='http://localhost:8080',help='set the URL of the piccolo server, default http://localhost:8080')
    args = parser.parse_args()
    
    piccolo = PiccoloJSONRPCClient(args.piccolo_url)

    scheduledJobs = PiccoloSchedule()
    scheduledJobs.piccoloConnect(piccolo)

    app = QtGui.QApplication([])
    form = ScheduleListDialog(scheduledJobs = scheduledJobs)
    form.show()
    app.exec_()

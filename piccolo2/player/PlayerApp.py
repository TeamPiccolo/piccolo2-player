__all__ = ['main']

import piccolo_client

from PyQt4 import QtGui, QtCore
import player
import connect

class IntegrationTimes(QtGui.QStandardItemModel):
    def __init__(self,*args,**keywords):

        QtGui.QStandardItemModel.__init__(self,*args,**keywords)

        self._shutters = None
        self._spectrometers = None
        self._piccolo = None

        self.itemChanged.connect(self.updateIntegrationTime)


    def updateIntegrationTime(self,index):
        try:
            data = float(index.text())
        except:
            index.setForeground(QtGui.QBrush(QtGui.QColor('red')))
            return
        index.setForeground(QtGui.QBrush(QtGui.QColor('black')))
        self._piccolo.setIntegrationTime(shutter=self._shutters[index.column()],
                                         spectrometer=self._spectrometers[index.row()],
                                         milliseconds=data)

    def piccoloConnect(self,piccolo):
        self._piccolo = piccolo
        self._shutters = self._piccolo.getShutterList()
        self._spectrometers = self._piccolo.getSpectrometerList()
        
        self.setRowCount(len(self._spectrometers))
        self.setColumnCount(len(self._shutters))

        for i in range(len(self._shutters)):
            self.setHorizontalHeaderItem(i,QtGui.QStandardItem(self._shutters[i]))
        for j in range(len(self._spectrometers)):
            self.setVerticalHeaderItem(j,QtGui.QStandardItem(self._spectrometers[j]))

        for j in range(len(self._spectrometers)):
            for i in range(len(self._shutters)):
                data = self._piccolo.getIntegrationTime(shutter=self._shutters[i],
                                                        spectrometer=self._spectrometers[j])
                self.setItem(j,i,QtGui.QStandardItem(str(data)))



class ConnectDialog(QtGui.QDialog,connect.Ui_ConnectDialog):
    def __init__(self,parent=None):
        super(ConnectDialog, self).__init__(parent)
        self.setupUi(self)

    def setConnection(self,connection,data):
        if connection == 'http':
            self.connectHTTP.setChecked(True)
            self.serverURL.setText(data)
        elif connection == 'xbee':
            self.connectXBee.setChecked(True)
            self.xbeeSerial.setText(data)
        else:
            raise RuntimeError, 'unkown connection type',connection

    @property
    def getConnectionMethod(self):
        if self.connectHTTP.isChecked():
            return 'http'
        elif self.connectXBee.isChecked():
            return 'xbee'
        else:
            raise RuntimeError, 'Unkown connection method'

    def getData(self,parent=None):
        dialog = ConnectDialog(parent=parent)
        result = self.exec_()

        if result != QtGui.QDialog.Accepted:
            return

        method = self.getConnectionMethod
        data = None
        if method == 'http':
            data = self.serverURL.text()
        elif method == 'xbee':
            data = self.xbeeSerial.text()
        return method,str(data)

class PlayerApp(QtGui.QMainWindow, player.Ui_MainWindow):
    def __init__(self, parent=None):
        super(PlayerApp, self).__init__(parent)
        self.setupUi(self)

        # hook up menu
        self.action_Connect.triggered.connect(self.connectDialog)
        self.action_Quit.triggered.connect(QtGui.qApp.quit)

        # the piccolo connection
        self._piccolo = None
        self._connectionType = 'http'
        self._connectionData = 'http://localhost:8080'

        # the integration times
        self._times = IntegrationTimes()
        self.integrationTimeView.setModel(self._times)

        # connect recording buttons
        self.startRecordingButton.clicked.connect(self.startRecording)
        self.stopRecordingButton.clicked.connect(self.stopRecording)
        self.pauseRecordingButton.clicked.connect(self.pauseRecording)

        # periodically check status
        self.statusLabel = QtGui.QLabel()
        self.statusbar.addWidget(self.statusLabel)
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.status)
        # check every second
        self.timer.start(1000)

    def status(self):
        state = 'red'
        status = 'disconnected'
        if self._piccolo != None:
            status = 'connected'
            state = 'green'
            (busy,paused) = self._piccolo.piccolo.status()
            if busy:
                status = 'busy'
                state = 'orange'
            if paused:
                status += ', paused'
                self.pauseRecordingButton.setText("Unpause")
            else:
                self.pauseRecordingButton.setText("Pause")

        self.statusLabel.setText(status)
        self.statusLabel.setStyleSheet(' QLabel {color: %s}'%state)
        self.repaint()

    def startRecording(self):
        n = self.repeatMeasurements.value()
        if n==0:
            n='Inf'
        self._piccolo.piccolo.record(delay=self.delayMeasurements.value(),
                                     nCycles=n,
                                     outDir=str(self.outputDir.text()))

    def pauseRecording(self):
        self._piccolo.piccolo.pause()

    def stopRecording(self):
        self._piccolo.piccolo.abort()

    def connect(self,connection,data):
        ok = True
        if connection == 'http':
            self._connectionType = 'http'
            self._connectionData = data
            try:
                self._piccolo = piccolo_client.PiccoloJSONRPCClient(data)
            except:
                ok = False
                errorTitle = 'failed to connect'
                errorMsg = 'failed to connect to {}'.format(data)
        else:
            ok = False
            errorTitle ='not implemented'
            errorMsg = 'connection type {} is not implemented yet'.format(connection)
        if not ok:
            error=QtGui.QMessageBox.critical(self,errorTitle,errorMsg,QtGui.QMessageBox.Ok)
            return
        
        # hook up integration times
        self._times.piccoloConnect(self._piccolo.piccolo)

            
    def connectDialog(self):
        dialog = ConnectDialog()
        dialog.setConnection(self._connectionType,self._connectionData)
        data = dialog.getData()
        if data !=None:
            self.connect(data[0],data[1])
        

def main(connection):
    app = QtGui.QApplication([])
    form = PlayerApp()
    form.show()
    form.connect(connection[0],connection[1])
    app.exec_()

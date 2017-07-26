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
import os

class SpectraListDialog(QtGui.QDialog,spectralist_ui.Ui_SpectraListDialog):
    def __init__(self,parent=None,fileList=[]):
        super(SpectraListDialog, self).__init__(parent)
        self.setupUi(self)

        self._fileList = fileList
        self._fileList.sort()
        self.group_files_by_batch()

        self.displayBatches(ftype='light')
        self.displaySpectraFromBatch()

        self.lightButton.toggled.connect(lambda:self.btnstate(self.lightButton))
        self.darkButton.toggled.connect(lambda:self.btnstate(self.darkButton))
        self.bothButton.toggled.connect(lambda:self.btnstate(self.bothButton))

        self.listWidget.itemClicked.connect(self.displaySpectraFromBatch)


    def group_files_by_batch(self):
        self._batch_dict = {}
        self._batch_list = []

        curr_key = ''
        for f in self._fileList:
            #check for start of _batch
            if '0000.pico' in f:
                curr_key = f
                self._batch_list.append(curr_key)
                self._batch_dict[curr_key] = [f]
            else:
                self._batch_dict[curr_key].append(f)

        self._batch_titles = [self.prettify_batch(f) for f in self._batch_list]
        #point both file names and formatted titles towards the same file list
        for bt,bl in zip(self._batch_titles,self._batch_list):
            self._batch_dict[bt] = self._batch_dict[bl]

    def btnstate(self,b):
        if b.isChecked():
            #self.displayList(ftype=b.text())
            self.displayBatches(ftype=str(b.text()))
            self.displaySpectraFromBatch()


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



    def prettify_batch(self,batch):
        batch_name = os.path.basename(batch)
        batch_date = batch_name.split('_')[0]
        batch_count = len(self._batch_dict.get(batch,[]))
        batch_light = [l for l in['light','dark','']if batch.endswith(l)][0]
        if batch_light:
            batch_light = '({})'.format(batch_light)

        batch_string = '{0} {1}: {2} spectr'+('a','um')[batch_count==1]
        
        
        return batch_string.format(batch_date,batch_light,batch_count) 


    def displayBatches(self,ftype='both'):
        self.listWidget.clear()
        self.listWidget_2.clear()
        if ftype=='both':
            fl = self._batch_titles
        else:
            fl = [b for b in self._batch_titles if ftype in b]
        self.listWidget.addItems(fl)
        self.listWidget.setCurrentRow(len(fl)-1)

    def displaySpectraFromBatch(self):
        self.listWidget_2.clear()
        curr_batch = str(self.listWidget.currentItem().text())
        fl = self._batch_dict[curr_batch]
        self.listWidget_2.addItems(fl)
        self.listWidget_2.setCurrentRow(len(fl)-1)

    @staticmethod
    def getSpectrum(parent=None,fileList=[]):
        dialog = SpectraListDialog(parent,fileList)
        result = dialog.exec_()

        if result == QtGui.QDialog.Accepted:
            return str(dialog.listWidget_2.currentItem().text())
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


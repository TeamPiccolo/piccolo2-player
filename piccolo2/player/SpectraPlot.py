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


__all__ = ['SpectraPlot']

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.lines as mlines
import time
from PyQt4 import QtCore
import numpy as np


class SpectraPlot(FigureCanvas):
    BASE_SCALE = 1.5
    BASE_DELTA = 0.0001

    COLORS= [
        {
            "Upwelling":"royalblue",
            "Downwelling":"navy"
        },
        {
            "Upwelling":"tomato",
            "Downwelling":"darkred"
        },
        {
            "Upwelling":"limegreen",
            "Downwelling":"green"
        },

    ]

    def __init__(self,parent=None):
        super(SpectraPlot,self).__init__(Figure())
        self.setParent(parent)

        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self._theplot = None
        self._twinplot = None
        self._lines = None
        self._spectra = None
        self._units = None
        
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.updatePlot)
        # check every 5 second
        self.timer.start(5000)

    def wheelEvent(self,event):
        for plot in self.theplot,self.twinplot:
            ylim = plot.get_ylim()
            yrange = ylim[1]-ylim[0]
            
            if event.delta() > 0:
                s = 1/self.BASE_SCALE
            else:
                s = self.BASE_SCALE  

            y=yrange*(s-1)

            plot.set_ylim([ylim[0],ylim[1]+y])
        self.draw()       

    @property
    def theplot(self):
        if self._theplot is None:
            self._theplot = self.figure.add_subplot(111)
        return self._theplot

    @property
    def twinplot(self):
        if self._twinplot is None:
            self._twinplot = self.theplot.twinx()
        return self._twinplot



    def setUnits(self):
        pass
    def setTitle(self,title):
        self.theplot.clear()
        self.theplot.set_title(title)
        self.twinplot.clear()


    def pixelsAsSaturationPct(self,pixels,spectrum):
        if 'SaturationLevel' in spectrum:
            return "Percent Saturation",100.*pixels/spectrum['SaturationLevel']
        else:
            return "DN Count",pixels

    def zero_lower_ylim(self,axis):
        axis.set_ylim(0,axis.get_ylim()[1])

    def plotSpectra(self,spectra,directions,spectrometers,units="Saturation %"):
        print "plotSpectra called"
        date=None

        self._spectra = spectra
        self._spectrometers = spectrometers
        self._lines = []
        self._labels = []
        self._line_handles = []
        self._units = units

        colors = {}
        c_idx = 0
        plots = [self.theplot,self.twinplot]
        used_plots = [False]*len(plots)
        for i in range( len(self._spectra) ):
            s = self._spectra[i]

            if not s['SerialNumber'] in colors:
                #assign a color pallette to the spectrometer
                colors[s['SerialNumber']] = SpectraPlot.COLORS[c_idx]
                colors[s['SerialNumber']].update({'plot':plots[c_idx]})
                c_idx+=1

            if not s['SerialNumber'] in spectrometers:
                #only plot specified serial number(s)
                continue

            pixels = np.asarray(s.pixels,dtype=float)
            waveLengths = s.waveLengths
            if s['SerialNumber'].startswith("QEP"):
                pixels[pixels >= 100000] = np.nan
            pixels[pixels==-1] = np.nan
            if self._units == "Saturation %":
                ylabel,pixels = self.pixelsAsSaturationPct(pixels,s)
            else:
                ylabel = "DN Count"
                
            if len(set(directions)) > 1:
                #if there are multiple directions, label them
                short_dir = directions[i].replace('welling','')
                label = "{:s} ({:s})".format(s['SerialNumber'],short_dir)
            else:
                label = s['SerialNumber']

            pct_label = label# + self.getStaurationPercent(pixels,s)

            color = colors[s['SerialNumber']][directions[i]]
            curr_plot = colors[s['SerialNumber']]['plot']
            #spaghetti-ish code to determine which plots are actually used
            #will probably want to refactor
            used_plots[plots.index(curr_plot)] = True

            label_color = colors[s['SerialNumber']]['Downwelling']
            curr_plot.set_ylabel(ylabel,color=label_color)
            curr_plot.set_xlabel("Wavelength (nm)")
            [t.set_color(label_color)for t in curr_plot.get_yticklabels()]


            l, = curr_plot.plot(waveLengths,pixels,label=pct_label,color=color,lw=3)
            
            #ensure all plots have the same lower limit
            #self.zero_lower_ylim(curr_plot)
            self._lines.append(l)
            self._labels.append(label)

            date=s['Datetime']
        if len(spectra)>0:
            t = self.theplot.get_title()
            self.theplot.set_title('{}\n{}'.format(t,date))
            self.theplot.legend(handles=self._lines)
            #hide unused axes
            for i,is_used in enumerate(used_plots):
                plots[i].get_yaxis().set_visible(is_used)

        self.draw()

    def updatePlot(self):

        if self._spectra is None or self._spectrometers is None:
            return

        used_spectra = [s for s in self._spectra if s["SerialNumber"] in self._spectrometers]

        if used_spectra is None:
            return
        
        done = True

        for i in range(len(used_spectra)):
            if not used_spectra[i].complete:
                done = False
            pixels = np.asarray(used_spectra[i].pixels,dtype=float)
            if used_spectra[i]['SerialNumber'].startswith("QEP"):
                pixels[pixels >= 100000] = np.nan
            pixels[pixels==-1] = np.nan
            if self._units == "Saturation %":
                ylabel,pixels = self.pixelsAsSaturationPct(pixels,s)
            else:
                ylabel = "DN Count"
            
            

            pct_label = self._labels[i] #+ self.getStaurationPercent(pixels,s)
            
            self._lines[i].set_ydata(pixels)
            self._lines[i]._axes.set_ylabel(ylabel)
            self._lines[i].set_label(pct_label)
            
        self.theplot.relim()
        self.twinplot.relim()
        self.theplot.autoscale_view()
        self.twinplot.autoscale_view()
        #self.zero_lower_ylim(self.theplot)
        #self.zero_lower_ylim(self.twinplot)
        self.theplot.legend(handles=self._lines)
        self.draw()

    def save(self,fname):
        self.figure.savefig(fname)

if __name__ == ['__main__']:
    pass

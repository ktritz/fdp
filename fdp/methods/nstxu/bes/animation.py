# -*- coding: utf-8 -*-
"""
Created on Fri Apr 15 15:32:52 2016

@author: drsmith
"""

import gc

import numpy as np
import scipy.signal
import scipy.interpolate
from matplotlib import animation
import matplotlib.pyplot as plt

from fdp.classes.fdp_globals import FdpError
from fdp.classes.utilities import isContainer
from . import utilities as UT

def animate(*args, **kwargs):
    """Plot 2D signals"""
    return Animation(*args, **kwargs)
    

class Animation(object):
    """
    """
    
    def __init__(self, container, 
                 tmin=0.0, tmax=5.0,
                 savemovie=False,
                 hightimeres=False,
                 saveeps = False):
        
        if not isContainer(container):
            raise FdpError("Use at container level, not signal level")
        self.container = container
        if tmax>10:
            # if tmax large, assume ms input and convert to s
            tmin = tmin/1e3
            tmax = tmax/1e3
        self.tmin = tmin
        self.tmax = tmax
        self.hightimeres = hightimeres
        self.saveeps = saveeps
        self.savemovie = savemovie
        
        self.signals = None
        self.data = None
        self.time = None
        self.istart = None
        self.istop = None
        
        self.writer = None
        
        self.filter = None
        self.fdata = None
        self.ftime = None
        self.cdata = None
        
        self.getSignals()
        self.loadConfig()
        self.setTimeIndices()
        self.loadData()
        self.applyNormalization()
        self.filterData()
        #self.gridData()
        self.makeAnimation()
        if self.savemovie:
            self.saveAnimationVideo()
        
    def getSignals(self):
        self.signals = UT.get_signals_in_container(self.container)
    
    def loadConfig(self):
        self.container.loadConfig()
    
    def setTimeIndices(self):
        time = self.signals[0].time
        self.shot = self.signals[0].shot
        time_indices = np.where(np.logical_and(time>=self.tmin,
                                               time<=self.tmax))[0]
        self.istart = time_indices[0]
        self.istop = time_indices[time_indices.size-1]
        
        self.time = time[self.istart:self.istop+1]
        self.ntime = self.time.size
        print('Data points: {}'.format(self.ntime))

    def loadData(self):
        self.data = np.ones((7,9,self.ntime))*(-1)
        self.datamask = np.zeros((7,9),dtype=bool)
        for signal in self.signals:
            if not hasattr(signal, 'row'):
                continue
            row = signal.row
            column = signal.column
            zerosignal = np.mean(signal[0:1e3])
            self.data[row-1,column-1,:] = signal[self.istart:self.istop+1] - zerosignal
            #self.data[row-1,column-1,:] = signal[self.istart:self.istop+1]
            self.datamask[row-1,column-1] = True
        
    def applyNormalization(self):
        nrow,ncol,_ = self.data.shape
        # column-wise normalization factor
        self.colcal = np.zeros((ncol,))
        for col in np.arange(ncol):
            rowmask = self.datamask[:,col]
            if not rowmask.any():
                continue
            self.colcal[col] = np.mean(self.data[rowmask.nonzero(),col,0:self.ntime/20])
        # boxcar filter column-wise normalization factor
        tmp = self.colcal.copy()
        for col in np.arange(ncol):
            if col==0 or col==ncol-1:
                continue
            d = self.colcal[col-1:col+2]
            if np.count_nonzero(d)!=3:
                continue
            tmp[col] = np.mean(d)
        self.colcal = tmp.copy()
        # apply normalization to data array
        for row in np.arange(nrow):
            for col in np.arange(ncol):
                if self.datamask[row,col]:
                    self.data[row,col,:] = self.data[row,col,:] * self.colcal[col] / np.mean(self.data[row,col,0:self.ntime/20])
        
    def filterData(self):
        self.filter = scipy.signal.daub(4)
        self.filter = self.filter/np.sum(self.filter)
        self.fdata = scipy.signal.lfilter(self.filter, [1], 
            self.data,
            axis=2)
        #self.fdata = scipy.signal.decimate(self.fdata, 2, axis=2)
        #self.ftime = self.time[::2]
        self.ftime = self.time
        
    def gridData(self):
        nrad = 9
        npol = 7
        rgrid = np.arange(1,nrad+1)
        pgrid = np.arange(1,npol+1)
        rr,pp = np.meshgrid(rgrid, pgrid)
        print(pp.shape)
        rnew = np.arange(0.5,nrad+0.51,0.25)
        pnew = np.arange(0.5,npol+0.51,0.25)
        self.gdata = np.zeros((pnew.size,rnew.size,self.ftime.size))
        print('starting interpolation')
        for i in np.arange(self.ftime.size):
            if i!=0 and np.mod(i+1,100)==0:
                print('  frame {} of {}'.format(i+1,self.ftime.size))
            f = scipy.interpolate.interp2d(rr,
                                           pp,
                                           self.fdata[:,:,i].squeeze(),
                                           kind='linear')
            self.gdata[:,:,i] = f(rnew,pnew)
        
        
    def plotContourf(self, axes=None, index=None):
        return axes.contourf(np.arange(1,10.1),
                             np.arange(1,8.1),
                             self.fdata[::-1,:,index],
                             cmap=plt.cm.YlGnBu)
                           
    def plotPColorMesh(self, axes=None, index=None):
        return axes.pcolormesh(np.arange(1,10.1),
                               np.arange(1,8.1),
                               self.fdata[::-1,:,index],
                               cmap=plt.cm.YlGnBu)
        
    def makeAnimation(self):
        ims = []
        if self.hightimeres:
            frameint = 2
        else:
            frameint = 40
        nframes = np.int(self.ftime.size/frameint)
        self.fig = plt.figure(figsize=(6.4,7))
        ax1 = self.fig.add_subplot(2,1,1)
        ax1.set_xlabel('Radial channels')
        ax1.set_ylabel('Poloidal channels')
        ax1.set_aspect('equal')
        ax2 = self.fig.add_subplot(2,1,2)
        ax2.set_xlim(np.array([self.tmin,self.tmax])*1e3)
        ax2.set_xlabel('Time (ms)')
        ax2.set_ylabel('Signal (V)')
        self.fig.subplots_adjust(hspace=0.38)
        print('starting frame loop with {} frames'.format(nframes))
        clim = [np.amin(self.fdata), np.amax(self.fdata)]
        for i in np.arange(nframes):
            if i!=0 and np.mod(i+1,20)==0:
                print('  frame {} of {}'.format(i+1,nframes))
            #im = self.plotContourf(axes=ax1, index=i*frameint)
            im = self.plotPColorMesh(axes=ax1, index=i*frameint)
            im.set_clim(clim)
            if i==0:
                cb = plt.colorbar(im, ax=ax1)
                cb.set_label('Signal (V)')
                cb.draw_all()
            pt = ax2.plot(self.ftime*1e3, self.fdata[0,1,:], 'b',
                          self.ftime*1e3, self.fdata[4,1,:], 'g',
                          self.ftime*1e3, self.fdata[0,6,:], 'c',
                          self.ftime*1e3, self.fdata[5,6,:], 'm')
            ax2.get_xaxis().get_major_formatter().set_useOffset(False)
            ax1_title = ax1.annotate('BES | {} | t={:.3f} ms'.format(
                self.shot,
                self.ftime[i*frameint]*1e3),
                xy=(0.5, 1.04), 
                xycoords='axes fraction',
                horizontalalignment ='center',
                size='large')
            ln = ax2.plot(np.ones(2)*self.ftime[i*frameint]*1e3,
                          ax2.get_ylim(), 
                          'r')
            an_l0 = ax2.annotate('Core Top',
                                  xy=(self.ftime[0]*1e3+0.01,
                                      self.fdata[0,1,15]+0.6),
                                  color='b')
            an_l1 = ax2.annotate('Core Bottom',
                                  xy=(self.ftime[0]*1e3+0.01,
                                      self.fdata[4,1,15]-0.6),
                                  color='g')
            an_l2 = ax2.annotate('SOL Top',
                                  xy=(self.ftime[0]*1e3+0.01,
                                      self.fdata[0,6,15]+0.6),
                                  color='c')
            an_l3 = ax2.annotate('SOL Bottom',
                                  xy=(self.ftime[0]*1e3+0.01,
                                      self.fdata[5,6,15]-0.6),
                                  color='m')
            ax2_title = ax2.annotate('BES | {}'.format(self.shot),
                xy=(0.5, 1.04), 
                xycoords='axes fraction',
                horizontalalignment ='center',
                size='large')
            plt.draw()
            if self.saveeps:
                filename = 'Bes2d_{}_{}.eps'.format(
                                self.shot,
                                np.int(self.ftime[i*frameint]*1e7))
                self.fig.savefig(filename, format='eps', transparent=True)
                ax1.cla()
                ax2.cla()
            if self.savemovie:
                artists = [cb.solids, pt[0], pt[1], pt[2], pt[3], ln[0], ax1_title, 
                           an_l0, an_l1, an_l2, an_l3, ax2_title]
                gc.disable()  # disable garbage collection to keep list appends fast
                if hasattr(im, 'collections'):
                    ims.append(im.collections+artists)
                else:
                    ims.append([im]+artists)
                gc.enable()
            
        if self.savemovie:
            print('calling ArtistAnimation')
            self.animation = animation.ArtistAnimation(self.fig, ims, 
                                                       blit=False,
                                                       interval=50,
                                                       repeat=False)
                                                   
    def saveAnimationVideo(self):
        print('calling ArtistAnimation.save()')
        filename = 'Bes2d_{}_{}ms.mp4'.format(
            self.shot,
            np.int(self.tmin*1e3))
        writer = animation.FFMpegWriter(fps=30,
                                        bitrate=1e5)
        self.animation.save(filename, writer=writer)


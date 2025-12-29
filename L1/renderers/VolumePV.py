__author__ = 'fabian sinzinger'
__email__ = 'fabiansi@kth.se'

import os
import sys

import vtk
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

import pyvista as pv
from pyvistaqt import QtInteractor


class VolumeRendererPV:
    def __init__(self, filename, frame):

        # load file and set up reader source 
        reader_src = vtk.vtkNIFTIImageReader()
        reader_src.SetFileName(filename)

        reader_src.Update()



        # convert tp pyvista object
        pyvista_volume = pv.wrap(reader_src.GetOutput())

        self.plotter = QtInteractor(frame)
        self.interactor = self.plotter.interactor
        self.renderer = self.plotter.renderer

        # add output of the reader source to the plotter
        self.plotter.add_volume(pyvista_volume)


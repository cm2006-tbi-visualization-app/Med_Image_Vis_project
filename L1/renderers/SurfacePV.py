__author__ = 'fabian sinzinger'
__email__ = 'fabiansi@kth.se'

import os
import sys

import vtk
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

import pyvista as pv
from pyvistaqt import QtInteractor


class SurfaceRendererPV:
    def __init__(self, filename, frame):

        reader_src = vtk.vtkNIFTIImageReader()
        reader_src.SetFileName(filename)

        reader_src.Update()

        # (filter) 
        cast_filter = vtk.vtkImageCast()
        cast_filter.SetInputConnection(reader_src.GetOutputPort())
        cast_filter.SetOutputScalarTypeToUnsignedShort()

        # marching cubes (mapper)
        contour = vtk.vtkMarchingCubes()
        contour.SetInputConnection(cast_filter.GetOutputPort())
        contour.ComputeNormalsOn()
        contour.ComputeGradientsOn()
        contour.SetValue(0, 100)

        # force the vtk pipeline to load the data now
        contour.Update()

        # convert tp pyvista object
        pyvista_mesh = pv.wrap(contour.GetOutput())

        self.plotter = QtInteractor(frame)
        self.interactor = self.plotter.interactor
        self.renderer = self.plotter.renderer

        self.plotter.add_mesh(pyvista_mesh)



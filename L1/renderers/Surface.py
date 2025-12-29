__author__ = 'fabian sinzinger'
__email__ = 'fabiansi@kth.se'

import os
import sys

import vtk
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor


class SurfaceRenderer:
    def __init__(self, filename, frame):
        # load the data (source)
        reader_src = vtk.vtkNIFTIImageReader()
        reader_src.SetFileName(filename)

        # filter 
        cast_filter = vtk.vtkImageCast()
        cast_filter.SetInputConnection(reader_src.GetOutputPort())
        cast_filter.SetOutputScalarTypeToUnsignedShort()

        # marching cubes (mapper)
        contour = vtk.vtkMarchingCubes()
        contour.SetInputConnection(cast_filter.GetOutputPort())
        contour.ComputeNormalsOn()
        contour.ComputeGradientsOn()
        contour.SetValue(0, 100)
        
        con_mapper =vtk.vtkPolyDataMapper()
        con_mapper.SetInputConnection(contour.GetOutputPort())
       
        # actor
        actor = vtk.vtkActor()
        actor.SetMapper(con_mapper)

        # setup the camera and the renderer
        self.renderer = vtk.vtkRenderer()

        camera = self.renderer.MakeCamera()
        camera.SetViewUp(0., 0., -.1)
        camera.SetPosition(-500, 100, 100)
        #camera.ResetCamera()

        self.renderer.SetBackground(0., 0., 0.) # so to black
        self.renderer.SetActiveCamera(camera)
        self.renderer.AddActor(actor) 

        # window interaction (camera movement etc)
        self.interactor = QVTKRenderWindowInteractor(frame)
        style = vtk.vtkInteractorStyleTrackballCamera()
        self.interactor.SetInteractorStyle(style)

        self.interactor.Initialize()



__author__ = 'fabian sinzinger'
__email__ = 'fabiansi@kth.se'

import os
import sys

import vtk
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor


class VolumeRenderer:
    def __init__(self, filename, frame):
        # load the data
        reader_src = vtk.vtkNIFTIImageReader()
        reader_src.SetFileName(filename)

        # transfer function, colot luts
        color_trans_fun = vtk.vtkColorTransferFunction()
        color_trans_fun.SetColorSpaceToRGB()
        color_trans_fun.AddRGBPoint(0,0,0,0)
        #color_trans_fun.AddRGBPoint(127,0,1,0)
        color_trans_fun.AddRGBPoint(512,1.0,1.0,1.0)

        # set the volume properties
        opacity_trans_fun = vtk.vtkPiecewiseFunction()
        opacity_trans_fun.AddPoint(0,0.)
        opacity_trans_fun.AddPoint(256,.01)


        vol_property = vtk.vtkVolumeProperty()
        vol_property.SetColor(color_trans_fun)
        vol_property.SetScalarOpacity(opacity_trans_fun)
        #vol_property.ShadeOn()
        vol_property.SetInterpolationTypeToLinear()
        vol_property.SetDiffuse(0.7)
        vol_property.SetAmbient(0.01)
        vol_property.SetSpecular(0.5)
        vol_property.SetSpecularPower(70.0)
        # setup the volume mapper
        volume_mapper = vtk.vtkGPUVolumeRayCastMapper()# vtkImageData converted into ?
        volume_mapper.SetInputConnection(reader_src.GetOutputPort())
        # setup the actor
        volume_actor = vtk.vtkVolume()
        volume_actor.SetMapper(volume_mapper)
        volume_actor.SetProperty(vol_property)
        # setup the camera and the renderer ---------------------------
        camera = vtk.vtkCamera()
        camera.SetFocalPoint(100,100,100)
        camera.SetPosition(-500, 100, 100)
        camera.SetViewUp(0., 1., 0.)

        # 9 create a renderer and set the color of the renderers background to black (0., 0., 0.)
        self.renderer = vtk.vtkRenderer()
        self.renderer.SetBackground(0.,0.,0.)
        # 10 set the renderers camera as active
        self.renderer.SetActiveCamera(camera)
        # 11 add the volume actor to the renderer
        self.renderer.AddActor(volume_actor)


        # 12 create a render window
        #render_window=vtk.vtkRenderWindow()
        # 13 add renderer to the render window
        #render_window.AddRenderer(renderer)

        # window interaction (camera movement etc)
        self.interactor = QVTKRenderWindowInteractor(frame)
        style = vtk.vtkInteractorStyleTrackballCamera()
        self.interactor.SetInteractorStyle(style)

        self.interactor.Initialize()



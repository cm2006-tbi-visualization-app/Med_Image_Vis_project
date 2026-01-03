import vtk
import sys
import nibabel as nib
import numpy as np
import matplotlib.pyplot as plt
import types
from PyQt5 import QtWidgets, uic, QtCore
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
global plane


class claaass():

    def __init__(self):
        # 1 get data path from the first argument given
        brain_data_path = sys.argv[1]
        img = nib.load(brain_data_path)
        data = img.get_fdata()
        print("Min:", np.min(data), "Max:", np.max(data))

        # Calculate the actual range and distribution
        data_non_zero = data[data > 100]  # Ignore background noise for better statistics
        if len(data_non_zero) == 0:
            data_non_zero = data

        d_min = np.min(data)
        d_max = np.max(data)
        p5, p10, p30, p70, p90, p99 = np.percentile(data_non_zero, [5, 10, 30, 70, 90, 99])
        self.data_stats = types.SimpleNamespace(
            d_min=d_min,
            d_max=d_max,
            p5=p5,
            p10=p10,
            p30=p30,
            p70=p70,
            p90=p90,
            p99=p99
        )
        # 2 set up the source
        reader_source = vtk.vtkNIFTIImageReader()#produces a vtkImageData - 3D voxel grid w scalar values
        reader_source.SetFileName(brain_data_path)

        # 3 set up the volume mapper
        volume_mapper = vtk.vtkGPUVolumeRayCastMapper()# vtkImageData converted into ?
        volume_mapper.SetInputConnection(reader_source.GetOutputPort())

        # 4 create a transfer function for color
        #   for now: map value 0   -> black: (0., 0., 0.)
        #                      512 -> black: (1., 1., 1.)
        import nibabel as nib
        import numpy as np

        img = nib.load(brain_data_path)
        data = img.get_fdata()
        print("Min:", np.min(data), "Max:", np.max(data))

        color_fun_head = vtk.vtkColorTransferFunction()
        color_fun_head.SetColorSpaceToRGB()
        # Use p10 (skin/soft tissue) up to p30 (denser tissue)
        color_fun_head.AddRGBPoint(self.data_stats.d_min, 0.0, 0.0, 0.0)      # Transparent background
        color_fun_head.AddRGBPoint(self.data_stats.p10, 0.55, 0.35, 0.30)     # Flesh tone
        color_fun_head.AddRGBPoint(self.data_stats.p30, 0.8, 0.4, 0.3)      # Lighter skin/bone
        color_fun_head.AddRGBPoint(self.data_stats.p70, 1, 0.9, 0.8)      # Lighter skin/bone
        color_fun_head.AddRGBPoint(self.data_stats.d_max, 0.9, 0.9, 0.9)    # Highlights

        # --- 7. Head/Skin Opacity Transfer Function ---
        opacity_fun_head = vtk.vtkPiecewiseFunction()
        # We want a "Ghostly" shell.
        # We define the skin surface and then drop opacity to zero immediately
        # so we don't block the brain inside.

        opacity_fun_head.AddPoint(self.data_stats.d_min, 0.0)
        opacity_fun_head.AddPoint(self.data_stats.p5 - 1, 0.05)
        opacity_fun_head.AddPoint(self.data_stats.p5, 0.3)
        # Reach full desired opacity at p10 (the main skin surface)
        opacity_fun_head.AddPoint(self.data_stats.p10, 0.9)
        # Keep it solid through the tissue
        opacity_fun_head.AddPoint(self.data_stats.p30, 0.5)
        # Drop to 0 inside so we can see the brain
        opacity_fun_head.AddPoint(self.data_stats.p70, 0.5)
        opacity_fun_head.AddPoint(self.data_stats.p99, 0.5)
        opacity_fun_head.AddPoint(self.data_stats.d_max, 0.5)


        # 6 set up the volume properties with linear interpolation
        vol_property = vtk.vtkVolumeProperty()
        vol_property.SetColor(color_fun_head)
        vol_property.SetScalarOpacity(opacity_fun_head)
        #vol_property.ShadeOn()
        vol_property.SetInterpolationTypeToLinear()
        vol_property.SetDiffuse(0.7)
        vol_property.SetAmbient(0.01)
        vol_property.SetSpecular(0.5)
        vol_property.SetSpecularPower(70.0)




        # 7 set up the actor and connect it to the mapper and the volume properties
        volume_actor = vtk.vtkVolume()
        volume_actor.SetMapper(volume_mapper)
        volume_actor.SetProperty(vol_property)

        # 8 set up the camera
        #   for now: up-vector:       (0., 1., 0.)
        #            camera position: (-500, 100, 100)
        #            focal point:     (100, 100, 100)
        camera = vtk.vtkCamera()
        camera.SetFocalPoint(100,100,100)
        camera.SetPosition(-500, 100, 100)
        camera.SetViewUp(0., 1., 0.)

        # 9 create a renderer and set the color of the renderers background to black (0., 0., 0.)
        renderer = vtk.vtkRenderer()
        renderer.SetBackground(0.,0.,0.)
        # 10 set the renderers camera as active
        renderer.SetActiveCamera(camera)
        # 11 add the volume actor to the renderer
        renderer.AddActor(volume_actor)
        # 12 create a render window
        render_window=vtk.vtkRenderWindow()
        # 13 add renderer to the render window
        render_window.AddRenderer(renderer)
        # 14 create an interactor
        interactor = vtk.vtkRenderWindowInteractor()
        # 15 connect interactor to the render window
        render_window.SetInteractor(interactor)
        # 16 start displaying the render window
        render_window.Render()

        # 17 make the window interactive (start the interactor)
        interactor.Start()

if __name__ == '__main__':
    cl = claaass()
import vtk
import sys


# 1 get data path from the first argument given
brain_data_path = sys.argv[1]

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

color_trans_fun = vtk.vtkColorTransferFunction()
color_trans_fun.SetColorSpaceToRGB()
color_trans_fun.AddRGBPoint(0, 0, 0, 0)         # background: black
color_trans_fun.AddRGBPoint(500, 0.8, 0.4, 0.3) # gray matter
color_trans_fun.AddRGBPoint(1500, 1.0, 0.8, 0.6) # white matter
color_trans_fun.AddRGBPoint(3000, 0.9, 0.9, 0.7) # brightest areas


# 5 create a scalar transfer function for opacity
#   for now: map value 0   -> 0. 
#                      256 -> .01
opacity_trans_fun = vtk.vtkPiecewiseFunction()
opacity_trans_fun = vtk.vtkPiecewiseFunction()
opacity_trans_fun.AddPoint(0, 0.0)        # background
opacity_trans_fun.AddPoint(500, 0.05)    # gray matter
opacity_trans_fun.AddPoint(1500, 0.2)    # white matter
opacity_trans_fun.AddPoint(3000, 0.35)   # bright regions
opacity_trans_fun.AddPoint(256, 0.01)    # max intensity


# 6 set up the volume properties with linear interpolation 
vol_property = vtk.vtkVolumeProperty()
vol_property.SetColor(color_trans_fun)
#vol_property.SetScalarOpacity(opacity_trans_fun)
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
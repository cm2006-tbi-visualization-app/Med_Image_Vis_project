import vtk
import sys
import nibabel as nib
import numpy as np
import matplotlib.pyplot as plt
import nibabel as nib

global plane


def my_callback(obj, event):
    global plane
    obj.GetPlane(plane)
    print(f"\nobject:{obj}")
    print(f"event:{event}\n")


# 1 get data path from the first argument given
brain_data_path = sys.argv[1]

img = nib.load(brain_data_path)
data = img.get_fdata()
print("Min:", np.min(data), "Max:", np.max(data))

'''
plt.hist(data[data > 0].flatten(), bins=200)
plt.xlabel("Voxel intensity")
plt.ylabel("Count")
plt.show()'''

plane = vtk.vtkPlane()

# 2 set up the source
reader_source = vtk.vtkNIFTIImageReader()#produces a vtkImageData - 3D voxel grid w scalar values
reader_source.SetFileName(brain_data_path)

# 3 set up the volume mapper
volume_mapper = vtk.vtkGPUVolumeRayCastMapper()# vtkImageData converted into ?
volume_mapper.SetInputConnection(reader_source.GetOutputPort())
volume_mapper.SetSampleDistance(0.5)

volume_mapper.AddClippingPlane(plane)

# Calculate the actual range and distribution
data_non_zero = data[data > 70]  # Ignore background noise for better statistics
if len(data_non_zero) == 0:
    data_non_zero = data

d_min = np.min(data)
d_max = np.max(data)
p10 = np.percentile(data_non_zero, 10)
p30 = np.percentile(data_non_zero, 30) # Likely Gray Matter
p70 = np.percentile(data_non_zero, 70) # Likely White Matter
p99 = np.percentile(data_non_zero, 99) # Brightest structures

# --- 4. Dynamic Color Transfer Function ---
color_trans_fun = vtk.vtkColorTransferFunction()
color_trans_fun.SetColorSpaceToRGB()

# Map colors to the calculated percentiles
color_trans_fun.AddRGBPoint(d_min, 0, 0, 0)        # Black (Background)
color_trans_fun.AddRGBPoint(p10, 0.2, 0, 0)        # Dark Red (Skin/Fat)
color_trans_fun.AddRGBPoint(p30, 0.8, 0.4, 0.3)    # Pinkish (Gray Matter)
color_trans_fun.AddRGBPoint(p70, 1.0, 0.9, 0.8)    # Off-white (White Matter)
color_trans_fun.AddRGBPoint(d_max, 0.9, 0.9, 1.0)  # Cool white (Highlights)

# --- 5. Dynamic Opacity Transfer Function ---
opacity_trans_fun = vtk.vtkPiecewiseFunction()

# This is the crucial part for "cutting" through the head
opacity_trans_fun.AddPoint(p10 * 1.2, 0.0)
opacity_trans_fun.AddPoint(d_min, 0.0)      # Totally transparent background
opacity_trans_fun.AddPoint(p10 * 0.5, 0.0)  # Keep noise transparent
opacity_trans_fun.AddPoint(p30, 0.15)       # Make brain tissue semi-transparent
opacity_trans_fun.AddPoint(p70, 0.4)        # Make white matter denser
opacity_trans_fun.AddPoint(p99, 0.6)        # Max opacity for brightest parts


# 5 create a scalar transfer function for opacity


# 6 set up the volume properties with linear interpolation 
vol_property = vtk.vtkVolumeProperty()
vol_property.SetColor(color_trans_fun)
vol_property.SetScalarOpacity(opacity_trans_fun)
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

volume_actor_brain = vtk.vtkVolume()
volume_actor_brain.SetMapper(volume_mapper)
volume_actor_brain.SetProperty(vol_property)

# 8 set up the camera
#   for now: up-vector:       (0., 1., 0.)
#            camera position: (-500, 100, 100)
#            focal point:     (100, 100, 100)
camera = vtk.vtkCamera()
camera.SetFocalPoint(100, 100, 100)
camera.SetPosition(-500, 100, 100)
camera.SetViewUp(0., 1., 0.)

# 9 create a renderer and set the color of the renderers background to black (0., 0., 0.)
renderer = vtk.vtkRenderer()
renderer.SetBackground(0.,0.,0.)
# 10 set the renderers camera as active
renderer.SetActiveCamera(camera)
# 11 add the volume actor to the renderer
renderer.AddActor(volume_actor)
renderer.AddActor(volume_actor_brain)
# 12 create a render window
render_window=vtk.vtkRenderWindow()

# 13 add renderer to the render window
render_window.AddRenderer(renderer)
# 14 create an interactor
interactor = vtk.vtkRenderWindowInteractor()
# 15 connect interactor to the render window
render_window.SetInteractor(interactor)

interactor.Initialize()

plane_widget = vtk.vtkImplicitPlaneWidget()
plane_widget.SetInteractor(interactor)
plane_widget.SetInputConnection(reader_source.GetOutputPort())
plane_widget.PlaceWidget()
plane_widget.AddObserver('InteractionEvent' , my_callback)

plane_widget.DrawPlaneOn() # Ensure the plane is visible
plane_widget.GetPlaneProperty().SetOpacity(0.2) # Make it faint so you can see through it
plane_widget.On() # This actually activates the widget in the scene

# 16 start displaying the render window
render_window.Render()

# 17 make the window interactive (start the interactor)
interactor.Start()
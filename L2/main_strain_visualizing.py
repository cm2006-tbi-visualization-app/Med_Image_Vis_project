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

def volume_actor(file_path, color_function, opacity_function, smoothing_std = 0.0):
    # 2 set up the source
    reader_source = vtk.vtkNIFTIImageReader()#produces a vtkImageData - 3D voxel grid w scalar values
    reader_source.SetFileName(file_path)

    if smoothing_std > 0:
        gaussian_smooth = vtk.vtkImageGaussianSmooth()
        gaussian_smooth.SetInputConnection(reader_source.GetOutputPort())
        gaussian_smooth.SetStandardDeviation(smoothing_std) # Adjust this (0.5 to 1.5) to smooth the "boxes"
        input_connection = gaussian_smooth.GetOutputPort()
    else:
        input_connection = reader_source.GetOutputPort()

    #mapper
    volume_mapper = vtk.vtkGPUVolumeRayCastMapper()
    volume_mapper.SetInputConnection(input_connection)
    volume_mapper.SetSampleDistance(0.1)


    # 6 set up the volume properties with linear interpolation
    vol_property = vtk.vtkVolumeProperty()
    vol_property.SetColor(color_function)
    vol_property.SetScalarOpacity(opacity_function)
    #vol_property.ShadeOn()
    vol_property.SetInterpolationTypeToLinear()
    vol_property.SetDiffuse(0.9)
    vol_property.SetAmbient(0.01)
    vol_property.SetSpecular(0.5)
    vol_property.SetSpecularPower(70.0)


    # 7 set up the actor and connect it to the mapper and the volume properties
    volume_actor = vtk.vtkVolume()
    volume_actor.SetMapper(volume_mapper)
    volume_actor.SetProperty(vol_property)

    return volume_actor, volume_mapper, reader_source


# 1 get data path from the first argument given
brain_data_path = sys.argv[2]
img = nib.load(brain_data_path)
data = img.get_fdata()
print("Min:", np.min(data), "Max:", np.max(data))

# Calculate the actual range and distribution
data_non_zero = data[data > 100]  # Ignore background noise for better statistics
if len(data_non_zero) == 0:
    data_non_zero = data
d_min = np.min(data)
d_max = np.max(data)
p10 = np.percentile(data_non_zero, 10)
p30 = np.percentile(data_non_zero, 30) # Likely Gray Matter
p70 = np.percentile(data_non_zero, 70) # Likely White Matter
p90 = np.percentile(data_non_zero, 90)
p99 = np.percentile(data_non_zero, 99) # Brightest structures

# --- 4. Dynamic Color Transfer Function ---
color_fun_strain = vtk.vtkColorTransferFunction()
color_fun_strain.SetColorSpaceToRGB()

# Highest deformation (0.2) -> Lowest deformation (0.0)
color_fun_strain.AddRGBPoint(0.200, 1.0, 0.0, 0.0)   # 1. Red
color_fun_strain.AddRGBPoint(0.18, 1.0, 0.5, 0.0)   # 2. Orange
color_fun_strain.AddRGBPoint(0.16, 1.0, 1.0, 0.0)   # 3. Yellow
color_fun_strain.AddRGBPoint(0.14, 0.6, 1.0, 0.2)   # 4. Light Green
color_fun_strain.AddRGBPoint(0.12, 0.0, 0.8, 0.0)   # 5. Semi Light Green
color_fun_strain.AddRGBPoint(0.10, 0.0, 0.4, 0.0)   # 6. Dark Green
color_fun_strain.AddRGBPoint(0.08, 0.0, 1.0, 1.0)   # 7. Cyan
color_fun_strain.AddRGBPoint(0.06, 0.5, 0.8, 1.0)   # 8. Baby Blue
color_fun_strain.AddRGBPoint(0.04, 0.0, 0.0, 1.0)   # 9. Blue
color_fun_strain.AddRGBPoint(0.02, 0.0, 0.0, 0.4)   # 10. Dark Blue
color_fun_strain.AddRGBPoint(0, 0.0, 0.0, 0.4)   # 10. Dark Blue AGAIN


# --- 5. Dynamic Opacity Transfer Function ---
opacity_fun_strain = vtk.vtkPiecewiseFunction()
# 0.00 to 0.005: Background/Air remains invisible
opacity_fun_strain.AddPoint(0.000, 0.0)
opacity_fun_strain.AddPoint(0.005, 0.0)
# Make lower deformations partially transparent to see depth
# 0.005 to 0.02: Gradually increase opacity for dark blue areas
opacity_fun_strain.AddPoint(0.010, 0.1)   # Very transparent for lowest deformations
opacity_fun_strain.AddPoint(0.015, 0.2)
opacity_fun_strain.AddPoint(0.020, 0.4)   # Dark blue starts becoming visible
# 0.02 to 0.08: Mid-range deformations (blues to greens)
opacity_fun_strain.AddPoint(0.04, 0.7)    # Blue area - fairly visible
opacity_fun_strain.AddPoint(0.06, 0.8)    # Baby blue
opacity_fun_strain.AddPoint(0.08, 0.9)    # Cyan - mostly opaque
# 0.10 to 0.20: Higher deformations (greens to reds)
opacity_fun_strain.AddPoint(0.10, 0.95)   # Dark green - nearly solid
opacity_fun_strain.AddPoint(0.12, 0.98)   # Semi light green
opacity_fun_strain.AddPoint(0.14, 1.0)    # Light green - your current max at ~0.141
opacity_fun_strain.AddPoint(0.16, 1.0)    # Yellow - fully opaque
opacity_fun_strain.AddPoint(0.18, 1.0)    # Orange - fully opaque
opacity_fun_strain.AddPoint(0.20, 1.0)    # Red - fully opaque (even though not in your data)



'''
color_fun_anatomy = vtk.vtkColorTransferFunction()
color_fun_anatomy.SetColorSpaceToRGB()
color_fun_anatomy.AddRGBPoint(0, 0, 0, 0)
color_fun_anatomy.AddRGBPoint(500, 1, 1, 1) #grayscale

opacity_fun_anatomy = vtk.vtkPiecewiseFunction()
opacity_fun_anatomy.AddPoint(0, 0.0)
opacity_fun_anatomy.AddPoint(50, 0.15) '''


color_fun_anatomy = vtk.vtkColorTransferFunction()
color_fun_anatomy.SetColorSpaceToRGB()
color_fun_anatomy.AddRGBPoint(d_min, 0, 0, 0)        # Black (Background)
color_fun_anatomy.AddRGBPoint(p10, 0.2, 0, 0)        # Dark Red (Skin/Fat)
color_fun_anatomy.AddRGBPoint(p30, 0.8, 0.4, 0.3)    # Pinkish (Gray Matter)
color_fun_anatomy.AddRGBPoint(p70, 1.0, 0.9, 0.8)    # Off-white (White Matter)
color_fun_anatomy.AddRGBPoint(d_max, 0.9, 0.9, 1.0)  # Cool white (Highlights)

opacity_fun_anatomy = vtk.vtkPiecewiseFunction()
# Filter out EVERYTHING except the most distinct features
opacity_fun_anatomy.AddPoint(d_min, 0.0)
opacity_fun_anatomy.AddPoint(p10, 0.0)

# p10 to p99: Make the bulk of the brain visible but translucent
# Using 0.2 means it is 20% opaque (80% transparent)
opacity_fun_anatomy.AddPoint(p30, 0.005)  # Gray matter / General structure
opacity_fun_anatomy.AddPoint(p70, 0.005)  # White matter / Internal structure
opacity_fun_anatomy.AddPoint(p99, 0.05)  # Brightest parts

# 8 set up the camera
camera = vtk.vtkCamera()
camera.SetFocalPoint(100,100,100)
camera.SetPosition(-300, 250, 400)
camera.SetViewUp(0., 1., 0.)

# 9 create a renderer and set the color of the renderers background to black (0., 0., 0.)
renderer = vtk.vtkRenderer()
renderer.SetBackground(0.,0.,0.)
# 10 set the renderers camera as active
renderer.SetActiveCamera(camera)
# 11 add the volume actors to the renderer

strain_actor, strain_vol_mapper, strain_reader_src = volume_actor(sys.argv[1], color_fun_strain,
                                                                  opacity_fun_strain, smoothing_std = 1.0)
anatomy_actor, anatomy_vol_mapper, anatomy_reader_src = volume_actor(sys.argv[2], color_fun_anatomy,
                                                                     opacity_fun_anatomy, smoothing_std = 0)
renderer.AddActor(strain_actor)
renderer.AddActor(anatomy_actor)

# 12 create a render window
render_window=vtk.vtkRenderWindow()

# 13 add renderer to the render window
render_window.AddRenderer(renderer)
# 14 create an interactor
interactor = vtk.vtkRenderWindowInteractor()
# 15 connect interactor to the render window
render_window.SetInteractor(interactor)

interactor.Initialize()


plane = vtk.vtkPlane()
strain_vol_mapper.AddClippingPlane(plane)


plane_widget = vtk.vtkImplicitPlaneWidget()
plane_widget.SetInteractor(interactor)
plane_widget.SetInputConnection(strain_reader_src.GetOutputPort())

plane_widget.PlaceWidget()
plane_widget.AddObserver('InteractionEvent' , my_callback)

plane_widget.DrawPlaneOn() # Ensure the plane is visible
plane_widget.GetPlaneProperty().SetOpacity(0.2) # Make it faint so you can see through it
plane_widget.On() # This actually activates the widget in the scene

# 16 start displaying the render window
render_window.Render()

# 17 make the window interactive (start the interactor)
interactor.Start()
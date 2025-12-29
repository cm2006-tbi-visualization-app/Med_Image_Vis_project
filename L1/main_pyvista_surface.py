import vtk
import sys
import pyvista as pv

# get data path from the first argument
filename = sys.argv[1] 

# set up the source
reader_src = vtk.vtkNIFTIImageReader()
reader_src.SetFileName(filename)

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

# -- untill here, everything is identical to main_surface.py --

# force the vtk pipeline to load the data now
contour.Update()

# convert tp pyvista object
pyvista_mesh = pv.wrap(contour.GetOutput())

# plot
pyvista_mesh.plot()

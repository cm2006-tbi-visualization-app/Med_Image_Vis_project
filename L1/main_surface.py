import vtk
import sys


# 1 get data path from the first argument
filename = sys.argv[1] 

# 2 set up the source
reader_src = vtk.vtkNIFTIImageReader() #produces a vtkImageData - 3D voxel grid w scalar values
reader_src.SetFileName(filename)

# 3 (filter) 
cast_filter = vtk.vtkImageCast()#converts the scalar type from vtkImageData (e.g. float->short)
cast_filter.SetInputConnection(reader_src.GetOutputPort())
cast_filter.SetOutputScalarTypeToUnsignedShort()

# 4 marching cubes (mapper)
contour = vtk.vtkMarchingCubes() # vtkImageData converted into vtkPolyData(triangles)
contour.SetInputConnection(cast_filter.GetOutputPort())
contour.ComputeNormalsOn()
contour.ComputeGradientsOn()
contour.SetValue(0, 100)# threshold=100

con_mapper =vtk.vtkPolyDataMapper()#converts to GPU-friendly primitives and attr for rednering
con_mapper.SetInputConnection(contour.GetOutputPort())

# 5 set up the actor
actor = vtk.vtkActor()
actor.SetMapper(con_mapper)

# 6 set up the camera and the renderer
renderer = vtk.vtkRenderer()

camera = vtk.vtkCamera()
camera.SetViewUp(0., 1., 0.)
camera.SetPosition(-500, 100, 100)
camera.SetFocalPoint(100, 100, 100)

# 7 set the color of the renderers background to black (0., 0., 0.)
renderer.SetBackground(1., 0., 0.)

# 8 set the renderers camera as active
renderer.SetActiveCamera(camera)

# 9 add the volume actor to the renderer
renderer.AddActor(actor)

# 10 create a render window
ren_win = vtk.vtkRenderWindow()

# 11 add renderer to the render window
ren_win.AddRenderer(renderer)

# 12 create an interactor
iren = vtk.vtkRenderWindowInteractor()

# 13 connect interactor to the render window
iren.SetRenderWindow(ren_win)

# 14 start displaying the render window
ren_win.Render()

# 15 make the window interactive
iren.Start()


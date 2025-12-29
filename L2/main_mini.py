import vtk


# Create source
source = vtk.vtkSphereSource()
source.SetCenter(0, 0, 0)
source.SetRadius(5.0)

# Create a mapper
mapper = vtk.vtkPolyDataMapper()
mapper.SetInputConnection(source.GetOutputPort())

# Create an actor
actor = vtk.vtkActor()
actor.SetMapper(mapper)

# Setup Renderer and Render Window
ren = vtk.vtkRenderer()
ren.AddActor(actor)

iren = vtk.vtkRenderWindowInteractor()
renwin = vtk.vtkRenderWindow()
iren.SetRenderWindow(renwin)
renwin.AddRenderer(ren)

renwin.Render()
iren.Initialize()
iren.Start()


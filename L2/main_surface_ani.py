import vtk
import sys



# 2) create a new class: TimerCallback

class TimerCallback:

    def __init__(self, act):
        self.actor = act
        self.timer_count = 0

    def get_angle(self):
        angle = self.timer_count % 360
        return angle

    def execute(self, obj, event):
        angle = self.get_angle()
        self.actor.SetOrientation(0,0,angle)

        obj.GetRenderWindow().Render()  #enforces an update of our render window
        self.timer_count += 1




# get data path from the first argument
filename = sys.argv[1] 

# set up the source
reader_src = vtk.vtkNIFTIImageReader()
reader_src.SetFileName(filename)

# set the origin of the data to its center 
reader_src.Update()
data = reader_src.GetOutput()
center = data.GetCenter()
data.SetOrigin(- center[0], - center[0], - center[0])

# marching cubes (mapper)
contour = vtk.vtkMarchingCubes()
contour.SetInputData(data) # note that we directly provide the data
# contour.SetInputConnection(cast_filter.GetOutputPort())
contour.ComputeNormalsOn()
contour.ComputeGradientsOn()
contour.SetValue(0, 100)

con_mapper =vtk.vtkPolyDataMapper()
con_mapper.SetInputConnection(contour.GetOutputPort())

# set up the actor
actor = vtk.vtkActor()
actor.SetMapper(con_mapper)

# set up the camera and the renderer
renderer = vtk.vtkRenderer()
camera = vtk.vtkCamera()
camera.SetPosition(0, 0, 500)

# set the color of the renderers background to black (0., 0., 0.)
renderer.SetBackground(0., 0., 0.)

# set the renderers canera as active
renderer.SetActiveCamera(camera)
renderer.AddActor(actor)

ren_win = vtk.vtkRenderWindow()
ren_win.AddRenderer(renderer)

# create an interactor
iren = vtk.vtkRenderWindowInteractor()

# connect interactor to the render window
iren.SetRenderWindow(ren_win)

#  start displaying the render window
ren_win.Render()

# 3) [!] animation

iren.Initialize() # need to initialize our interactor before we can add things

timer_callback = TimerCallback(actor)
iren.AddObserver('TimerEvent', timer_callback.execute)
iren.CreateRepeatingTimer(10)


# make the window interactive
iren.Start()


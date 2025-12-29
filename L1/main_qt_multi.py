import sys
import vtk

from PyQt5 import Qt, QtCore, QtGui
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor


from renderers.Volume import VolumeRenderer
from renderers.VolumePV import VolumeRendererPV
from renderers.SurfacePV import SurfaceRendererPV

# here, we import our own modules
from renderers.Surface import SurfaceRenderer
# 6 import also the volume renderer


def idx_from_shape(shape_):
    assert len(shape_) == 2
    retlist = list()
    for i_ in range(shape_[0]):
        for j_ in range(shape_[1]):
            retlist.append((i_, j_))

    return retlist


class MainWindow(Qt.QMainWindow):

    def __init__(self, render_list, shape, frame, parent = None):
        # check if render_list and mayout match
        assert len(render_list) == shape[0] * shape[1]
        
        Qt.QMainWindow.__init__(self, parent)

        self.vl = Qt.QVBoxLayout()
        self.horizontalGroupBox = Qt.QGroupBox("LabisLab")
        self.vl.addWidget(self.horizontalGroupBox)
        self.layout = Qt.QGridLayout()
        self.frame = frame
        self.render = render_list
        self.vtk_widgets = [ren_.interactor for ren_ in self.render]
        self.layout_grid = idx_from_shape(shape)
        
        self.rens = list()
        self.irens = list()

        for idx, (wid_, grd_, ren_) in enumerate(zip(self.vtk_widgets,
            self.layout_grid, self.render)):
            self.layout.addWidget(wid_, grd_[0], grd_[1])

            self.rens.append(vtk.vtkRenderer()) 
            wid_.GetRenderWindow().AddRenderer(ren_.renderer)
            self.irens.append(wid_.GetRenderWindow().GetInteractor())

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

        self.horizontalGroupBox.setLayout(self.layout)
        self.frame.setLayout(self.vl)

        self.setCentralWidget(self.horizontalGroupBox)

        self.show()

        for iren_ in self.irens:
            iren_.Initialize()
            iren_.Start()


if __name__ == "__main__":
    # 1 read filenames
    filename = sys.argv[1]
    app = Qt.QApplication(sys.argv)
    frame = Qt.QFrame()

    render = list()
    
    # 2 create renderers and put them into a list
    render.append(SurfaceRenderer(filename, frame=frame))
    render.append(VolumeRenderer(filename, frame=frame))
    render.append(SurfaceRendererPV(filename, frame=frame))
    render.append(VolumeRendererPV(filename, frame=frame))

    # 3 define a layout
    layout = (2, 2)

    # 4 render the window
    window = MainWindow(render, layout, frame)
    app.exec_()

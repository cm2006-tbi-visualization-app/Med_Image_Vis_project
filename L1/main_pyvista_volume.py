import vtk
import sys
import pyvista as pv


# get data path from the first argument given
fname = sys.argv[1]

# set up the source
reader_src = vtk.vtkNIFTIImageReader()
reader_src.SetFileName(fname)

# force the pipeline to load
reader_src.Update()

# add pyvista plotter
pl = pv.Plotter()
# Wrap the raw VTK object into a Pyvista object
vol = pv.wrap(reader_src.GetOutput())
pl.add_volume(vol)
# plot
pl.show()

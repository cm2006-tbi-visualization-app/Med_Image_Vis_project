import heapq

import os
import glob

import vtk
import sys
import nibabel as nib
import numpy as np
import matplotlib.pyplot as plt
import nibabel as nib
import types
from PyQt5 import QtWidgets, uic, QtCore
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
global plane


class TBIvisualizer(QtWidgets.QDialog):

    def __init__(self, strain_path, anatomy_path, head_path):
        super().__init__()

        brain_data_path = anatomy_path
        img = nib.load(brain_data_path)
        self.data_all = img.get_fdata()
        print("Min:", np.min(self.data_all), "Max:", np.max(self.data_all))

        # Calculate the actual range and distribution
        self.data = self.data_all[self.data_all > 0]  # Ignore background noise for better statistics
        if len(self.data) == 0:
            self.data = self.data_all

        d_min = np.min(self.data_all)
        d_max = np.max(self.data_all)
        p5, p10, p20, p30, p50, p70, p90, p99 = np.percentile(self.data, [5, 10, 20, 30, 50, 70, 90, 99])
        self.data_stats = types.SimpleNamespace(
            d_min=d_min,
            d_max=d_max,
            p5=p5,
            p10=p10,
            p20=p20,
            p30=p30,
            p50=p50,
            p70=p70,
            p90=p90,
            p99=p99
        )
        img_strain = nib.load(strain_path)
        data_strain = img_strain.get_fdata()
        print("Min strain:", np.min(data_strain), "Max strain:", np.max(data_strain))
        self.risk = self.caculate_risk(data_strain)
        print("Risk of TBI:", self.risk)

        uic.loadUi("tbi_viewer.ui",self)
        self.opacity_slider.valueChanged.connect(self.update_anatomy_opacity)
        self.head_visible = True
        self.strip_button.clicked.connect(self.toggle_head)
        self.select_files_button.clicked.connect(self.show_select_window)

        self.animation_timer = QtCore.QTimer()
        self.animation_timer.timeout.connect(self.animate_stripping)
        self.current_head_opacity = 1.0

        self.setMinimumSize(1000, 800)
        # 1. Create the VTK Widget
        self.vtkWidget = QVTKRenderWindowInteractor(self.vtk_frame)

        # Add the VTK widget to the layout of your frame
        self.layout = QtWidgets.QVBoxLayout(self.vtk_frame)
        self.layout.addWidget(self.vtkWidget)


        # 8 set up the camera
        self.camera = vtk.vtkCamera()
        self.camera.SetFocalPoint(100,100,100)
        self.camera.SetPosition(-300, 250, 400)
        self.camera.SetViewUp(0., 1., 0.)

        # 9 create a renderer and set the color of the renderers background to black (0., 0., 0.)
        self.renderer = vtk.vtkRenderer()
        self.renderer.SetBackground(0.,0.,0.)
        # 10 set the renderers camera as active
        self.renderer.SetActiveCamera(self.camera)
        self.vtkWidget.GetRenderWindow().AddRenderer(self.renderer)

        self.interactor = self.vtkWidget.GetRenderWindow().GetInteractor()

        (self.color_fun_strain, self.opacity_fun_strain,
         self.color_fun_anatomy, self.opacity_fun_anatomy,
         self.color_fun_head, self.opacity_fun_head) = self.create_transfer_functions()

        self.strain_actor, self.strain_vol_mapper, self.strain_reader_src = self.volume_actor(strain_path, self.color_fun_strain, self.opacity_fun_strain, 1.0)
        self.anatomy_actor, self.anatomy_vol_mapper, self.anatomy_reader_src = self.volume_actor(anatomy_path, self.color_fun_anatomy, self.opacity_fun_anatomy, 0.0)
        self.head_actor, self.head_vol_mapper, self.head_reader_src = self.volume_actor(head_path, self.color_fun_head, self.opacity_fun_head, 1.0)

        self.renderer.AddActor(self.strain_actor)
        self.renderer.AddActor(self.anatomy_actor)
        self.renderer.AddActor(self.head_actor)

        self.plane = vtk.vtkPlane()
        self.strain_vol_mapper.AddClippingPlane(self.plane)

        self.add_scalar_bar()

        self.plane_widget = vtk.vtkImplicitPlaneWidget()
        self.plane_widget.SetInteractor(self.interactor)
        self.plane_widget.SetInputConnection(self.strain_reader_src.GetOutputPort())
        self.plane_widget.PlaceWidget()
        self.plane_widget.AddObserver('InteractionEvent' , self.my_callback)
        self.plane_widget.DrawPlaneOn() # Ensure the plane is visible
        self.plane_widget.GetPlaneProperty().SetOpacity(0.2) # Make it faint so you can see through it
        self.plane_widget.On() # This actually activates the widget in the scene


        cam = self.renderer.GetActiveCamera()
        cam.SetFocalPoint(100, 100, 100)
        cam.SetPosition(-300, 250, 400)

        self.vtkWidget.Initialize()
        self.vtkWidget.Start()

    def show_select_window(self):
        selector = FileSelector()
        # If we already have paths, allow them to close it (optional logic)
        if selector.exec_() == QtWidgets.QDialog.Accepted:
            new_paths = selector.paths
            # Logic to reload:
            self.reload_visualization(new_paths["strain"], new_paths["anatomy"], new_paths["head"])

    def reload_visualization(self, strain_p, anatomy_p, head_p):
        # Remove old actors
        self.renderer.RemoveAllViewProps()
        self.renderer.RemoveActor(self.strain_actor)
        self.renderer.RemoveActor(self.anatomy_actor)
        self.renderer.RemoveActor(self.head_actor)

        # Re-create actors with new paths
        self.strain_actor, self.strain_vol_mapper, self.strain_reader_src = self.volume_actor(strain_p, self.color_fun_strain, self.opacity_fun_strain, 1.0)
        self.anatomy_actor, self.anatomy_vol_mapper, self.anatomy_reader_src = self.volume_actor(anatomy_p, self.color_fun_anatomy, self.opacity_fun_anatomy, 0.0)

        self.renderer.AddActor(self.strain_actor)
        self.renderer.AddActor(self.anatomy_actor)

        if head_p:
            self.head_actor, self.head_vol_mapper, self.head_reader_src = self.volume_actor(head_p, self.color_fun_head, self.opacity_fun_head, 1.0)
            self.renderer.AddActor(self.head_actor)

        # Update the plane widget to the new data
        self.plane_widget.SetInputConnection(self.strain_reader_src.GetOutputPort())
        self.vtkWidget.GetRenderWindow().Render()

    def caculate_risk(self, m):
        print('max-mps: ',np.max(m))
        m_flat = m.flatten()
        largest_207 = heapq.nlargest(208, m_flat)
        print(largest_207[-1])
        beta0 = -5.502
        beta1 = 26.779
        m_95 = np.percentile(m, 95)
        print('95-mps: ', m_95)
        risk = 1 / (1 + np.exp(-1 * (beta0 + beta1 * m_95)))
        return risk

    def toggle_head(self):
        if self.head_visible:
            # Start stripping (disappearing)
            self.animation_timer.start(30)
            self.strip_button.setText("Show Head")
        else:
            # Instantly show or animate back
            self.current_head_opacity = 1.0
            self.show_head(1.0)
            self.strip_button.setText("Strip Head")

        self.head_visible = not self.head_visible

    def show_head(self, opacity_value):
        """Helper to set opacity back to the original high-quality settings"""
        # We use opacity_value (usually 1.0) to scale the whole function
        self.opacity_fun_head.RemoveAllPoints()

        # EXACT same points as your create_transfer_functions logic:
        self.opacity_fun_head.AddPoint(self.data_stats.d_min, 0.0)
        self.opacity_fun_head.AddPoint(self.data_stats.p5 - 0.1, 0.1 * opacity_value)
        self.opacity_fun_head.AddPoint(self.data_stats.p5, 0.4 * opacity_value)
        self.opacity_fun_head.AddPoint(self.data_stats.p5 + 2, 0.7 * opacity_value)
        self.opacity_fun_head.AddPoint(self.data_stats.p10, 0.85 * opacity_value)
        self.opacity_fun_head.AddPoint(self.data_stats.p30, 0.8 * opacity_value)
        self.opacity_fun_head.AddPoint(self.data_stats.p50, 0.8 * opacity_value)
        self.opacity_fun_head.AddPoint(self.data_stats.p70, 0.8 * opacity_value)
        self.opacity_fun_head.AddPoint(self.data_stats.p90, 0.8 * opacity_value)
        self.opacity_fun_head.AddPoint(self.data_stats.d_max, 0.8 * opacity_value)

        self.vtkWidget.GetRenderWindow().Render()

    def animate_stripping(self):
        # We still decrement linearly
        self.current_head_opacity -= 0.02

        if self.current_head_opacity <= 0:
            self.current_head_opacity = 0
            self.animation_timer.stop()

        # Easing: Squaring the value makes the initial drop (from 1.0)
        # feel more significant and the end (near 0.0) much smoother.
        eased_opacity = self.current_head_opacity ** 2

        self.opacity_fun_head.RemoveAllPoints()
        self.opacity_fun_head.AddPoint(self.data_stats.d_min, 0.0)
        self.opacity_fun_head.AddPoint(self.data_stats.p10 - 1, 0.0)
        self.opacity_fun_head.AddPoint(self.data_stats.p10, eased_opacity)
        self.opacity_fun_head.AddPoint(self.data_stats.p30, eased_opacity * 0.5)

        self.vtkWidget.GetRenderWindow().Render()

    def add_scalar_bar(self):
        scalar_bar = vtk.vtkScalarBarActor()
        scalar_bar.SetLookupTable(self.color_fun_strain) # Link to your strain colors
        scalar_bar.SetTitle("deformation")
        scalar_bar.SetNumberOfLabels(5)

        scalar_bar.UnconstrainedFontSizeOn()

        title_prop = scalar_bar.GetTitleTextProperty()
        title_prop.SetFontSize(24)             # Set specific size
        title_prop.SetFontFamilyToCourier()      # Font options: Arial, Courier, Times

        label_prop = scalar_bar.GetLabelTextProperty()
        label_prop.SetFontSize(18)             # Smaller than title
        label_prop.SetFontFamilyToCourier()

        scalar_bar.SetVerticalTitleSeparation(15)
        scalar_bar.SetLabelFormat("%.2f")
        # Position and size in the 3D window (percentage of screen)
        scalar_bar.SetWidth(0.1)
        scalar_bar.SetHeight(0.5)
        scalar_bar.GetPositionCoordinate().SetValue(0.85, 0.1) # Right side

        # Text color and style
        scalar_bar.GetTitleTextProperty().SetColor(1, 1, 1) # White
        scalar_bar.GetLabelTextProperty().SetColor(1, 1, 1)


        # --- NEW: Risk Text Actor ---
        risk_text = vtk.vtkTextActor()
        # Formatting to 2 decimal places or percentage
        risk_text.SetInput(f"Risk of TBI: {self.risk:.2%}")

        txt_prop = risk_text.GetTextProperty()
        txt_prop.SetFontSize(22)
        txt_prop.SetFontFamilyToCourier()
        txt_prop.BoldOn()
        txt_prop.SetColor(1, 1, 1) # White
        txt_prop.SetFrame(1)
        txt_prop.SetFrameColor(0.8, 0.8, 0.8) # Light Grey border
        txt_prop.SetJustificationToCentered()
        txt_prop.SetBackgroundColor(0.1, 0.1, 0.1)
        txt_prop.SetBackgroundOpacity(0.5)
        risk_text.GetPositionCoordinate().SetCoordinateSystemToNormalizedViewport()
        risk_text.GetPositionCoordinate().SetValue(0.84, 0.9)

        self.renderer.AddActor2D(risk_text)

        self.renderer.AddViewProp(scalar_bar)
    def update_anatomy_opacity(self, value):
        """
        Adjusts the brain anatomy opacity based on slider value (0-100).
        """
        # Convert slider 0-100 to a max opacity of 0.2 (20%)
        # because 1.0 (100%) would be a solid block hiding the strain.
        max_opacity = (value / 100.0) * 0.2

        # We only want to change the 'visible' points, not the 'air' points
        # Assuming p30 and p99 were calculated in create_transfer_functions
        # We clear the old points and add new ones
        self.opacity_fun_anatomy.RemoveAllPoints()
        self.opacity_fun_anatomy.AddPoint(self.data_stats.d_min, 0.0)
        self.opacity_fun_anatomy.AddPoint(self.data_stats.p10, 0.0)
        self.opacity_fun_anatomy.AddPoint(self.data_stats.p30, max_opacity * 0.1) # Faint interior
        self.opacity_fun_anatomy.AddPoint(self.data_stats.p99, max_opacity)       # Defined shell

        # Trigger a re-render
        self.vtkWidget.GetRenderWindow().Render()

    def my_callback(self, obj, event):
        global plane
        obj.GetPlane(self.plane)
        print(f"\nobject:{obj}")
        print(f"event:{event}\n")

    def volume_actor(self, file_path, color_function, opacity_function, smoothing_std = 0.0):
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
        volume_mapper.SetSampleDistance(0.5)

        volume_mapper.SetAutoAdjustSampleDistances(0) # Disable auto-adjustment to keep it crisp
        volume_mapper.SetUseJittering(1) # Keep this ON once distance is low



        # 6 set up the volume properties with linear interpolation
        vol_property = vtk.vtkVolumeProperty()
        vol_property.SetColor(color_function)
        vol_property.SetScalarOpacity(opacity_function)
        #vol_property.ShadeOn()
        vol_property.SetInterpolationTypeToLinear()
        #vol_property.SetDiffuse(0.6)
        #vol_property.SetAmbient(0.3)
        #vol_property.SetSpecular(0.2)
        #vol_property.SetSpecularPower(10.0)


        # 7 set up the actor and connect it to the mapper and the volume properties
        volume_actor = vtk.vtkVolume()
        volume_actor.SetMapper(volume_mapper)
        volume_actor.SetProperty(vol_property)

        return volume_actor, volume_mapper, reader_source

    def create_transfer_functions(self):

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

        color_fun_anatomy = vtk.vtkColorTransferFunction()
        color_fun_anatomy.SetColorSpaceToRGB()

        color_fun_anatomy.AddRGBPoint(self.data_stats.d_min, 0, 0, 0)        # Black (Background)
        color_fun_anatomy.AddRGBPoint(self.data_stats.p10, 0.2, 0, 0)        # Dark Red (Skin/Fat)
        color_fun_anatomy.AddRGBPoint(self.data_stats.p30, 0.8, 0.4, 0.3)    # Pinkish (Gray Matter)
        color_fun_anatomy.AddRGBPoint(self.data_stats.p70, 1.0, 0.9, 0.8)    # Off-white (White Matter)
        color_fun_anatomy.AddRGBPoint(self.data_stats.d_max, 0.9, 0.9, 1.0)  # Cool white (Highlights)

        opacity_fun_anatomy = vtk.vtkPiecewiseFunction()
        # Filter out EVERYTHING except the most distinct features
        opacity_fun_anatomy.AddPoint(self.data_stats.d_min, 0.0)
        opacity_fun_anatomy.AddPoint(self.data_stats.p10, 0.0)

        # p10 to p99: Make the bulk of the brain visible but translucent
        # Using 0.2 means it is 20% opaque (80% transparent)
        opacity_fun_anatomy.AddPoint(self.data_stats.p30, 0.005)  # Gray matter / General structure
        opacity_fun_anatomy.AddPoint(self.data_stats.p70, 0.005)  # White matter / Internal structure
        opacity_fun_anatomy.AddPoint(self.data_stats.p99, 0.05)  # Brightest parts

        # --- 6. Head/Skin Color Transfer Function ---
        color_fun_head = vtk.vtkColorTransferFunction()
        color_fun_head.SetColorSpaceToRGB()
        # Natural skin tones progression
        color_fun_head.AddRGBPoint(self.data_stats.d_min, 0.0, 0.0, 0.0)      # Black background
        color_fun_head.AddRGBPoint(self.data_stats.p5, 0.4, 0.25, 0.2)        # Dark tissue
        color_fun_head.AddRGBPoint(self.data_stats.p10, 0.85, 0.65, 0.55)     # SKIN COLOR (peachy/tan)
        color_fun_head.AddRGBPoint(self.data_stats.p30, 0.9, 0.7, 0.6)        # Lighter skin/muscle
        color_fun_head.AddRGBPoint(self.data_stats.p70, 0.95, 0.95, 0.92)     # OFF-WHITE (bone)
        color_fun_head.AddRGBPoint(self.data_stats.d_max, 1.0, 1.0, 1.0)      # Pure white (bright bone)

        # --- 7. Head/Skin Opacity Transfer Function ---
        opacity_fun_head = vtk.vtkPiecewiseFunction()
        opacity_fun_head.AddPoint(self.data_stats.d_min, 0.0)
        opacity_fun_head.AddPoint(self.data_stats.p5 - 0.1, 0.1)
        opacity_fun_head.AddPoint(self.data_stats.p5, 0.4)        # Gentle start
        opacity_fun_head.AddPoint(self.data_stats.p5 + 2, 0.7)
        opacity_fun_head.AddPoint(self.data_stats.p10, 0.85)      # SOLID at skin surface
        opacity_fun_head.AddPoint(self.data_stats.p30, 0.8)       # Stay fairly solid
        opacity_fun_head.AddPoint(self.data_stats.p50, 0.8)       # Start becoming transparent
        opacity_fun_head.AddPoint(self.data_stats.p70, 0.8)       # More transparent (see brain)
        opacity_fun_head.AddPoint(self.data_stats.p90, 0.8)       # Bone becomes visible again
        opacity_fun_head.AddPoint(self.data_stats.d_max, 0.8)     # Bright bone solid

        return color_fun_strain, opacity_fun_strain, color_fun_anatomy, opacity_fun_anatomy, color_fun_head, opacity_fun_head

class FileSelector(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Select Brain Data Files")
        self.setFixedSize(400, 200)

        layout = QtWidgets.QVBoxLayout(self)

        self.btn_strain = QtWidgets.QPushButton("Select Strain File")
        self.btn_anatomy = QtWidgets.QPushButton("Select Anatomy File")
        self.btn_head = QtWidgets.QPushButton("Select Head File (Optional)")
        self.btn_visualize = QtWidgets.QPushButton("VISUALIZE")
        self.btn_visualize.setStyleSheet("background-color: lightgreen; font-weight: bold;")

        layout.addWidget(self.btn_strain)
        layout.addWidget(self.btn_anatomy)
        layout.addWidget(self.btn_head)
        layout.addWidget(self.btn_visualize)

        self.paths = {"strain": None, "anatomy": None, "head": None}

        # Map internal keys to the buttons for easy updating
        self.buttons = {
            "strain": self.btn_strain,
            "anatomy": self.btn_anatomy,
            "head": self.btn_head
        }

        self.btn_strain.clicked.connect(lambda: self.get_file("strain"))
        self.btn_anatomy.clicked.connect(lambda: self.get_file("anatomy"))
        self.btn_head.clicked.connect(lambda: self.get_file("head"))
        self.btn_visualize.clicked.connect(self.validate_and_accept)

        # Automatically try to find files in the current folder
        self.auto_fill_paths()

    def auto_fill_paths(self):
        """Looks for files starting with 'head', 'strain', and 'anatomy' in CWD."""
        cwd = os.getcwd()
        # NIfTI extensions to check
        extensions = ["*.nii", "*.nii.gz"]

        for key in self.paths.keys():
            matches = []
            for ext in extensions:
                # Case-insensitive search for files starting with the key
                pattern = os.path.join(cwd, f"{key}*{ext}")
                matches.extend(glob.glob(pattern))

            # Logic: ONLY auto-select if exactly one unique file matches
            if len(matches) == 1:
                file_path = matches[0]
                self.paths[key] = file_path
                self.buttons[key].setText(f"{key.capitalize()} (found)")
                self.buttons[key].setStyleSheet("color: green; font-style: bold;")

    def get_file(self, key):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, f"Select {key}", "", "NIfTI files (*.nii.gz *.nii)")
        if path:
            self.paths[key] = path
            self.buttons[key].setText(f"{key.capitalize()} Selected")
            self.buttons[key].setStyleSheet("") # Reset style if manually chosen

    def validate_and_accept(self):
        # Allow proceeding if Strain and Anatomy are found (keeping Head as optional if desired)
        if self.paths["strain"] and self.paths["anatomy"]:
            self.accept()
        else:
            QtWidgets.QMessageBox.warning(self, "Missing Files", "Please select at least Strain and Anatomy files.")

if __name__ == "__main__":

    app = QtWidgets.QApplication(sys.argv)
    selector = FileSelector()
    if selector.exec_() == QtWidgets.QDialog.Accepted:
        # 2. Only if files are chosen, open the visualizer
        p = selector.paths
        window = TBIvisualizer(p["strain"], p["anatomy"], p["head"])
        window.show()
        sys.exit(app.exec_())
    else:
        sys.exit()
    '''
    if len(sys.argv) < 3:
        print("Usage: python main.py strain.nii.gz anatomy.nii.gz head.nii.gz(optional)")
        sys.exit()
    strain_path = sys.argv[1]
    anatomy_path = sys.argv[2]

    if len(sys.argv) == 4:
        head_path = sys.argv[3]
    else:
        head_path = None


    window = TBIvisualizer(strain_path, anatomy_path, head_path)

    window.show()
    sys.exit(app.exec_())
    '''
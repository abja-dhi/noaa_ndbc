from .utils import utils, Structure
from .plotter import Plotter
import pandas as pd
import numpy as np
from scipy.interpolate import griddata, RegularGridInterpolator
from scipy.ndimage import gaussian_filter
from shapely.geometry import Polygon, Point
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import os

class ScourScatter:
    def __init__(self, experiment, apply_filter=False, structure="auto", rotate=None, rotate_X_start=None, rotate_X_end=None, rotate_y=None) -> None:
        self.experiment = experiment
        if structure == "auto":
            self.structure, _, _ = utils.get_experiment_info(experiment)
        elif os.path.exists(structure):
            self._process_structure(structure)
        else:
            raise ValueError("Invalid structure input! structure should be set to 'auto' or a valid path to a structure file.")

        self.corners = [self.structure.p1.to_list(), self.structure.p2.to_list(), self.structure.p3.to_list(), self.structure.p4.to_list()]
        self.center = [np.mean([c[0] for c in self.corners]), np.mean([c[1] for c in self.corners])]
        self.corners = [[x + 23.9, y + 1.5] for x, y in self.corners]
        self.center = [self.center[0] + 23.9, self.center[1] + 1.5]
        self.polygon = Polygon(self.corners)
        self.data = pd.read_csv(experiment.scour_path)
        self.data.loc[:, "Z"] = self.data.loc[:, "Z"] * 100
        self._cleaner(rotate=rotate, rotate_X_start=rotate_X_start, rotate_X_end=rotate_X_end, rotate_y=rotate_y)
        if apply_filter:
            self.noise_filter()
    
    def _cleaner(self, rotate=None, rotate_X_start=None, rotate_X_end=None, rotate_y=None):
        mask = (self.data["X"] > 0) & (self.data["Y"] < 0) & (self.data["X"] < 3.3) & (self.data["Y"] > -1.4) & (self.data["Y"] < -0.1) & (self.data["Z"] < 0.1)
        self.data = self.data[mask]
        x = self.data["X"] + 23.9
        y = self.data["Y"] + 1.5
        z = self.data["Z"]

        X = np.linspace(x.min(), x.max(), 1000)
        Y = np.linspace(y.min(), y.max(), 500)
        self.X, self.Y = np.meshgrid(X, Y)
        self.X = self.X 
        self.Y = self.Y 
        
        self.Z = griddata((x, y), z, (self.X, self.Y), method='linear')
        if rotate is not None:
            if isinstance(rotate, str):
                rotate = [rotate]
                rotate_X_start = [rotate_X_start]
                rotate_X_end = [rotate_X_end]
                rotate_y = [rotate_y]
            for rotate, rotate_X_start, rotate_X_end, rotate_y in zip(rotate, rotate_X_start, rotate_X_end, rotate_y):
                upperblock = (self.X >= rotate_X_start) & (self.X <= rotate_X_end) & (self.Y >= self.center[1]) & (self.Y - self.center[1] <= rotate_y)
                upperblock_first_row = np.where(upperblock)[0][0]
                upperblock_last_row = np.where(upperblock)[0][-1]
                first_column = np.where(upperblock)[1][0]
                last_column = np.where(upperblock)[1][-1]
                lowerblock = (self.X >= rotate_X_start) & (self.X <= rotate_X_end) & (self.Y < self.center[1]) & (self.center[1] - self.Y <= rotate_y)
                lowerblock_first_row = np.where(lowerblock)[0][0]
                lowerblock_last_row = np.where(lowerblock)[0][-1]
                Z_copy = self.Z.copy()
                if rotate == "top2bottom":
                    Z_copy[lowerblock_first_row:lowerblock_last_row, first_column:last_column] = self.Z[upperblock_last_row:upperblock_first_row:-1, first_column:last_column]
                elif rotate == "bottom2top":
                    Z_copy[upperblock_first_row:upperblock_last_row, first_column:last_column] = self.Z[lowerblock_last_row:lowerblock_first_row:-1, first_column:last_column]
                self.Z = Z_copy

    def _process_structure(self, structure):
        df = pd.read_csv(structure, index_col=0)
        self.structure = Structure(df)

    def noise_filter(self, sigma=5):
        self.Z = gaussian_filter(self.Z, sigma=sigma)
    
    def get_scour_depth(self, x, y, inst=None, new_file=False):
        interpolator = RegularGridInterpolator((self.X[0, :], self.Y[:, 0]), self.Z.transpose(), method="linear")
        mode = "w" if new_file else "a"
        if inst is not None:
            with open(f"{self.experiment.path}/Scour Depth/Final Scour.csv", mode) as f:
                f.write(f"{inst},{interpolator((x, y))}\n")
        return interpolator((x, y))

    def plot(self, add_description=True, add_structure=True, **kwargs):
        levels = kwargs.get("levels", np.linspace(-15, 2, 100))
        cticks = kwargs.get("cticks", np.linspace(-15, 2, 18))
        xlim = kwargs.get("xlim", [24.1, 27])
        ylim = kwargs.get("ylim", [0.2, 1.3])
        cmap = kwargs.get("cmap", "turbo")
        x_description = kwargs.get("x_description", 0.82)
        y_description = kwargs.get("y_description", 0.92)
        
        if add_structure:
            mask = np.array([self.polygon.contains(Point(x, y)) for x, y in zip(self.X.flatten(), self.Y.flatten())])
            mask = mask.reshape(self.X.shape)
            self.Z[mask] = np.nan
            
        self.plt = Plotter(figwidth=10, figheight=5)
        self.plt.contour(self.X, self.Y, self.Z, clabel="Elevation [cm]", xlim=xlim, ylim=ylim, cmap=cmap, levels=levels, cticks=cticks)
        if add_structure:
            self.plt.ax[0].add_patch(plt.Polygon(self.corners, closed=True, facecolor='gray', alpha=0.5))
        self.plt.set_prop(title=self.experiment.test_name, xlabel="X [m]", ylabel="Y [m]", grid=False)
        if add_description:
            self.plt.add_description(self.experiment.test_name, x_description=x_description, y_description=y_description, facecolor="none")
        return self
    
    def show(self):
        self.plt.show()

    def save(self, path="Plots/Scour Profile.jpg"):
        self.plt.save(path, dpi=600, bbox_inches="tight")
        
class DraggableRectangle:
    def __init__(self, ax, rect):
        self.ax = ax
        self.rect = rect
        self.press = None
        self.background = None
        self.cidpress = rect.figure.canvas.mpl_connect('button_press_event', self.on_press)
        self.cidrelease = rect.figure.canvas.mpl_connect('button_release_event', self.on_release)
        self.cidmotion = rect.figure.canvas.mpl_connect('motion_notify_event', self.on_motion)

    def on_press(self, event):
        if event.inaxes != self.rect.axes:
            return
        contains, attr = self.rect.contains(event)
        if not contains:
            return
        x0, y0 = self.rect.xy
        self.press = x0, y0, event.xdata, event.ydata
        
        # Save the background
        self.background = self.rect.figure.canvas.copy_from_bbox(self.ax.bbox)

    def on_release(self, event):
        self.press = None
        self.rect.figure.canvas.draw()
        
    def on_motion(self, event):
        if self.press is None:
            return
        if event.inaxes != self.rect.axes:
            return
        x0, y0, xpress, ypress = self.press
        dx = event.xdata - xpress
        dy = event.ydata - ypress
        
        # Update the rectangle's position
        self.rect.set_xy((x0 + dx, y0 + dy))
        
        # Restore the background
        self.rect.figure.canvas.restore_region(self.background)
        
        # Redraw the rectangle
        self.ax.draw_artist(self.rect)
        
        # Blit the canvas
        self.rect.figure.canvas.blit(self.ax.bbox)

class ScourScatterCheck:
    def __init__(self, experiment) -> None:
        self.experiment = experiment
        self.structure, _, _ = utils.get_experiment_info(experiment)
        self.data = pd.read_csv(experiment.scour_path)
        self.data.loc[:, "Z"] = self.data.loc[:, "Z"] * 100
        self._cleaner()
        
        
    @staticmethod
    def calculate_corners(rect):
        x, y = rect.xy
        width, height = rect.get_width(), rect.get_height()
        angle = np.deg2rad(rect.angle)
        
        corners = np.array([
            [x, y],
            [x + width * np.cos(angle), y + width * np.sin(angle)],
            [x + width * np.cos(angle) - height * np.sin(angle), y + width * np.sin(angle) + height * np.cos(angle)],
            [x - height * np.sin(angle), y + height * np.cos(angle)]
        ])
        return corners

    def _cleaner(self):
        mask = (self.data["X"] > 0) & (self.data["Y"] < 0) & (self.data["X"] < 3.3) & (self.data["Y"] > -1.4) & (self.data["Y"] < -0.1) & (self.data["Z"] < 0.1)
        self.data = self.data[mask]
        x = self.data["X"]
        y = self.data["Y"]
        z = self.data["Z"]

        X = np.linspace(x.min(), x.max(), 1000)
        Y = np.linspace(y.min(), y.max(), 500)
        self.X, self.Y = np.meshgrid(X, Y)
        self.Z = griddata((x, y), z, (self.X, self.Y), method='linear')

    def _process_structure(self, corners):
        ids = ["Upstream-lower", "Downstream-lower", "Downstream-upper", "Upstream-upper"]
        X = [corner[0] for corner in corners]
        Y = [corner[1] for corner in corners]
        df = pd.DataFrame({"X": X, "Y": Y}, index=ids)
        df.to_csv("LiDAR/Structure.csv")
        
    def plot(self, angle=45, **kwargs):
        xlim = kwargs.get("xlim", None)
        ylim = kwargs.get("ylim", None)
        cmap = kwargs.get("cmap", "turbo")
        self.plt = Plotter(figwidth=10, figheight=5)
        self.ax = self.plt.ax[0]
        self.ax.contourf(self.X, self.Y, self.Z, cmap="turbo", levels=np.linspace(-15, 2, 100), cticks=np.linspace(-15, 2, 18), extend='both')
        self.rectangle = patches.Rectangle((1, -1), self.structure.width, self.structure.length, angle=angle, fill=False, color='blue', alpha=0.5)
        self.ax.add_patch(self.rectangle)
        dr = DraggableRectangle(self.ax, self.rectangle)
        plt.show()
        corners = self.calculate_corners(self.rectangle)
        self._process_structure(corners)
        

from .utils import utils
from .plotter import Plotter
import pandas as pd
import numpy as np
from scipy.interpolate import griddata
from scipy.ndimage import gaussian_filter
from shapely.geometry import Polygon, Point
import matplotlib.pyplot as plt

class ScourScatter:
    def __init__(self, experiment, apply_filter=False) -> None:
        self.experiment = experiment
        self.structure, _, _ = utils.get_experiment_info(experiment)
        self.corners = [self.structure.p1, self.structure.p2, self.structure.p3, self.structure.p4]
        self.polygon = Polygon(self.corners)
        self.data = pd.read_csv("LiDAR/Point Cloud.txt")
        self.data.loc[:, "Z"] = self.data.loc[:, "Z"] * 100
        self._cleaner()
        if apply_filter:
            self.noise_filter()
        
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

    def noise_filter(self, sigma=5):
        self.Z = gaussian_filter(self.Z, sigma=sigma)

    def plot(self, add_description=True, add_structure=True, **kwargs):
        levels = kwargs.get("levels", np.linspace(-15, 2, 100))
        cticks = kwargs.get("cticks", np.linspace(-15, 2, 18))
        xlim = kwargs.get("xlim", [24.1, 27])
        ylim = kwargs.get("ylim", [0.2, 1.3])
        cmap = kwargs.get("cmap", "turbo")
        if add_structure:
            mask = np.array([self.polygon.contains(Point(x, y)) for x, y in zip(self.X.flatten(), self.Y.flatten())])
            mask = mask.reshape(self.X.shape)
            self.Z[mask] = np.nan
        self.X = self.X + 23.9
        self.Y = self.Y + 1.5
        self.corners = [[x + 23.9, y + 1.5] for x, y in self.corners]
        self.plt = Plotter(figwidth=10, figheight=5)
        self.plt.contour(self.X, self.Y, self.Z, clabel="Elevation [cm]", xlim=xlim, ylim=ylim, cmap=cmap, levels=levels, cticks=cticks)
        if add_structure:
            self.plt.ax[0].add_patch(plt.Polygon(self.corners, closed=True, facecolor='gray', alpha=0.5))
        self.plt.set_prop(title=self.experiment.test_name, xlabel="X [m]", ylabel="Y [m]", grid=False)
        if add_description:
            self.plt.add_description(self.experiment.test_name, x_description=0.82, y_description=0.92, facecolor="none")
        return self
    
    def show(self):
        self.plt.show()

    def save(self, path="Plots/Scour Profile.jpg"):
        self.plt.save(path, dpi=600, bbox_inches="tight")
        
    

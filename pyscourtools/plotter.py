import numpy as np
import pandas as pd
from pyplume.plotting.matplotlib_shell import subplots
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import os
from matplotlib.widgets import LassoSelector
from matplotlib.path import Path
from .utils import utils

class Specifications:
    def __init__(self):
        self.colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"]
        self.linestyles = ["-", "--", "-.", ":"]
        self.color_idx = 0
        self.linestyle_idx = 0

    def get_color(self):
        color = self.colors[self.color_idx]
        self.color_idx += 1
        if self.color_idx == len(self.colors):
            self.color_idx = 0
        return color
    
    def get_linestyle(self):
        linestyle = self.linestyles[self.linestyle_idx]
        self.linestyle_idx += 1
        if self.linestyle_idx == len(self.linestyles):
            self.linestyle_idx = 0
        return linestyle

class Plotter:
    dictionary = {"SC": "Single Column",
                   "SW": "Short Wall",
                   "MW": "Medium Wall",
                   "LW": "Long Wall",
                   "H1": "70 cm",
                   "H2": "60 cm",
                   "H3": "50 cm",
                   "A0": "Angle N/A",
                   "A1": "0 degrees",
                   "A2": "45 degrees",
                   "A3": "90 degrees",
                   "R": "Repeated"
                   }
    
    def __init__(self, fig=None, ax=None, nrow=1, ncol=1, **kwargs):
        if fig is None and ax is None:
            self.fig, self.ax = subplots(nrow=nrow, ncol=ncol, **kwargs)
            if nrow == 1 and ncol == 1:
                self.ax = np.array([self.ax])
        else:
            self.fig = fig
            self.ax = ax
        
    def plot(self, x, y, ax_number=0, **kwargs):
        color = kwargs.pop('color', None)
        linestyle = kwargs.pop('linestyle', '-')
        marker = kwargs.pop('marker', False)
        label = kwargs.pop('label', 'Data')
        alpha = kwargs.pop('alpha', 0.7)
        marker = None if not marker else "o"
        
        self.ax[ax_number].plot(x, y, color=color, linestyle=linestyle, marker=marker, label=label, alpha=alpha)
        return self.fig, self.ax

    def add_description(self, test_names, x_description=0.8, y_description=0.7, ax_number=0, **kwargs):
        facecolor = kwargs.pop('facecolor', 'white')
        items = self._get_description(test_names)
        self.ax[ax_number].text(x_description, y_description, items, transform=self.ax[ax_number].transAxes, ha="left", va="top", bbox=dict(facecolor=facecolor, edgecolor='black', boxstyle='round'))

    def _get_description(self, test_names):
        items = ["Test Name Definitions"]
        if isinstance(test_names, str):
            test_names = [test_names]
        for test_name in test_names:
            part = test_name.split('-')[0]
            item = "  - " + part + ": " + self.dictionary[part]
            if item not in items: items.append(item)
        for test_name in test_names:
            part = test_name.split('-')[1]
            item = "  - " + part + ": " + self.dictionary[part]
            if item not in items: items.append(item)
        for test_name in test_names:
            part = test_name.split('-')[2]
            item = "  - " + part + ": " + self.dictionary[part]
            if item not in items: items.append(item)
        for test_name in test_names:
            part = test_name.split('-')
            if len(part) == 4:
                part = part[3]
                item = "  - " + part + ": " + self.dictionary[part]
                if item not in items: items.append(item)
        return "\n".join(items)

    def set_prop(self, ax_number=0, **kwargs):
        title = kwargs.pop('title', 'Plot')
        xlabel = kwargs.pop('xlabel', 'X')
        ylabel = kwargs.pop('ylabel', 'Y')
        legend = kwargs.pop('legend', False)
        grid = kwargs.pop('grid', True)
        xlim = kwargs.pop('xlim', None)
        ylim = kwargs.pop('ylim', None)
        xticks = kwargs.pop('xticks', None)
        yticks = kwargs.pop('yticks', None)
        self.ax[ax_number].set_title(title)
        self.ax[ax_number].set_xlabel(xlabel)
        self.ax[ax_number].set_ylabel(ylabel)
        if xlim:
            self.ax[ax_number].set_xlim(xlim)
        if ylim:
            self.ax[ax_number].set_ylim(ylim)
        if xticks:
            self.ax[ax_number].set_xticks(xticks)
        if yticks:
            self.ax[ax_number].set_yticks(yticks)
        if grid:
            self.ax[ax_number].grid()
        if legend:
            self.ax[ax_number].legend()

    def show(self):
        plt.show()

    def save(self, path, **kwargs):
        dpi = kwargs.pop('dpi', 600)
        bbox_inches = kwargs.pop('bbox_inches', 'tight')
        directory = os.path.dirname(path)
        if not os.path.exists(directory) and directory != "":
            os.makedirs(directory)
        plt.savefig(path, dpi=dpi, bbox_inches=bbox_inches)

    def contour(self, x, y, z, ax_number=0, add_colorbar=True, **kwargs):
        cticks = kwargs.pop('cticks', None)
        levels = kwargs.pop('levels', 100)
        xlim = kwargs.pop('xlim', None)
        ylim = kwargs.pop('ylim', None)
        aspect = kwargs.pop('aspect', 'equal')
        clabel = kwargs.pop('clabel', 'Elevation [cm]')
        cmap = kwargs.pop('cmap', 'turbo')
        self.ax[ax_number].contourf(x, y, z, levels=levels, cmap=cmap, extend='both')
        self.ax[ax_number].set_aspect(aspect)
        self.ax[ax_number].set_xlim(xlim)
        self.ax[ax_number].set_ylim(ylim)
        if add_colorbar:
            cbar = self.fig.colorbar(self.ax[ax_number].collections[0], ax=self.ax[ax_number], orientation='vertical')
            cbar.set_label(clabel)
            if cticks is not None:
                cbar.set_ticks(cticks)
        return self.fig, self.ax

class ScourPlotter:
    def __init__(self, experiment, fig=None, ax=None, **kwargs):
        if fig is None or ax is None:
            self.fig = plt.figure()
            self.ax1 = self.fig.add_subplot(121, projection='3d')
            self.ax2 = self.fig.add_subplot(122, projection='3d')
            self.axs = [self.ax1, self.ax2]
        else:
            self.fig = fig
            self.ax1, self.ax2 = ax
        self.test_name = experiment.test_name
        self._get_info()
        self._initialize(ax=self.ax1, angle=-135)
        self._initialize(ax=self.ax2, angle=-45)
        

    def _get_info(self):
        structure = self.test_name.split('-')[0]
        if structure == "SC":
            self.width = 10
        elif structure == "SW":
            self.width = 30
        elif structure == "LW":
            self.width = 50
        else:
            raise ValueError("Invalid structure type. Choose from 'SC', 'SW', 'LW'.")
        self.length = 10
        self.height = 40
        
    def _initialize(self, ax, angle):
        ax.grid(False)
        ax.plot([0, self.width], [0, 0], [0, 0], color='black')
        ax.plot([0, self.width], [0, 0], [self.height, self.height], color='black')
        ax.plot([self.width, self.width], [0, self.length], [0, 0], color='black')
        ax.plot([self.width, self.width], [0, self.length], [self.height, self.height], color='black')
        ax.plot([0, 0], [0, 0], [0, self.height], color='black')
        ax.plot([self.width, self.width], [0, 0], [0, self.height], color='black')
        ax.plot([self.width, self.width], [self.length, self.length], [0, self.height], color='black')
        ax.plot([0, 0], [self.length, self.length], [0, self.height], color='black')
        ax.plot([0, self.width], [self.length, self.length], [0, 0], color='black')
        ax.plot([0, self.width], [self.length, self.length], [self.height, self.height], color='black')
        ax.plot([0, 0], [0, self.length], [0, 0], color='black')
        ax.plot([0, 0], [0, self.length], [self.height, self.height], color='black')
        ax.view_init(azim=angle)
        ax.set_xlim([0, self.width])
        ax.set_ylim([0, self.length])
        ax.set_zlim([0, self.height])
        ax.set_facecolor('white')
        ax.set_aspect('equal')
        # ax.set_xlabel('Y (cm)')
        # ax.set_ylabel('X (cm)')
        # ax.set_axis_off()
        self.fig.suptitle(self.test_name, fontweight='bold', fontsize=15)

    def plot(self, fname="Scour Depth/Scour Depth.csv", **kwargs):
        df = pd.read_csv(fname)
        time = df['Time']
        X = df['X']
        Y = df['Y']
        Z = df['Z']
        if Z.iloc[0] != 25:
            Z = Z - (Z.iloc[0] - 25)
        for t in time.unique():
            idx = time == t
            x = X[idx]
            y = Y[idx]
            z = Z[idx]
            closest_idx = np.abs(x - self.width/2).argmin()
            for ax in self.axs:
                ax.plot(x, y, z, linewidth=0.5)
                ax.text(self.width/2, 0, z.iloc[closest_idx], str(t), fontsize=10, color='black', ha='center', va='center')

    def show(self):
        plt.show()

    def save(self):
        self.fig.savefig("Plots/Scour Depth.jpg", dpi=600, bbox_inches='tight')


        
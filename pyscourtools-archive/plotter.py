import numpy as np
import pandas as pd
from pyplume.plotting.matplotlib_shell import subplots
import matplotlib.pyplot as plt
from matplotlib.axes import Axes

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
                   "T0": "Angle N/A",
                   "T1": "0 degrees",
                   "T2": "45 degrees",
                   "T3": "90 degrees",
                   "R": "Repeated"
                   }
    
    def __init__(self, nrow=1, ncol=1, **kwargs):
        self.fig, self.ax = subplots(nrow=nrow, ncol=ncol, **kwargs)
        if nrow == 1 and ncol == 1:
            self.ax = np.array([self.ax])
        
    def plot(self, x, y, ax_number=0, **kwargs):
        color = kwargs.pop('color', None)
        linestyle = kwargs.pop('linestyle', '-')
        marker = kwargs.pop('marker', False)
        label = kwargs.pop('label', 'Data')
        marker = None if not marker else "o"
        
        self.ax[ax_number].plot(x, y, color=color, linestyle=linestyle, marker=marker, label=label)

    def add_description(self, test_names, x_description=0.8, y_description=0.7, ax_number=0):
        items = self._get_description(test_names)
        self.ax[ax_number].text(x_description, y_description, items, transform=self.ax[ax_number].transAxes, ha="left", va="top", bbox=dict(facecolor='white', edgecolor='black', boxstyle='round'))

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
        
        plt.savefig(path, dpi=dpi, bbox_inches=bbox_inches)
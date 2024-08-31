import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

class Plotter:
    def __init__(self):
        pass

    def plot(self, x, y, **kwargs):
        fig = kwargs.pop('fig', None)
        ax1 = kwargs.pop('ax', None)
        if ax1 is None:
            title = kwargs.pop('title', 'Plot')
            xlabel = kwargs.pop('xlabel', 'X')
            ylabel = kwargs.pop('ylabel', 'Y')
            legend = kwargs.pop('legend', False)
            grid = kwargs.pop('grid', True)
            xlim = kwargs.pop('xlim', None)
            ylim = kwargs.pop('ylim', None)
            xticks = kwargs.pop('xticks', None)
            yticks = kwargs.pop('yticks', None)
            
            
        color = kwargs.pop('color', 'blue')
        linestyle = kwargs.pop('linestyle', '-')
        marker = kwargs.pop('marker', False)
        label = kwargs.pop('label', 'Data')
        show = kwargs.pop('show', True)
        figsize = kwargs.pop('figsize', (10, 6))
        save = kwargs.pop('save', False)
        save_path = kwargs.pop('save_path', 'plot.png')
        dpi = kwargs.pop('dpi', 600)
        
        if fig is None and ax1 is None:
            fig, ax = plt.subplots(figsize=figsize)
        else:
            ax = ax1
        
        bbox_inches = kwargs.pop('bbox_inches', 'tight')
        marker = None if not marker else "o"
        
        
        ax.plot(x, y, color=color, linestyle=linestyle, marker=marker, label=label)
        if ax1 is None:
            ax.set_title(title)
            ax.set_xlabel(xlabel)
            ax.set_ylabel(ylabel)
            if xlim:
                ax.set_xlim(xlim)
            if ylim:
                ax.set_ylim(ylim)
            if xticks:
                ax.set_xticks(xticks)
            if yticks:
                ax.set_yticks(yticks)
            if grid:
                ax.grid()
            if legend:
                ax.legend()
        if save:
            plt.savefig(save_path, dpi=dpi, bbox_inches=bbox_inches)
        if show:
            plt.show()
        else:
            return fig, ax
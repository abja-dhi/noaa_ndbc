import pandas as pd
import numpy as np
from scipy import signal
from .plotter import Plotter
from scipy.interpolate import interp1d
import os
import matplotlib.pyplot as plt
from matplotlib.widgets import LassoSelector
from matplotlib.path import Path

class Instrument:
    conversion_factors = {
            "mm": {"cm": 0.1, "m": 0.001},
            "cm": {"mm": 10, "m": 0.01},
            "m": {"mm": 1000, "cm": 100},
            "m/s": {"cm/s": 100, "mm/s": 1000},
            "cm/s": {"m/s": 0.01, "mm/s": 10},
            "mm/s": {"m/s": 0.001, "cm/s": 0.1}
        }
    
    def __init__(self, test_name, instrument, data, thresholds=None, color=None) -> None:
        self.test_name = test_name
        self.name = instrument
        if "US" in self.name:
            self.variable = "Surface Elevation"
        elif "ADV" in self.name:
            self.variable = "Velocity"
        self.data = data.copy().to_numpy()
        self.time = data.index.copy().to_numpy()
        self.original_data = self.data.copy()
        self.original_time = self.time.copy()
        self.thresholds = thresholds
        self.correction = None
        self.corner = None
        self.reach_time = None
        self.color = color
        self._set_instrument_info()

    def _set_instrument_info(self):
        if "US" in self.name:
            self.unit = "mm"
            self.label = "Z"
        elif "ADV" in self.name:
            self.unit = "m/s"
            self.label = "Velocity"
        
    def correct_data(self, threshold=None):
        if "US" in self.name:
            self._correct_US(threshold=threshold)
        elif "ADV" in self.name:
            self._correct_ADV()

    def _correct_US(self, threshold=None):
        idx_reach = np.where(self.time >= self.reach_time)[0][0]
        if threshold is not None:
           mask = (self.time < self.reach_time) & (self.data > threshold)
           self.data[mask] = np.nan
        sensor_height = np.nanmean(self.data[0:idx_reach])
        self.data = sensor_height - self.data
        self.data[self.time < self.reach_time] = 0

    def _correct_ADV(self):
        self.data[self.time < self.reach_time] = 0

    def get_duration(self, duration):
        self.duration = duration
        mask = self.time < duration
        self.data = self.data[mask]
        self.time = self.time[mask]

    def get_frequency(self):
        return 1 / (self.time[1] - self.time[0])
    
    def change_units(self, target_unit):
        if self.unit == target_unit:
            return
        
        # Determine the type of data: water depth or velocity
        if self.unit in self.conversion_factors and target_unit in self.conversion_factors[self.unit]:
            factor = self.conversion_factors[self.unit][target_unit]
            self.data = self.data * factor
            self.unit = target_unit
        else:
            raise ValueError(f"Conversion from {self.unit} to {target_unit} is not supported.")
        
    def reset_data(self):
        self.data = self.original_data.copy()
        self.time = self.original_time.copy()

    def noise_reduction(self, N, Wn, fs, btype='low'):
        sos = signal.butter(N, Wn, btype=btype, fs=fs, output='sos')
        self.data = signal.sosfilt(sos, self.data)

    def find_consecutive_runs(self, data):
        runs = []
        start_idx = None
        for idx in data:
            if start_idx is None:
                start_idx = idx
            elif idx != prev_idx + 1:
                runs.append((start_idx, prev_idx))
                start_idx = idx
            prev_idx = idx
        if start_idx is not None:
            runs.append((start_idx, prev_idx))
        return runs

    def interp(self, limit=None):
        if limit is None:
            limit = len(self.data)
        valid_indices = np.where(~np.isnan(self.data))[0]
        invalid_indices = np.where(np.isnan(self.data))[0]
        valid_data = self.data[valid_indices]
        consecutive_runs = self.find_consecutive_runs(invalid_indices)
        for run in consecutive_runs:
            run_length = run[1] - run[0] + 1
            if run_length <= limit:
                interp_indices = np.arange(run[0], run[1] + 1)
                self.data[interp_indices] = np.interp(interp_indices, valid_indices, valid_data)
        
    def cleaner(self):
        for _, row in self.thresholds.iterrows():
            unit = self.unit
            self.change_units(row["Unit"])
            if row["Type"].lower() == "g":
                mask = (self.time > row["Start"]) & (self.time < row["End"]) & (self.data > row["Threshold"])
                self.data[mask] = np.nan
            elif row["Type"].lower() == "l":
                mask = (self.time > row["Start"]) & (self.time < row["End"]) & (self.data < row["Threshold"])
                self.data[mask] = np.nan
            self.change_units(unit)

    def remove_negatives(self, threshold=0):
        self.data[self.data < threshold] = np.nan
        

    def normalize(self, d0):
        self.data = self.data / d0
        self.time = self.time * np.sqrt(9.81 / d0)

    def remove_value(self, value, threshold = 0.001):
        mask = np.abs(self.data - value) < threshold
        self.data[mask] = np.nan

    def remove_points(self):
        if not os.path.exists(f"{self.name}.csv"):
            print(f"No file found for {self.name}!")
            return
        data = pd.read_csv(f"{self.name}.csv", header=None, names=["Index"])
        indices = data["Index"].to_numpy()
        self.data[indices] = np.nan

    def to_csv(self, filtered=False):
        if not os.path.exists("Processed Data"):
            os.mkdir("Processed Data")
        df = pd.DataFrame(data=self.data, index=self.time, columns=[self.name + " [" + self.unit + "]"])
        if filtered:
            df.to_csv(f"Processed Data/{self.name}-filtered.csv")
        else:
            df.to_csv(f"Processed Data/{self.name}.csv")

    def plot(self, duration=60, description=True, x_description=0.8, y_description=0.7, set_prop=True, add_scour=False, add_final_scour=False, ax=None, fig=None, color=True, marker=False, **kwargs):
        label = kwargs.get("label", self.name)
        xlim = kwargs.get("xlim", [0, duration])
        kwargs["xlim"] = xlim
        plot = Plotter(fig=fig, ax=ax, **kwargs)
        if color:
            color = self.color
        else:
            color = None
        fig, ax = plot.plot(self.time, self.data, label=f"{self.variable} - {label}", color=color, marker=marker)
        if add_scour:
            try:
                scour = -self._interp_correction()
                color = ax[0].lines[-1].get_color()
                if scour is not None:
                    plot.plot(self.time, scour, color=color, linestyle="--", label=f"Bed Elevation - {label}")
            except:
                pass
        if add_final_scour:
            if self.final_scour is not None:
                plot.scatter([self.time[-50]], [self.final_scour], color=color, marker="o", label=f"Final Scour Depth - {label}", alpha=1, s=50)
            
        if description:
            plot.add_description(self.test_name, x_description=x_description, y_description=y_description)
        if set_prop:
            plot.set_prop(xlabel="Time [s]", ylabel=f"{self.label} [{self.unit}]", title=self.test_name, legend=True, grid=False, **kwargs)
        return plot

    def moving_average(self, window_size, min_periods=1):
        """
        Calculate the moving average of a numpy array, handling NaN values.
        
        Parameters:
        data (np.array): Input data array.
        window_size (int): Size of the moving average window.
        min_periods (int): Minimum number of observations in window required to have a value. Defaults to 1.
        
        Returns:
        np.array: Array of moving averages.
        """
        self.data = pd.Series(self.data).rolling(window=window_size, min_periods=min_periods).mean().to_numpy()

    def time_based_moving_average(self, start_time, end_time, window_size, min_periods=1):
        """
        Calculate the moving average of data for time less than average_time.
        
        Parameters:
        time (np.array): Input time array.
        data (np.array): Input data array.
        average_time (float): Time threshold for moving average.
        window_size (int): Size of the moving average window.
        min_periods (int): Minimum number of observations in window required to have a value. Defaults to 1.
        
        Returns:
        np.array: Array with moving averages where time < average_time and original data otherwise.
        """
        
        # Identify indices where time is less than average_time
        indices = np.where((self.time < end_time) & (self.time >= start_time))[0]
        
        # Initialize the result array
        result = np.copy(self.data)
        
        # Apply moving average to the subset where time < average_time
        if len(indices) > 0:
            subset_data = self.data[indices]
            moving_avg = pd.Series(subset_data).rolling(window=window_size, min_periods=min_periods).mean().to_numpy()
            result[indices] = moving_avg
        
        # For the subset where time >= average_time, the result array already contains the original data
        self.data = result

    def shift(self, shift_value):
        self.time = self.time + shift_value
        new_times = np.arange(0, self.time[0], 1/self.get_frequency())
        new_data = np.full(len(new_times), 0)
        self.time = np.concatenate((new_times, self.time))
        self.data = np.concatenate((new_data, self.data))
        mask = self.time < self.duration
        self.time = self.time[mask]
        self.data = self.data[mask]

    def correct_depth(self):
        if self.correction is None:
            print(f"No correction data available for {self.name}!")
            return
        else:
            unit = self.unit
            self.change_units(self.correction["Unit"].iloc[0])
            interp_depth = self._interp_correction()
            self.data = self.data + interp_depth
            self.change_units(unit)

    def _interp_correction(self):
        if self.correction is not None:
            correction_time = self.correction.index.to_numpy()
            correction_data = self.correction["Scour depth"].to_numpy().flatten()
            interp_func = interp1d(correction_time, correction_data, kind="linear", fill_value="extrapolate")
            interp_depth = interp_func(self.time)
            return interp_depth
        else:
            return None
        
    def _interp_corner(self):
        if self.corner is not None:
            corner_time = self.corner.index.to_numpy()
            corner_data = self.corner["Scour depth"].to_numpy().flatten()
            interp_func = interp1d(corner_time, corner_data, kind="linear", fill_value="extrapolate")
            interp_depth = interp_func(self.time)
            return interp_depth
        
    def point_selector(self, new_file=False, **kwargs):
        plot = self.plot(marker=True, **kwargs)
        ax = plot.ax[0]
        selector = SelectPoints(ax, self.time, self.data, f"{self.name}.csv", new_file=new_file)
        plt.show()
        
class SelectPoints:
    def __init__(self, ax, x, y, output_file, new_file):
        self.ax = ax
        self.x = x
        self.y = y
        self.output_file = output_file
        if new_file and os.path.exists(output_file):
            os.remove(output_file)
        self.selected_points = []
        self.lasso = LassoSelector(ax, onselect=self.onselect)
        # self.ax.plot(x, y, marker='o')
        
    def onselect(self, verts):
        path = Path(verts)
        ind = path.contains_points(list(zip(self.x, self.y)))
        selected_indices = np.where(ind)[0]
        with open(self.output_file, 'a') as f:
            for index in selected_indices:
                f.write(f"{index}\n")
        # print(f"Saved {len(selected_data)} points to {output_file}")
        self.ax.scatter(self.x[ind], self.y[ind], color='red')
        plt.draw()
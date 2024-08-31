import pandas as pd
import numpy as np
from scipy import signal
from .plotter import Plotter
from scipy.interpolate import interp1d

class Instrument:
    conversion_factors = {
            "mm": {"cm": 0.1, "m": 0.001},
            "cm": {"mm": 10, "m": 0.01},
            "m": {"mm": 1000, "cm": 100},
            "m/s": {"cm/s": 100, "mm/s": 1000},
            "cm/s": {"m/s": 0.01, "mm/s": 10},
            "mm/s": {"m/s": 0.001, "cm/s": 0.1}
        }
    
    def __init__(self, test_name, instrument, data) -> None:
        self.test_name = test_name
        self.name = instrument
        self.data = data.copy().to_numpy()
        self.time = data.index.copy().to_numpy()
        self.original_data = self.data.copy()
        self.original_time = self.time.copy()
        self.correction = None
        self._set_instrument_info()

    def _set_instrument_info(self):
        if "US" in self.name:
            self.unit = "mm"
            self.label = "Water Elevation"
        elif "ADV" in self.name:
            self.unit = "m/s"
            self.label = "Velocity"
        
    def correct_data(self, reach_time):
        if "US" in self.name:
            self._correct_US(reach_time)
        elif "ADV" in self.name:
            self._correct_ADV(reach_time)

    def _correct_US(self, reach_time):
        idx_reach = np.where(self.time >= reach_time)[0][0]
        sensor_height = np.nanmean(self.data[0:idx_reach])
        self.data = sensor_height - self.data
        self.data[self.time < reach_time] = 0

    def _correct_ADV(self, reach_time):
        self.data[self.time < reach_time] = 0

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
        
    def cleaner(self, thresholds):
        for row in thresholds:
            if row[3].lower() == "g":
                mask = (self.time > row[0]) & (self.time < row[1]) & (self.data > row[2])
                self.data[mask] = np.nan
            elif row[3].lower() == "l":
                mask = (self.time > row[0]) & (self.time < row[1]) & (self.data < row[2])
                self.data[mask] = np.nan

    def remove_negatives(self):
        self.data[self.data < 0] = np.nan
        

    def normalize(self, d0):
        self.data = self.data / d0
        self.time = self.time * np.sqrt(9.81 / d0)

    def remove_value(self, value, threshold = 0.001):
        mask = np.abs(self.data - value) < threshold
        self.data[mask] = np.nan

    def to_csv(self, filtered=False):
        df = pd.DataFrame(data=self.data, index=self.time, columns=[self.name + " [" + self.unit + "]"])
        if filtered:
            df.to_csv(f"{self.name}-filtered.csv")
        else:
            df.to_csv(f"{self.name}.csv")

    def plot(self, duration=60, description=True, x_description=0.8, y_description=0.7, **kwargs):
        plot = Plotter()
        plot.plot(self.time, self.data, label=self.name, **kwargs)
        if description:
            plot.add_description(self.test_name, x_description=x_description, y_description=y_description)
        plot.set_prop(xlabel="Time [s]", ylabel=f"{self.label} [{self.unit}]", title=self.test_name, xlim=[0, duration], legend=True, grid=False, **kwargs)
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
            print("No correction data available!")
            return
        else:
            correction_time = self.correction.index.to_numpy()
            correction_data = self.correction.to_numpy().flatten()
            interp_func = interp1d(correction_time, correction_data, kind="linear", fill_value="extrapolate")
            interp_depth = interp_func(self.time)
            self.data = self.data + interp_depth
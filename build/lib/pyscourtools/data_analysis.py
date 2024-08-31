import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import signal


class Data_Analysis:
    def __init__(self, time, data):
        self.original_data = data
        self.original_time = time
        self.time = time
        self.data = data
        if len(self.time) != len(self.data):
            raise ValueError("Time and data arrays must have the same length.")

    def reset_data(self):
        self.data = self.original_data
        self.time = self.original_time

    def noise_reduction(self, N, Wn, fs, btype='low'):
        sos = signal.butter(N, Wn, btype=btype, fs=fs, output='sos')
        self.data = signal.sosfilt(sos, self.data)
    
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

    def find_consecutive_runs(self):
        runs = []
        start_idx = None
        for idx in self.data:
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
                # Interpolate using np.interp
                interp_indices = np.arange(run[0], run[1] + 1)
                self.data[interp_indices] = np.interp(interp_indices, valid_indices, valid_data)
        
    def cleaner(self, thresholds):
        for row in thresholds:
            if "g" in row[3].lower():
                mask = (self.time > row[0]) & (self.time < row[1]) & (self.data > row[2])
                self.data[mask] = np.nan
            elif "l" in row[3].lower():
                mask = (self.time > row[0]) & (self.time < row[1]) & (self.data < row[2])
                self.data[mask] = np.nan
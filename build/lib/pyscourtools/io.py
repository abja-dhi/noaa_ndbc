import pandas as pd
import numpy as np

class IO:
    def __init__(self, fname) -> None:
        self.fname = fname
        try:
            self.data = pd.read_csv(self.fname, delim_whitespace=True, skiprows=1, header=None, names=["Time", "US1", "US2", "US3", "US4", "US5", "ADV-x", "ADV-y", "ADV-z"], usecols=[0,1,2,3,4,5,6,7,8], index_col=0)
        except FileNotFoundError:
            print(f"Error: {self.fname} not found!")
            self.data = None
    
    def get_item(self, item, duration):
        if self.data is None:
            return None
        time = self.data.index.copy().to_numpy()
        try:
            data = self.data[item].copy().to_numpy()
            if duration is not None:
                indices = np.where(time < duration)[0]
                time = time[indices]
                data = data[indices]
            return time, data
        except KeyError:
            print(f"Error: {item} not found in the data! Only time is returned!")
            return time
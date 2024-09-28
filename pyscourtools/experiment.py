from .plotter import Plotter
from .video import Video
from .instrument import Instrument
from .animation import VideoOnScreen, VideoAsAnimation
from .io import IO
from .scour import ScourScatter
import pandas as pd
import numpy as np
import os


class Experiment:
    colors = {"US1": '#283747', "US2": '#0051a2', "US3": '#41ab5d', "US4": '#feb24c', "US5": '#93003a', "ADV": "#283747"}
    def __init__(self,
                 test_name,
                 filename=None,
                 instruments=["US1", "US2", "US3", "US4", "ADV"],
                 use_corrected_instruments=False,
                 use_filtered_instruments=False,
                 videos=["Upstream", "Downstream", "Side", "Front", "Back"],
                 use_trimmed_videos=True,
                 path='.',
                 duration=60,
                 thresholds=None,
                 add_scour=True,
                 structure="auto",
                 reach_times="Reach Times.csv",
                 point_cloud_fname="LiDAR/Point Cloud.txt",
                 rotate_X_start=None, rotate_X_end=None, rotate_y=None, rotate=None,
                 apply_filter=True) -> None:
        self.path = path
        self.duration = duration
        self.test_name = test_name
        if thresholds is not None:
            self.thresholds = pd.read_csv(thresholds)
        if use_corrected_instruments:
            data = None
            for instrument in instruments:
                if use_filtered_instruments:
                    df = pd.read_csv(f"{path}/Processed Data/{instrument}-filtered.csv", index_col=0)
                else:
                    df = pd.read_csv(f"{path}/Processed Data/{instrument}.csv", index_col=0)
                unit = df.columns[0].split("[")[1].split("]")[0]
                if data is None:
                    data = df
                else:
                    data = pd.concat([data, df.iloc[:, 0]], axis=1)
                inst = Instrument(test_name=test_name, instrument=instrument, data=df.iloc[:, 0], color=self.colors[instrument])
                inst.unit = unit
                setattr(self, instrument, inst)
            self.data = data
        else:
            self.filename = filename
            io = IO(self.filename)
            self.frequency = io.get_frequency()
            self.data = io.data
            
            for instrument in instruments:
                mask = self.thresholds["Instrument"] == instrument
                setattr(self, instrument, Instrument(test_name=test_name, instrument=instrument, data=self.data[instrument], thresholds=self.thresholds[mask], color=self.colors[instrument]))
        for view in videos:
            setattr(self, view.capitalize(), Video(view=view, path=path, use_trimmed_videos=use_trimmed_videos, duration=self.duration))
        
        if os.path.exists(os.path.join(path, "Scour Depth")):
            for f in os.listdir(os.path.join(path, "Scour Depth")):
                if f.endswith(".csv"):
                    if f.split(".")[0] in instruments:
                        df = pd.read_csv(os.path.join(path, f"Scour Depth/{f}"), index_col=1)
                        instrument = getattr(self, f.split(".")[0])
                        instrument.correction = df
                    elif "final scour" in f.lower():
                        df = pd.read_csv(os.path.join(path, f"Scour Depth/{f}"), index_col=0, header=None, names=["Instrument", "Scour Depth"])
                        for inst in df.index.to_list():
                            if inst in instruments:
                                instrument = getattr(self, inst)
                                instrument.final_scour = df.loc[inst, "Scour Depth"]
                    elif "corner" in f.lower():
                        df = pd.read_csv(os.path.join(path, f"Scour Depth/{f}"), index_col=1)
                        instrument = getattr(self, "US3")
                        instrument.corner = df
                                
        if os.path.exists(os.path.join(path, reach_times)):
            times = pd.read_csv(os.path.join(path, reach_times), index_col=0, skiprows=1, names=["Instrument", "Reach Time"])
            for inst, row in times.iterrows():
                instrument = getattr(self, inst)
                instrument.reach_time = row["Reach Time"]
        if add_scour:
            if os.path.exists(os.path.join(path, point_cloud_fname)):
                self.scour_path = os.path.join(path, point_cloud_fname)
                self.scour = ScourScatter(self, apply_filter=apply_filter, structure=structure, rotate=rotate, rotate_X_start=rotate_X_start, rotate_X_end=rotate_X_end, rotate_y=rotate_y)

    def plot(self, instruments=["US1", "US2", "US3", "US4"], duration=60, description=True, x_description=0.8, y_description=0.7, add_scour=False, **kwargs):
        if isinstance(instruments, str):
            instruments = [instruments]
        if "ADV" in instruments:
            instruments.remove("ADV")
            print("Warning: ADV data is not plotted due to inconsistency with the other instruments!")
        plot = Plotter()
        for instrument in instruments:
            ins = getattr(self, instrument)
            ins.get_duration(duration)
            ins.plot(fig=plot.fig, ax=plot.ax, description=False, set_prop=False, add_scour=add_scour, **kwargs)
        plot.set_prop(xlabel="Time [s]", ylabel=f"Elevation [{ins.unit}]", title=self.test_name, legend=True, grid=False, xlim=[0, duration], **kwargs)
        if description:
            plot.add_description(self.test_name, x_description=x_description, y_description=y_description)
        return plot
    
    def animate(self, instrument, video, speed_factor=1.0, show=True, save=False, add_scour=False, **kwargs):
        if show and save:
            raise ValueError("Both show and save cannot be True!")
        inst = getattr(self, instrument)
        vid = getattr(self, video)
        if show:
            VideoOnScreen(vid, inst, speed_factor, test_name=self.test_name, add_scour=add_scour, **kwargs).start(**kwargs)
        elif save:
            VideoAsAnimation(vid, inst, speed_factor, test_name=self.test_name, add_scour=add_scour, **kwargs).start(**kwargs)
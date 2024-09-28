from .plotter import Plotter
from .video import Video
from .instrument import Instrument
from .animation import VideoOnScreen, VideoAsAnimation
from .io import IO
import pandas as pd
import os


class Experiment:
    def __init__(self,
                 test_name,
                 filename=None,
                 instruments=["US1", "US2", "US3", "US4", "ADV"],
                 use_corrected_instruments=False,
                 use_filtered_instruments=False,
                 videos=["Upstream", "Downstream", "Side", "Front", "Back"],
                 use_trimmed_videos=True,
                 path=None,
                 duration=60) -> None:
        self.duration = duration
        self.test_name = test_name
        if use_corrected_instruments:
            data = None
            for instrument in instruments:
                if use_filtered_instruments:
                    df = pd.read_csv(f"{path}/{instrument}-filtered.csv", index_col=0)
                else:
                    df = pd.read_csv(f"{path}/{instrument}.csv", index_col=0)
                unit = df.columns[0].split("[")[1].split("]")[0]
                if data is None:
                    data = df
                else:
                    data = pd.concat([data, df.iloc[:, 0]], axis=1)
                inst = Instrument(test_name=test_name, instrument=instrument, data=df.iloc[:, 0])
                inst.unit = unit
                setattr(self, instrument, inst)
            self.data = data
        else:
            self.filename = filename
            io = IO(self.filename)
            self.frequency = io.get_frequency()
            self.data = io.data
            for instrument in instruments:
                setattr(self, instrument, Instrument(test_name=test_name, instrument=instrument, data=self.data[instrument]))
        for view in videos:
            setattr(self, view.capitalize(), Video(view=view, use_trimmed_videos=use_trimmed_videos, duration=self.duration))
        if os.path.exists("Scour Depth"):
            for f in os.listdir("Scour Depth"):
                if f.endswith(".csv"):
                    if f.split(".")[0] in instruments:
                        df = pd.read_csv(f"Scour Depth/{f}", index_col=0)
                        instrument = getattr(self, f.split(".")[0])
                        instrument.correction = df

    def plot(self, instruments=["US1", "US2", "US3", "US4"], duration=60, description=True, x_description=0.8, y_description=0.7, **kwargs):
        if isinstance(instruments, str):
            instruments = [instruments]
        if "ADV" in instruments:
            instruments.remove("ADV")
            print("Warning: ADV data is not plotted due to inconsistency with the other instruments!")
        plot = Plotter()
        for instrument in instruments:
            ins = getattr(self, instrument)
            ins.get_duration(duration)
            plot.plot(ins.time, ins.data, label=ins.name, **kwargs)
        plot.set_prop(xlabel="Time [s]", ylabel="Water Elevation [m]", title=self.test_name, legend=True, grid=False, xlim=[0, duration], **kwargs)
        if description:
            plot.add_description(self.test_name, x_description=x_description, y_description=y_description)
        return plot
    
    def animate(self, instrument, video, speed_factor=1.0, show=True, save=False):
        if show and save:
            raise ValueError("Both show and save cannot be True!")
        inst = getattr(self, instrument)
        vid = getattr(self, video)
        if show:
            VideoOnScreen(vid, inst, speed_factor, test_name=self.test_name).start()
        elif save:
            VideoAsAnimation(vid, inst, speed_factor, test_name=self.test_name).start()
        
    
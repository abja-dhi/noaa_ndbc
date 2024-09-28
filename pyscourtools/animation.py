import cv2
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
import time
from matplotlib.animation import FFMpegWriter
from .video import Video
from .instrument import Instrument
from .plotter import Plotter
import os

class _VideoAnimation:
    def __init__(self, va: Video, inst: Instrument, speed_factor=1.0, test_name="Test", add_scour=False, **kwargs):
        x_description = kwargs.get("x_description", 0.01)
        y_description = kwargs.get("y_description", 0.28)
        self.va = va
        self.inst = inst
        self.frame_rate = self.va.get_fps()
        self.data_frequency = self.inst.get_frequency()
        self.video_cap = cv2.VideoCapture(self.va.input)
        plot = Plotter(nrow=2, ncol=1, figwidth=10, figheight=8)
        self.fig = plot.fig
        plot.add_description(test_name, x_description=x_description, y_description=y_description, ax_number=1, facecolor=None, alpha=0, fontsize=10)
        self.fig.suptitle(test_name, fontsize=16, fontweight='bold')
        axs = plot.ax
        self.ax_video = axs[0]
        self.ax_plot = axs[1]
        if "US" in self.inst.name:
            self.line, = self.ax_plot.plot(self.inst.time, self.inst.data, label=f"{self.inst.name} - Surface Elevation")
        else:
            self.line, = self.ax_plot.plot(self.inst.time, self.inst.data, label=f"Flow Velocity")
        self.red_dot, = self.ax_plot.plot([], [], 'ro', markersize=5)
        self.add_scour = add_scour
        self.color = self.line.get_color()
        if add_scour:
            self.scour = -inst._interp_correction()
            self.scour_line, = self.ax_plot.plot(self.inst.time, self.scour, label=f"{self.inst.name} Scour Depth", linestyle='--', color=self.color)
            self.scour_dot, = self.ax_plot.plot([], [], 'ro', markersize=5)
            if self.inst.name == "US3" and self.inst.corner is not None:
                self.corner = -inst._interp_corner()
                self.corner_line, = self.ax_plot.plot(self.inst.time, self.corner, label="Upstream Corner Scour Depth", linestyle='--', color='#feb24c')
                self.corner_dot, = self.ax_plot.plot([], [], 'ro', markersize=5)
        self.set_prop()
        self.running = False
        self.speed_factor = speed_factor
        self.current_time = 0
        

    def _get_prop(self):
        if "US" in self.inst.name:
            xlabel = "Time [s]"
            ylabel = f"Z [{self.inst.unit}]"
            if self.add_scour:
                title = "Timeseries of Surface Elevation and Scour Depth"
            else:
                title = "Timeseries of Surface Elevation"
        elif "ADV" in self.inst.name:
            xlabel = "Time [s]"
            ylabel = f"Velocity [{self.inst.unit}]"
            title = "Timeseries of Velocity"
        return xlabel, ylabel, title

    def set_prop(self):
        xlabel, ylabel, title = self._get_prop()
        self.ax_plot.set_xlabel(xlabel)
        self.ax_plot.set_ylabel(ylabel)
        self.ax_plot.set_title(title)
        self.ax_plot.legend()

class VideoOnScreen(_VideoAnimation):
    def __init__(self, va: Video, inst: Instrument, speed_factor=1.0, test_name="Test", add_scour=False, **kwargs):
        super().__init__(va, inst, speed_factor, test_name, add_scour, **kwargs)  
        self.paused = False
        self.start_time = time.time()
        self.setup_gui()      

    def setup_gui(self):
        ax_pause = plt.axes([0.81, 0.01, 0.1, 0.05])
        ax_play = plt.axes([0.59, 0.01, 0.1, 0.05])

        self.btn_pause = Button(ax_pause, 'Pause')
        self.btn_play = Button(ax_play, 'Play')

        self.btn_pause.on_clicked(self.pause)
        self.btn_play.on_clicked(self.play)

    def start(self, **kwargs):
        self.rotate = kwargs.pop('rotate', False)
        self.running = True
        self.paused = False
        self.current_time = 0
        self.start_time = time.time()  # Correct start time
        self.run(**kwargs)
        plt.show()

    def pause(self, event=None):
        self.paused = True
        self.current_time = (time.time() - self.start_time) * self.speed_factor

    def play(self, event=None):
        if not self.running:
            self.running = True
            self.start_time = time.time() - self.current_time / self.speed_factor  # Correct start time
            self.run()
        else:
            self.paused = False
            self.start_time = time.time() - self.current_time / self.speed_factor  # Correct start time

    def run(self, **kwargs):
        total_frames = int(self.video_cap.get(cv2.CAP_PROP_FRAME_COUNT))

        ymin = kwargs.get("ymin", self.ax_plot.get_ylim()[0])
        ymax = kwargs.get("ymax", self.ax_plot.get_ylim()[1])
        self.ax_plot.set_xlim(self.inst.time[0], self.inst.time[-1])
        self.ax_plot.set_ylim(ymin, ymax)
        
        while self.running:
            if not self.paused:
                self.current_time = (time.time() - self.start_time) * self.speed_factor

                # Calculate the current frame index
                frame_idx = int(self.current_time * self.frame_rate)
                data_idx = int(self.current_time * self.data_frequency)

                # Set the video to the correct frame
                self.video_cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)

                ret, frame = self.video_cap.read()
                if not ret or frame_idx >= total_frames or data_idx >= len(self.inst.time):
                    break

                self.ax_video.clear()
                if self.rotate:
                    rotated_frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
                    rotated_frame_rgb = cv2.cvtColor(rotated_frame, cv2.COLOR_BGR2RGB)
                else:
                    rotated_frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                self.ax_video.imshow(rotated_frame_rgb)
                self.ax_video.axis('off')
                self.ax_video.set_title(f"Time: {self.current_time:.2f} s")

                self.red_dot.set_data(self.inst.time[data_idx], self.inst.data[data_idx])
                self.ax_plot.draw_artist(self.line)
                self.ax_plot.draw_artist(self.red_dot)
                if self.add_scour:
                    self.scour_dot.set_data(self.inst.time[data_idx], self.scour[data_idx])
                    self.ax_plot.draw_artist(self.scour_line)
                    self.ax_plot.draw_artist(self.scour_dot)
                    if self.inst.name == "US3" and self.inst.corner is not None:
                        self.corner_dot.set_data(self.inst.time[data_idx], self.corner[data_idx])
                        self.ax_plot.draw_artist(self.corner_line)
                        self.ax_plot.draw_artist(self.corner_dot)
                            
                plt.pause(0.01)
            else:
                plt.pause(0.1)

        self.video_cap.release()


class VideoAsAnimation(_VideoAnimation):
    def __init__(self, va: Video, inst: Instrument, speed_factor=1.0, test_name="Test", add_scour=False, **kwargs):
        super().__init__(va, inst, speed_factor, test_name, add_scour, **kwargs)
        if not os.path.exists("Animations"):
            os.mkdir("Animations")
        self.output = f"Animations/{self.inst.name} - {self.va.view}.mp4"

    def start(self, **kwargs):
        self.rotate = kwargs.pop('rotate', False)
        self.running = True
        self.current_time = 0
        self.run(**kwargs)

    def run(self, **kwargs):
        total_frames = int(self.video_cap.get(cv2.CAP_PROP_FRAME_COUNT))

        ymin = kwargs.get("ymin", self.ax_plot.get_ylim()[0])
        ymax = kwargs.get("ymax", self.ax_plot.get_ylim()[1])
        self.ax_plot.set_xlim(self.inst.time[0], self.inst.time[-1])
        self.ax_plot.set_ylim(ymin, ymax)
        
        # Set up the FFMpeg writer
        writer = FFMpegWriter(fps=self.frame_rate)
        with writer.saving(self.fig, self.output, dpi=100):
            while self.running:
                print(self.current_time)
                # Calculate the current frame index
                frame_idx = int(self.current_time * self.frame_rate)
                data_idx = int(self.current_time * self.data_frequency)
                # Set the video to the correct frame
                self.video_cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = self.video_cap.read()
                if not ret or frame_idx >= total_frames or data_idx >= len(self.inst.time):
                    break
                self.ax_video.clear()
                if self.rotate:
                    rotated_frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
                    rotated_frame_rgb = cv2.cvtColor(rotated_frame, cv2.COLOR_BGR2RGB)
                else:
                    rotated_frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                self.ax_video.imshow(rotated_frame_rgb)
                self.ax_video.axis('off')
                self.ax_video.set_title(f"Time: {self.current_time:.2f} s")
                self.red_dot.set_data(self.inst.time[data_idx], self.inst.data[data_idx])
                self.ax_plot.draw_artist(self.line)
                self.ax_plot.draw_artist(self.red_dot)
                if self.add_scour:
                    self.scour_dot.set_data(self.inst.time[data_idx], self.scour[data_idx])
                    self.ax_plot.draw_artist(self.scour_line)
                    self.ax_plot.draw_artist(self.scour_dot)
                    if self.inst.name == "US3" and self.inst.corner is not None:
                        self.corner_dot.set_data(self.inst.time[data_idx], self.corner[data_idx])
                        self.ax_plot.draw_artist(self.corner_line)
                        self.ax_plot.draw_artist(self.corner_dot)
                writer.grab_frame()
                self.current_time = self.current_time + (1 / self.frame_rate) * self.speed_factor
                
        self.video_cap.release()
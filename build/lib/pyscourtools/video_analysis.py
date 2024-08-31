from moviepy.editor import VideoFileClip
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
import matplotlib.pyplot as plt
import math
import subprocess
import os
import numpy as np

class Video_Analysis:
    def __init__(self, input_file):
        self.input = input_file

    def extract_video_segment(self, start_time, duration, output_file):        
        end_time = start_time + duration
        # Construct the ffmpeg command to include only video and audio streams
        cmd = [
            "ffmpeg",
            "-y",  # Overwrite output file if it exists
            "-i", f"{self.input}",
            "-ss", str(start_time),
            "-to", str(end_time),
            "-map", "0:v",  # Select only video stream
            "-map", "0:a",  # Select only audio stream
            "-c", "copy",  # Copy the streams as is
            output_file
        ]

        try:
            subprocess.call(cmd)
            return 0
        except:
            print("Error: Unable to extract video segment")
            return 1

    def get_video_fps(self):
        video = VideoFileClip(self.input)
        fps = video.fps
        video.close()
        return fps

    def show_frames_between_times(self, start_time, end_time, video_title="Video", n_rotates=2):
        clip = VideoFileClip(self.input)
        
        current_time = start_time
        fps = clip.fps
        duration = end_time - start_time
        
        num_frames = int(duration * fps)
        
        for i in range(num_frames):
            frame = clip.get_frame(current_time)
            frame = np.rot90(frame, n_rotates)
            
            plt.figure(figsize=(15, 20))
            plt.imshow(frame)
            plt.title(f"{video_title} - Time: {current_time:.4f} seconds")
            plt.axis('off')
            plt.show()
            
            current_time += 1.0 / fps
        
        clip.close()

    def show_frames_as_table(self, start_time, end_time, video_title="Video"):
        clip = VideoFileClip(self.input)
        fps = clip.fps
        duration = end_time - start_time
        
        num_frames = int(duration * fps)
        frame_interval = 1.0 / fps

        num_columns = 5
        num_rows = math.ceil(num_frames / num_columns)
        
        fig, axs = plt.subplots(num_rows, num_columns, figsize=(15, num_rows * 3))
        fig.suptitle(f"{video_title} - Frames between {start_time:.2f} s and {end_time:.2f} s", fontsize=20)
        for i in range(num_frames):
            current_time = start_time + i * frame_interval
            frame = clip.get_frame(current_time)
            
            row = i // num_columns
            col = i % num_columns
            
            axs[row, col].imshow(frame)
            axs[row, col].set_title(f"Time: {current_time:.4f} s")
            axs[row, col].axis('off')
        
        for j in range(i + 1, num_rows * num_columns):
            row = j // num_columns
            col = j % num_columns
            axs[row, col].axis('off')
        
        plt.tight_layout()
        plt.show()
        
        clip.close()
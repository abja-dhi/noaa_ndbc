import cv2
import matplotlib.pyplot as plt
import subprocess
import os

class Video:
    def __init__(self, view, use_trimmed_videos=False, duration=60):
        self.duration = duration
        view = view.lower()
        if view not in ["upstream", "downstream", "side", "front", "back"]:
            raise ValueError("Invalid view. Choose 'upstream', 'downstream', 'side', 'front', or 'back'.")
        self.view = view.capitalize()
        if use_trimmed_videos:
            fname = f"{self.view} 0.0 - {self.duration}.mp4"
            if not os.path.exists(os.path.join("Videos", fname)):
                print(f"Warning: Trimmed video not found for {view}. Using original video.")
                self.input = os.path.join("Videos", f"{self.view}.mp4")
            else:
                self.input = os.path.join("Videos", f"{self.view} 0.0 - {self.duration}.mp4")
        else:
            self.input = os.path.join("Videos", f"{self.view}.mp4")
        
        

    def get_fps(self):
        cap = cv2.VideoCapture(self.input)
        fps = cap.get(cv2.CAP_PROP_FPS)
        cap.release()
        return fps
    
    def show_frames_between_times(self, start_time, end_time, display_mode='table'):
        # Open the video file
        cap = cv2.VideoCapture(self.input)
        
        if not cap.isOpened():
            print("Error: Could not open video.")
            return
        
        # Get the frame rate
        frame_rate = cap.get(cv2.CAP_PROP_FPS)
        
        # Calculate start and end frames
        start_frame = int(start_time * frame_rate)
        end_frame = int(end_time * frame_rate)
        
        frames = []
        
        # Set the video to start frame
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        
        # Capture frames between start and end times
        for frame_num in range(start_frame, end_frame):
            ret, frame = cap.read()
            if not ret:
                break
            frames.append((frame_num / frame_rate, frame))
        
        cap.release()
        
        if display_mode == 'table':
            self.display_frames_as_table(frames)
        elif display_mode == 'separate':
            self.display_frames_separately(frames)
        else:
            print("Invalid display mode. Choose 'table' or 'separate'.")

    @staticmethod
    def display_frames_as_table(frames):
        # Calculate number of rows and columns
        num_frames = len(frames)
        num_cols = min(num_frames, 5)  # Limit columns to 5
        num_rows = (num_frames + num_cols - 1) // num_cols
        
        fig, axes = plt.subplots(num_rows, num_cols, figsize=(15, 3 * num_rows))
        fig.suptitle("Frames", fontsize=16)
        if num_rows == 1:
            axes = [axes]
        
        for i, (time, frame) in enumerate(frames):
            row = i // num_cols
            col = i % num_cols
            ax = axes[row][col] if num_rows > 1 else axes[col]
            ax.imshow(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            ax.set_title(f"Time: {time:.4f} s")
            ax.axis('off')
        
        # Hide any unused subplots
        for j in range(i + 1, num_rows * num_cols):
            row = j // num_cols
            col = j % num_cols
            ax = axes[row][col] if num_rows > 1 else axes[col]
            ax.axis('off')
        
        plt.tight_layout()
        plt.show()

    @staticmethod
    def display_frames_separately(frames):
        for time, frame in frames:
            plt.figure(figsize=(20, 15))
            plt.imshow(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            plt.title(f"Time: {time:.4f} s")
            plt.axis('off')
            plt.show()

    def extract_video_segment(self, start_time):
        # Open the video file
        cap = cv2.VideoCapture(self.input)
        
        if not cap.isOpened():
            print("Error: Could not open video.")
            return
        
        # Get the frame rate and frame count
        frame_rate = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Calculate start and end frames
        start_frame = int(start_time * frame_rate)
        end_frame = int((start_time + self.duration) * frame_rate)
        
        # Check if end frame exceeds total frames
        if end_frame > total_frames:
            end_frame = total_frames
        
        # Set the video to start frame
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        
        # Get the width and height of the frames
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Define the codec and create VideoWriter object
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Codec for .mp4 format
        out = cv2.VideoWriter(self.input.replace(".mp4", f" 0.0 - {self.duration}.mp4"), fourcc, frame_rate, (width, height))
        
        # Write frames from start to end frame
        for frame_num in range(start_frame, end_frame):
            print(f"{frame_num}/{end_frame}")
            ret, frame = cap.read()
            if not ret:
                break
            out.write(frame)
        
        # Release everything if job is finished
        cap.release()
        out.release()
        print("Extracted video saved to " + self.input.replace(".mp4", f"0.0 - {self.duration}.mp4"))
        self.input = os.path.join("Videos", f"{self.view} 0.0 - {self.duration}.mp4")
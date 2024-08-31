import cv2
import matplotlib.pyplot as plt
import shutil
import os

class Video:
    def __init__(self, view, path, use_trimmed_videos=False, duration=60):
        self.duration = duration
        view = view.lower()
        if view not in ["upstream", "downstream", "side", "front", "back"]:
            raise ValueError("Invalid view. Choose 'upstream', 'downstream', 'side', 'front', or 'back'.")
        self.view = view.capitalize()
        if use_trimmed_videos:
            fname = f"{self.view} 0.0 - {self.duration}.mp4"
            if not os.path.exists(os.path.join(path, "Videos", fname.capitalize())):
                print(f"Warning: Trimmed video not found for {view}. Using original video.")
                self.input = os.path.join(path, "Videos", f"{self.view}.mp4")
            else:
                self.input = os.path.join(path, "Videos", f"{self.view} 0.0 - {self.duration}.mp4")
        else:
            self.input = os.path.join(path, "Videos", f"{self.view}.mp4")
        
        

    def get_fps(self):
        cap = cv2.VideoCapture(self.input)
        fps = cap.get(cv2.CAP_PROP_FPS)
        cap.release()
        return fps
    
    def _get_frames(self, start_time, end_time):
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
        return frames
    

    def show_frames_between_times(self, start_time, end_time, display_mode='table', draw_line=False, save=False, **kwargs):
        frames = self._get_frames(start_time, end_time)
        
        if display_mode == 'table':
            self.display_frames_as_table(frames)
        elif display_mode == 'separate':
            self.display_frames_separately(frames, draw_line=draw_line, save=save, **kwargs)
        else:
            print("Invalid display mode. Choose 'table' or 'separate'.")

    @staticmethod
    def display_frames_as_table(frames):
        # Calculate number of rows and columns
        num_frames = len(frames)
        num_cols = min(num_frames, 9)  # Limit columns to 5
        num_rows = (num_frames + num_cols - 1) // num_cols
        
        fig, axes = plt.subplots(num_rows, num_cols, figsize=(2.5 * num_cols, 3 * num_rows))
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
    def display_frames_separately(frames, draw_line=False, save=False, **kwargs):
        if save:
            if os.path.exists("tmp"):
                shutil.rmtree("tmp")
            os.mkdir("tmp")
        for time, frame in frames:
            fig, ax = plt.subplots(figsize=(20, 15))
            ax.imshow(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            if draw_line:
                xmin = kwargs.get('xmin', ax.get_xlim()[0])
                xmax = kwargs.get('xmax', ax.get_xlim()[1])
                ymin = kwargs.get('ymin', ax.get_ylim()[0])
                ymax = kwargs.get('ymax', ax.get_ylim()[1])
                ax.plot([xmin, xmax], [ymin, ymax], 'r-', lw=2)
            ax.set_title(f"Time: {time:.4f} s")
            if save:
                print(time)
                fig.savefig(f"tmp/{time:.4f}.jpg")
                plt.close(fig)
            else:
                plt.show()
        print("Frames saved to 'tmp' directory! Do not forget to delete the directory after use.")

    def export_frames(self, start_time, end_time, path="Front Scour", draw_line=False, ymins=None, ymaxs=None, xmins=None, xmaxs=None, points=None, times=None, save=False):
        if not os.path.exists(path):
            os.mkdir(path)
        frames = self._get_frames(start_time, end_time)
        for time, frame in frames:
            print(time)
            if times is not None and time not in times:
                continue
            fig, ax = plt.subplots(figsize=(20, 15))
            ax.imshow(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            x_low = ax.get_xlim()[0]
            x_high = ax.get_xlim()[1]
            y_low = ax.get_ylim()[0]
            y_high = ax.get_ylim()[1]
            if draw_line:
                if ymins is not None and ymaxs is not None:
                    for ymin, ymax in zip(ymins, ymaxs):
                        ax.plot([x_low, x_high], [ymin, ymax], 'r-', lw=2)
                if xmins is not None and xmaxs is not None:
                    for xmin, xmax in zip(xmins, xmaxs):
                        ax.plot([xmin, xmax], [y_low, y_high], 'g-', lw=2)
                if points is not None:
                    for point in points:
                        for i, p in enumerate(point[0]):
                            if p is None:
                                point[0][i] = x_high
                        for i, p in enumerate(point[1]):
                            if p is None:
                                point[1][i] = y_high
                        ax.plot(point[0], point[1], 'cyan', lw=2)
            ax.set_title(f"Time: {time:.4f} s")
            if save:
                fig.savefig(f"{path}/{time:.4f}.jpg")
                plt.close(fig)
            else:
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
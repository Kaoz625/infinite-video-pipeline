"""
Video Generator: Infinite Video Creation Workflow
- Converts generated images into video sequences.
- Adds transitions, audio, and infinite looping with FFmpeg.
"""

import os
import subprocess

# Configuration
image_dir = os.path.expanduser('~/infinite-video-pipeline/outputs')
output_video = os.path.expanduser('~/infinite-video-pipeline/final_video.mp4')
audio_file = os.path.expanduser('~/infinite-video-pipeline/background_audio.mp3')

# FFmpeg Commands
ffmpeg_images_to_video = (
    f"ffmpeg -framerate 1 -pattern_type glob -i '{image_dir}/*.png' "
    f"-c:v libx264 -r 30 -pix_fmt yuv420p {output_video}"
)

ffmpeg_add_audio = (
    f"ffmpeg -i {output_video} -i {audio_file} -c:v copy -c:a aac "
    f"-shortest {output_video.replace('.mp4', '_with_audio.mp4')}"
)

def create_video():
    try:
        print("[Video Generator] Converting images to video...")
        subprocess.run(ffmpeg_images_to_video, shell=True, check=True)
    except subprocess.CalledProcessError as error:
        print(f"[Video Generator Error] {str(error)}")

def add_audio():
    try:
        print("[Video Generator] Adding background audio to video...")
        subprocess.run(ffmpeg_add_audio, shell=True, check=True)
    except subprocess.CalledProcessError as error:
        print(f"[Video Generator Error] {str(error)}")

def main():
    create_video()
    if os.path.exists(audio_file):
        add_audio()

if __name__ == "__main__":
    print("[Pipeline] Starting Infinite Video Generation...")
    main()

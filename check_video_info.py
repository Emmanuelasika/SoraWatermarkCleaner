"""Check video file information"""
import ffmpeg
from pathlib import Path

video_path = Path("m2-res_470p.mp4")

probe = ffmpeg.probe(str(video_path))
video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')

print(f"File: {video_path}")
print(f"Size: {video_path.stat().st_size / (1024*1024):.2f} MB")
print(f"Resolution: {video_info['width']}x{video_info['height']}")
print(f"FPS: {eval(video_info['r_frame_rate']):.2f}")

duration = float(probe['format'].get('duration', 0))
fps = eval(video_info['r_frame_rate'])
frames = int(duration * fps) if duration > 0 else int(video_info.get('nb_frames', 0))

print(f"Duration: {duration:.2f} seconds")
print(f"Estimated frames: {frames}")
print(f"Codec: {video_info.get('codec_name', 'unknown')}")


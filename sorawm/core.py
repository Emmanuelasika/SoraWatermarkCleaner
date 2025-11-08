from pathlib import Path
from typing import Callable
import threading
import queue as queue_module
import time
import shutil

import ffmpeg
import numpy as np
from loguru import logger
from tqdm import tqdm

from sorawm.utils.video_utils import VideoLoader
from sorawm.watermark_cleaner import WaterMarkCleaner
from sorawm.watermark_detector import SoraWaterMarkDetector
from sorawm.utils.imputation_utils import (
    find_2d_data_bkps,
    get_interval_average_bbox,
    find_idxs_interval,
)

VIDEO_EXTENSIONS = [".mp4", ".avi", ".mov", ".mkv", ".flv", ".wmv", ".webm"]

class SoraWM:
    def __init__(self):
        self.detector = SoraWaterMarkDetector()
        self.cleaner = WaterMarkCleaner()

    def run_batch(self, input_video_dir_path: Path,
        output_video_dir_path: Path | None = None,
        progress_callback: Callable[[int], None] | None = None,
        quiet: bool = False,
        ):
        if output_video_dir_path is None:
            output_video_dir_path = input_video_dir_path.parent / "watermark_removed"
            if not quiet:
                logger.warning(f"output_video_dir_path is not set, using {output_video_dir_path} as output_video_dir_path")
        output_video_dir_path.mkdir(parents=True, exist_ok=True)        
        input_video_paths = []
        for ext in VIDEO_EXTENSIONS:
            input_video_paths.extend(input_video_dir_path.rglob(f"*{ext}"))
        
        video_lengths = len(input_video_paths)
        if not quiet:
            logger.info(f"Found {video_lengths} video(s) to process")
        for idx, input_video_path in enumerate(tqdm(input_video_paths, desc="Processing videos", disable=quiet)):
            output_video_path = output_video_dir_path / input_video_path.name            
            if progress_callback:
                def batch_progress_callback(single_video_progress: int):
                    overall_progress = int((idx / video_lengths) * 100 + (single_video_progress / video_lengths))
                    progress_callback(min(overall_progress, 100))
                
                self.run(input_video_path, output_video_path, progress_callback=batch_progress_callback, quiet=quiet)
            else:
                self.run(input_video_path, output_video_path, progress_callback=None, quiet=quiet)

    def run(
        self,
        input_video_path: Path,
        output_video_path: Path,
        progress_callback: Callable[[int], None] | None = None,
        quiet: bool = False,
    ):
        input_video_loader = VideoLoader(input_video_path)
        output_video_path.parent.mkdir(parents=True, exist_ok=True)
        width = input_video_loader.width
        height = input_video_loader.height
        fps = input_video_loader.fps
        total_frames = input_video_loader.total_frames

        temp_output_path = output_video_path.parent / f"temp_{output_video_path.name}"
        
        # Build FFmpeg input stream
        ffmpeg_input = ffmpeg.input(
            "pipe:",
            format="rawvideo",
            pix_fmt="bgr24",
            s=f"{width}x{height}",
            r=fps,
        )
        
        # Build output stream with safe, compatible options
        # Use explicit parameters that work across all FFmpeg versions
        output_kwargs = {
            "vcodec": "libx264",
            "pix_fmt": "yuv420p",
            "r": fps,  # Match input framerate
        }
        
        # Set quality/bitrate - use CRF for quality (lower = better quality)
        # CRF 20 is a good balance (default is 23, 20 gives better quality)
        if input_video_loader.original_bitrate:
            # Use bitrate if available from source
            bitrate = int(int(input_video_loader.original_bitrate) * 1.2)
            output_kwargs["video_bitrate"] = str(bitrate)
            output_kwargs["bufsize"] = str(bitrate * 2)  # Buffer size
        else:
            # Use CRF for quality-based encoding (no preset needed)
            output_kwargs["crf"] = "20"  # Quality setting (18-28 range, lower = better)
        
        # Create output stream
        ffmpeg_output = ffmpeg.output(ffmpeg_input, str(temp_output_path), **output_kwargs)
        
        # Start FFmpeg process with proper error handling
        # No preset option - using default libx264 settings which are reliable
        process_out = (
            ffmpeg_output
            .overwrite_output()
            .global_args("-loglevel", "warning")
            .run_async(pipe_stdin=True, pipe_stderr=True)
        )

        frame_bboxes = {}
        detect_missed = []
        bbox_centers = []
        bboxes = []
        if not quiet:
            logger.debug(
                f"total frames: {total_frames}, fps: {fps}, width: {width}, height: {height}"
            )
        for idx, frame in enumerate(
            tqdm(input_video_loader, total=total_frames, desc="Detect watermarks", disable=quiet)
        ):
            detection_result = self.detector.detect(frame)
            if detection_result["detected"]:
                frame_bboxes[idx] = { "bbox": detection_result["bbox"]}
                x1, y1, x2, y2 = detection_result["bbox"]
                bbox_centers.append((int((x1 + x2) / 2), int((y1 + y2) / 2)))
                bboxes.append((x1, y1, x2, y2))

            else:
                frame_bboxes[idx] = {"bbox": None}
                detect_missed.append(idx)
                bbox_centers.append(None)
                bboxes.append(None)
            # 10% - 50%
            if progress_callback and idx % 10 == 0:
                progress = 10 + int((idx / total_frames) * 40)
                progress_callback(progress)
        if not quiet:
            logger.debug(f"detect missed frames: {detect_missed}")
        if detect_missed:
            # 1. find the bkps of the bbox centers
            bkps = find_2d_data_bkps(bbox_centers)
            # add the start and end position, to form the complete interval boundaries
            bkps_full = [0] + bkps + [total_frames]
            # logger.debug(f"bkps intervals: {bkps_full}")

            # 2. calculate the average bbox of each interval
            interval_bboxes = get_interval_average_bbox(bboxes, bkps_full)
            # logger.debug(f"interval average bboxes: {interval_bboxes}")

            # 3. find the interval index of each missed frame
            missed_intervals = find_idxs_interval(detect_missed, bkps_full)
            # logger.debug(
            #     f"missed frame intervals: {list(zip(detect_missed, missed_intervals))}"
            # )

            # 4. fill the missed frames with the average bbox of the corresponding interval
            for missed_idx, interval_idx in zip(detect_missed, missed_intervals):
                if (
                    interval_idx < len(interval_bboxes)
                    and interval_bboxes[interval_idx] is not None
                ):
                    frame_bboxes[missed_idx]["bbox"] = interval_bboxes[interval_idx]
                    if not quiet:
                        logger.debug(f"Filled missed frame {missed_idx} with bbox:\n"
                        f" {interval_bboxes[interval_idx]}")
                else:
                    # if the interval has no valid bbox, use the previous and next frame to complete (fallback strategy)
                    before = max(missed_idx - 1, 0)
                    after = min(missed_idx + 1, total_frames - 1)
                    before_box = frame_bboxes[before]["bbox"]
                    after_box = frame_bboxes[after]["bbox"]
                    if before_box:
                        frame_bboxes[missed_idx]["bbox"] = before_box
                    elif after_box:
                        frame_bboxes[missed_idx]["bbox"] = after_box
        else:
            del bboxes
            del bbox_centers
            del detect_missed
        
        input_video_loader = VideoLoader(input_video_path)

        try:
            # Read stderr in background to prevent blocking
            stderr_lines = []
            stderr_queue = queue_module.Queue()
            
            def read_stderr():
                """Read FFmpeg stderr in background thread"""
                try:
                    if process_out.stderr:
                        for line in iter(process_out.stderr.readline, b''):
                            if line:
                                stderr_lines.append(line.decode('utf-8', errors='ignore'))
                                stderr_queue.put(line.decode('utf-8', errors='ignore'))
                except Exception as e:
                    logger.warning(f"Error reading FFmpeg stderr: {e}")
            
            stderr_thread = threading.Thread(target=read_stderr, daemon=True)
            stderr_thread.start()
            
            for idx, frame in enumerate(tqdm(input_video_loader, total=total_frames, desc="Remove watermarks", disable=quiet)):
                # Check if FFmpeg process is still alive (non-blocking check)
                if process_out.poll() is not None:
                    # Process has terminated unexpectedly
                    return_code = process_out.returncode
                    # Collect stderr output
                    stderr_output = '\n'.join(stderr_lines)
                    if not stderr_output:
                        # Try to get any remaining stderr
                        try:
                            remaining = process_out.stderr.read().decode('utf-8', errors='ignore') if process_out.stderr else ""
                            if remaining:
                                stderr_output = remaining
                        except:
                            pass
                    raise RuntimeError(
                        f"FFmpeg process terminated unexpectedly at frame {idx}/{total_frames} with return code {return_code}. "
                        f"Error: {stderr_output}"
                    )
                
                bbox = frame_bboxes[idx]["bbox"]
                if bbox is not None:
                    x1, y1, x2, y2 = bbox
                    mask = np.zeros((height, width), dtype=np.uint8)
                    mask[y1:y2, x1:x2] = 255
                    cleaned_frame = self.cleaner.clean(frame, mask)
                else:
                    cleaned_frame = frame
                
                # Write frame to FFmpeg pipe with error handling
                try:
                    process_out.stdin.write(cleaned_frame.tobytes())
                    process_out.stdin.flush()  # Flush to ensure data is written
                except BrokenPipeError as e:
                    # FFmpeg process closed the pipe (crashed or closed)
                    stderr_output = '\n'.join(stderr_lines)
                    if not stderr_output:
                        try:
                            remaining = process_out.stderr.read().decode('utf-8', errors='ignore') if process_out.stderr else ""
                            if remaining:
                                stderr_output = remaining
                        except:
                            pass
                    raise RuntimeError(
                        f"FFmpeg pipe broken at frame {idx}/{total_frames}. "
                        f"This usually means FFmpeg crashed. Error: {stderr_output}"
                    ) from e
                except OSError as e:
                    # Handle other OS-level errors (like process terminated)
                    if process_out.poll() is not None:
                        return_code = process_out.returncode
                        stderr_output = '\n'.join(stderr_lines)
                        raise RuntimeError(
                            f"FFmpeg process terminated at frame {idx}/{total_frames} with return code {return_code}. "
                            f"Error: {stderr_output}"
                        ) from e
                    raise RuntimeError(f"Error writing frame {idx} to FFmpeg: {e}") from e
                except Exception as e:
                    raise RuntimeError(f"Error writing frame {idx} to FFmpeg: {e}") from e

                # 50% - 95%
                if progress_callback and idx % 10 == 0:
                    progress = 50 + int((idx / total_frames) * 45)
                    progress_callback(progress)

            # Close stdin and wait for FFmpeg to finish
            process_out.stdin.close()
            
            # Wait for process to finish (poll with timeout to detect hangs)
            timeout_seconds = 300  # 5 minute timeout for final encoding
            start_time = time.time()
            return_code = None
            
            while return_code is None:
                return_code = process_out.poll()
                if return_code is not None:
                    break
                if time.time() - start_time > timeout_seconds:
                    logger.error(f"FFmpeg process did not finish within {timeout_seconds} seconds, killing...")
                    process_out.kill()
                    return_code = process_out.wait()
                    break
                time.sleep(0.1)  # Check every 100ms
            
            if return_code is None:
                return_code = process_out.wait()
            
            # Wait a bit for stderr thread to finish reading
            stderr_thread.join(timeout=2)
            
            # Collect final stderr output
            stderr_output = '\n'.join(stderr_lines)
            if not stderr_output and process_out.stderr:
                try:
                    remaining = process_out.stderr.read().decode('utf-8', errors='ignore')
                    if remaining:
                        stderr_output = remaining
                except:
                    pass
            
            if return_code != 0:
                raise RuntimeError(
                    f"FFmpeg encoding failed with return code {return_code}. "
                    f"Error: {stderr_output}"
                )
                
        except Exception as e:
            # Ensure process is terminated on error
            try:
                process_out.stdin.close()
            except:
                pass
            try:
                process_out.terminate()
                process_out.wait(timeout=5)
            except:
                try:
                    process_out.kill()
                except:
                    pass
            raise

        # 95% - 99%
        if progress_callback:
            progress_callback(95)

        self.merge_audio_track(input_video_path, temp_output_path, output_video_path)

        if progress_callback:
            progress_callback(99)

    def merge_audio_track(
        self, input_video_path: Path, temp_output_path: Path, output_video_path: Path
    ):
        logger.info("Merging audio track...")
        try:
            # Check if input video has audio
            probe = ffmpeg.probe(str(input_video_path))
            has_audio = any(stream.get('codec_type') == 'audio' for stream in probe.get('streams', []))
            
            if has_audio:
                video_stream = ffmpeg.input(str(temp_output_path))
                audio_stream = ffmpeg.input(str(input_video_path)).audio

                (
                    ffmpeg.output(
                        video_stream,
                        audio_stream,
                        str(output_video_path),
                        vcodec="copy",  # Copy video codec (no re-encoding)
                        acodec="aac",   # Encode audio to AAC
                        strict="experimental",  # Allow experimental codecs if needed
                    )
                    .overwrite_output()
                    .global_args("-loglevel", "warning")
                    .run(quiet=False, capture_stdout=True, capture_stderr=True)
                )
            else:
                # No audio track, just copy video to output
                logger.info("No audio track found, copying video only...")
                shutil.copy2(str(temp_output_path), str(output_video_path))
            
            # Clean up temporary file
            if temp_output_path.exists():
                temp_output_path.unlink()
            logger.info(f"Saved no watermark video at: {output_video_path}")
        except Exception as e:
            logger.error(f"Error merging audio: {e}")
            # If audio merge fails, at least save the video without audio
            if temp_output_path.exists():
                try:
                    shutil.copy2(str(temp_output_path), str(output_video_path))
                    logger.warning(f"Saved video without audio due to merge error: {output_video_path}")
                    temp_output_path.unlink()
                except Exception as copy_error:
                    logger.error(f"Failed to copy video file: {copy_error}")
                    raise RuntimeError(f"Failed to merge audio and save video: {e}") from e
            else:
                raise RuntimeError(f"Failed to merge audio: {e}") from e


if __name__ == "__main__":
    from pathlib import Path

    input_video_path = Path(
        "resources/19700121_1645_68e0a027836c8191a50bea3717ea7485.mp4"
    )
    output_video_path = Path("outputs/sora_watermark_removed.mp4")
    sora_wm = SoraWM()
    sora_wm.run(input_video_path, output_video_path)

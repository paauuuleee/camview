from __future__ import annotations
import time
from dataclasses import dataclass
from typing import Callable, TypeAlias
import cv2 as cv

Frame: TypeAlias = cv.typing.MatLike
"""
Type alias for a pixel array (Frame data)
"""

class CaptureFormat:
    MONO8 = "Mono8"
    BAYER_RG8 = "BayerRG8"
    RGB8 = "RGB8"

@dataclass
class Image:
    frame_id: int
    timestamp: int
    exposure_time: float
    capture_format: CaptureFormat
    frame: Frame

class Timer:
    """
    The Timer class measures the frame time and frame rate of a loop.
    """
    def __init__(self, frame_cap: int, epoch_callback: Callable[[float, float], None] | None):
        """
        **DO NOT USE!** The Timer constructor is only meant for internal usage.
        Use Timer.create(...) instead.
        """
        self._epoch_callback = epoch_callback
        self._epoch_frame_cap = frame_cap
        self._frame_count = 0
        self._start_time = 0.0
        self._epoch_start_time = 0.0
        self._frame_start_time = 0.0
        self._fps = 0.0
        self._avg_frame_time = 0.0
    
    @classmethod
    def create(cls, frames_per_epoch: int, epoch_callback: Callable[[float, float], None] | None = None) -> Timer:
        """
        Tries to calculate an average frame rate and frame time of an epoch of frames. Creates the Timer object. 
        Pass the desired frames per epoch and optionally a callback function for the end of an epoch that presents the frame rate and frame time in some way.
        
        :param frames_per_epoch: Number of frames that are in one epoch
        :type frames_per_epoch: int
        :param epoch_callback: Optinal callback function object that takes in frame rate and frame time
        :type epoch_callback: Callable[[float, float], None] | None
        :return: Configured Timer object
        :rtype: Timer
        """
        return cls(frames_per_epoch, epoch_callback)

    def start(self) -> None:
        """
        Starts the timer (ideally before the first frame).
        """
        self._start_time = time.time()
        self._epoch_start_time = self._start_time
        self._frame_time = self._start_time
        self._frame_count = 1
    
    def stop_and_reset(self) -> None:
        """
        Stops the timer.
        """
        self._start_time = 0.0
        self._epoch_start_time = 0.0
        self._frame_time = 0.0
        self._frame_count = 0
        self._fps = 0.0
        self._avg_frame_time = 0.0

    def frame(self) -> float:
        """
        Triggers the timer that one frame has been processed. Measures the frame time, updates the Timer, and if at the end of an epoch, calculates the frame rate and average frame time. 
        
        :return: Frame time of the current frame. 
        :rtype: float
        """
        curr_time = time.time()
        frame_time = curr_time - self._frame_start_time

        self._frame_count += 1
        self._check_epoch(curr_time)

        self.frame_start_time = curr_time
        return frame_time

    def _check_epoch(self, curr_time: float) -> None:
        """
        Helper function to calculate frame rate and frame time. Also calls the callback function. Only for internal usage.        
        """
        if self._frame_count == self._epoch_frame_cap:
            self._fps = self._epoch_frame_cap / (curr_time - self._epoch_start_time)
            self._avg_frame_time = (curr_time - self._epoch_start_time) / self._epoch_frame_cap
            if not self._epoch_callback == None:
                self._epoch_callback(self._fps, self._avg_frame_time)
            self._epoch_start_time = curr_time
            self._frame_count = 1
    
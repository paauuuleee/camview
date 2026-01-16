from __future__ import annotations
import time
from typing import Callable, TypeAlias
import cv2 as cv

Frame: TypeAlias = cv.typing.MatLike

class Timer:
    def __init__(self, frame_cap: int, epoch_callback: Callable[[float, float], None] | None):
        self._epoch_callback = epoch_callback
        self._epoch_frame_cap = frame_cap
        self._frame_count = 0
        self._start_time = 0.0
        self._epoch_start_time = 0.0
        self._frame_start_time = 0.0
        self._fps = 0.0
        self._avg_frame_time = 0.0
    
    @classmethod
    def create(cls, frames_per_epoch: int, epoch_callback: Callable[[float, float], None] | None) -> Timer:
        return cls(frames_per_epoch, epoch_callback)

    def start(self) -> None:
        self._start_time = time.time()
        self._epoch_start_time = self._start_time
        self._frame_time = self._start_time
        self._frame_count = 1
    
    def stop_and_reset(self) -> None:
        self._start_time = 0.0
        self._epoch_start_time = 0.0
        self._frame_time = 0.0
        self._frame_count = 0
        self._fps = 0.0
        self._avg_frame_time = 0.0

    def frame(self) -> float:
        curr_time = time.time()
        frame_time = curr_time - self._frame_start_time

        self._frame_count += 1
        self._check_epoch(curr_time)

        self.frame_start_time = curr_time
        return frame_time

    def _check_epoch(self, curr_time: float) -> None:
        if self._frame_count == self._epoch_frame_cap:
            self._fps = self._epoch_frame_cap / (curr_time - self._epoch_start_time)
            self._avg_frame_time = (curr_time - self._epoch_start_time) / self._epoch_frame_cap
            if not self._epoch_callback == None:
                self._epoch_callback(self._fps, self._avg_frame_time)
            self._epoch_start_time = curr_time
            self._frame_count = 1
    
    @property
    def frame_rate(self) -> float:
        return self._fps
    




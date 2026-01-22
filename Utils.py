from __future__ import annotations

# from Processors import Processor, ProcessFilter
from matplotlib import pyplot as plt

from dataclasses import dataclass
from typing import Callable, TypeAlias

import cv2
import numpy
import scipy

import time
import threading
import keyboard

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

Frame: TypeAlias = cv2.typing.MatLike
"""
Type alias for a pixel array (Frame data)
"""

def keyboard_signal(key: str) -> threading.Event:
    """
    Helper function to define a break condition on specific keyboard input to stop the acquisition loop..
        
    :param key: Keyboard input to set the break condition
    :type key: str
    :return: Thread signal that is set whenever specified keyboard input is detected.
    :rtype: threading.Event
    """
    signal = threading.Event()
    keyboard.add_hotkey(key, lambda: signal.set())
    return signal

class CaptureFormat:
    MONO8 = "Mono8"
    BAYER_RG8 = "BayerRG8"
    RGB8 = "RGB8"

@dataclass
class FrameData:
    frame_id: int
    timestamp: int
    exposure_time: float
    capture_format: CaptureFormat

def convert_bayer_mono(frame: Frame) -> Frame:
    return cv2.cvtColor(frame, cv2.COLOR_BayerRG2GRAY)
    
def convert_bayer_rgb(frame: Frame) -> Frame:
    return cv2.cvtColor(frame, cv2.COLOR_BayerRG2RGB)

def convert_rgb_mono(frame: Frame) -> Frame:
    return cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)

def expand_mono_rgb(frame: Frame) -> Frame:
    return cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)

def project(frame: Frame) -> tuple[numpy.array[int], numpy.array[int]]:
    hori_dist = numpy.sum(frame, 1)[::-1]
    vert_dist = numpy.sum(frame, 0)
    return hori_dist, vert_dist

@dataclass
class Gaussian:
    amplitude: float
    center: float
    sigma: float
    offset: float
    perr: float

def gauss_fit(distribution: numpy.array[int]) -> Gaussian:
    amp_guess = numpy.max(distribution)
    offset_guess = numpy.min(distribution)
    center_guess = distribution.tolist().index(amp_guess)

    indecies = numpy.arange(len(distribution))
    mean = numpy.average(indecies, weights=distribution)
    sigma_guess = numpy.sqrt(numpy.average((indecies - mean)**2, weights=distribution))

    def gauss(x: float, amplitude: float, center: float, sigma: float, offset: float) -> float:
        return amplitude * numpy.exp(-0.5 * ((x - center)**2 / sigma**2))+ offset

    params, cov_matrix = scipy.optimize.curve_fit(
        gauss, 
        xdata=indecies, 
        ydata=distribution, 
        p0=(
            amp_guess,
            center_guess,
            sigma_guess,
            offset_guess
        )
    )

    amplitude, center, sigma, offset= params
    perr = numpy.sqrt(numpy.diag(cov_matrix))
    return Gaussian(amplitude, center, sigma, offset, perr)

'''
def gauss_test() -> int:
    background = cv2.imread('I0T3.png')
    background_mono = cv2.cvtColor(background, cv2.COLOR_BGR2GRAY)

    processor = Processor.create(ProcessFilter.SUBSTRACT(background_mono), ProcessFilter.MEDIAN(3), ProcessFilter.THRESHOLD(30))
    
    frame = cv2.imread('I0T3-08082025152658-0.png')
    mono_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    processed_frame = processor.process(mono_frame)

    horiz_dist, vert_dist = project(processed_frame)
    horiz_gaussian = gauss_fit(horiz_dist)
    vert_gaussian = gauss_fit(vert_dist)

    def gauss(x: float, amplitude: float, center: float, sigma: float, offset: float) -> float:
        return amplitude * numpy.exp(-0.5 * ((x - center)**2 / sigma**2))+ offset

    horiz_x = numpy.linspace(0, len(horiz_dist))
    horiz_y = gauss(horiz_x, horiz_gaussian.amplitude, horiz_gaussian.center, horiz_gaussian.sigma, horiz_gaussian.offset)

    vert_x = numpy.linspace(0, len(vert_dist))
    vert_y = gauss(vert_x, vert_gaussian.amplitude, vert_gaussian.center, vert_gaussian.sigma, vert_gaussian.offset)

    _, (horiz, vert) = plt.subplots(1, 2, figsize=(10, 4))

    horiz.plot(horiz_dist)
    horiz.plot(horiz_x, horiz_y)
    horiz.set_title('Horizontal distribution')

    vert.plot(vert_dist)
    vert.plot(vert_x, vert_y)
    vert.set_title('Vertical distribution')

    plt.legend()
    plt.show()
'''
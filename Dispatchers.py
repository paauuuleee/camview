from __future__ import annotations
from abc import ABC, abstractmethod
from Cameras import Camera
from Processors import Processor
import cv2 as cv
import numpy as np
from Utils import Timer, Frame, Image
import keyboard
import threading
import pygame
import numpy
import scipy.optimize as so

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

class Dispatcher(ABC):
    """
    The Dispatcher interface describes the general structure of a consumer class. 
    It is the blue print for all classes that ultimately recieve processed images in a loop and evaluate or even display them to the screen.
    **IMPORTANT:** This is an abstract class (interface). Actual consumer classes are supposed to inherit the Dispatcher interface.
    """
    def __init__(self, cam: Camera, processor: Processor):
        """
        **DO NOT USE!** The Dispatcher constructor is only for internal usage.
        To create an object of a childclass of the Dispatcher interface use *Classname*.create(...).
        """
        self._cam = cam
        self._processor = processor
        self._timer = None

    @classmethod 
    def create(cls, cam: Camera, processor: Processor) -> Dispatcher:
        """
        Creates an object of a childclass of the Dispatcher interface. 
        Each consumer class needs a Camera object to acquire images form and a Processor object to process them properly.
        
        :param cam: Camera object to acquire image frames from
        :type cam: Camera
        :param processor: Processor object to process the image frames accordingly.
        :type processor: Processor
        :return: An object or a childclass of the Dispatcher interface
        :rtype: Dispatcher
        """
        return cls(cam, processor)


    
    def add_timer(self, timer: Timer) -> None:
        """
        Adds a timer to the cosumer object that can be used to evaluate the frame rate and average frame time of a acquisition, processing cycle. 
        The timer will automatically be triggered, when calling .next_frame().
        
        :param timer: Specified timer object to measure the frame rate and average frame time.
        :type timer: Timer
        """
        self._timer = timer
    
    def setup_and_begin(self, config = None) -> None:
        """
        Final setup of the camera image processing pipeline by specifying the desired pixel format and additional camera device settings.
        Then it starts the image acquisition of the camera.

        :param pixel_format: Desired image pixel format of the final frame.
        :type pixel_format: PixelFormat
        :param config: Camera config object (still unspecified)
        
        :raises PySpin.SpinnakerException: May fail to setup the camera and start acqusition.
        """
        self._cam.setup(config)
        self._cam.begin()
        if not self._timer == None:
            self._timer.start()

    def next_frame(self) -> tuple[Image, Frame, Frame]:
        """
        Acquires the frame from the pysical camera device and processes the frame data once according to the processing pipeline.
        Optinally if a timer object was configured prior it triggers the timer.frame() method to measure the frame time.

        :return: Processed frame
        :rtype: Frame
        """
        if not self._timer == None:
            self._timer.frame()
        raw_image = self._cam.acquire()
        mono_frame = self._processor.convert_color(raw_image)
        processed_frame = self._processor.process(mono_frame)
        return raw_image, mono_frame, processed_frame

    def end_and_cleanup(self) -> None:
        """
        Stops the image acquisition. Nessesary for cleanup

        :param self: Description
        """
        self._cam.end()
    
    @abstractmethod
    def dispatch(self) -> None:
        """
        Abstract method of the Dispatcher interface that must be implemented by the consumer childclasses of it. 
        This is supposed to contain the acqusition and processing loop.
        """
        pass

class Consumer(Dispatcher):
    def setup(self) -> pygame.Surface:
        size = (self._cam.descriptor.Width, self._cam.descriptor.Height)
        pygame.init()
        pygame.display.set_caption(f"CamView for {self._cam.descriptor.VendorName} {self._cam.descriptor.ModelName}")
        return pygame.display.set_mode(size)
        
    def dispatch(self) -> None:
        screen = self.setup()
        show_processed = False

        try:
            self.setup_and_begin()

            break_cond = keyboard_signal('space')
            switch = keyboard_signal('s')
            while not break_cond.is_set():
                if switch.is_set():
                    switch.clear()
                    show_processed = not show_processed
                try:
                    raw_image, mono_frame, processed_frame = self.next_frame()
                    gauss_fit(processed_frame)
                    
                    show_frame = processed_frame if show_processed else mono_frame
                    show_frame = cv.cvtColor(show_frame, cv.COLOR_GRAY2RGB)
                    show_frame = numpy.rot90(show_frame)
                    surface = pygame.surfarray.make_surface(show_frame)
                    screen.blit(surface, (0, 0))
                    pygame.display.flip()
                except Exception as ex:
                    print(f"Error: {ex}")
                    continue
        except Exception as ex:
            print(f"Error: {ex}")
        finally:
            self.end_and_cleanup()
            pygame.quit()

def projection(frame: Frame) -> tuple[list[int], list[int]]:
    hori_proj = np.sum(frame, 0)
    vert_proj = np.sum(frame, 1)
    return hori_proj, vert_proj

def gauss_fit(frame: Frame):
    hori_proj, vert_proj = projection(frame)

    def gauss(x: float, amplitude: float, center: float, sigma: float, offset: float) -> float:
        return amplitude * np.exp(-1 * ((x - center)**2 / 2 * sigma**2) + offset)

    amplitude_guess = np.max(hori_proj)
    center_guess = hori_proj.index(amplitude_guess)

    mean = 0.0
    for i, value in enumerate(hori_proj):
        mean += i * value
    meam /= len(hori_proj)

    sigma_guess = 0.0
    for i, value in enumerate(hori_proj):
        sigma_guess = (value - mean)**2
    sigma_guess = np.sqrt(sigma_guess / len(hori_proj))
    offset_guess = np.min(hori_proj)

    so.curve_fit()
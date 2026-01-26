from __future__ import annotations
from dataclasses import dataclass

from processor import Processor
from utils import DisplayMode
from camera import CameraConfig, Camera

from multiprocessing import Queue
from multiprocessing.synchronize import Event

@dataclass
class Channel:
    def __init__(
            self, 
            sig_term: Event, 
            sig_calc: Event, 
            sig_record: Event, 
            display_mode_queue: Queue, 
            processor_queue: Queue, 
            cam_config_queue: Queue, 
            sig_request_cam_config: Event, 
            cam_config_respond_queue: Queue):
        self._sig_term = sig_term
        self._sig_calc = sig_calc
        self._sig_record = sig_record
        self._display_mode_queue = display_mode_queue
        self._processor_queue = processor_queue
        self._cam_config_queue = cam_config_queue
        self._sig_request_cam_config = sig_request_cam_config
        self._cam_config_respond_queue = cam_config_respond_queue

    @classmethod
    def create(cls) -> Channel:
        sig_term = Event()
        sig_calc = Event()
        sig_record = Event()
        display_mode_queue = Queue(maxsize=1)
        processor_queue = Queue(maxsize=1)
        cam_config_queue = Queue(maxsize=1)
        sig_request_cam_config = Event()
        cam_config_respond_queue = Queue(maxsize=1)
        return cls(sig_term, sig_calc, sig_record, display_mode_queue, processor_queue, cam_config_queue, sig_request_cam_config, cam_config_respond_queue)
    
    @property
    def processor(self) -> Processor:
        return self._processor_queue.get(block=False)

    @processor.setter
    def processor(self, processor: Processor) -> None:
        self._processor_queue.put(processor)

    @property
    def display_mode(self) -> DisplayMode:
        return self._display_mode_queue.get(block=True)

    @display_mode.setter
    def display_mode(self, display_mode: DisplayMode) -> None:
        self._display_mode_queue.put(display_mode)

    def terminate(self) -> None:
        self._sig_term.set()

    def should_terminate(self) -> bool:
        return self._sig_term.is_set()

    def calculate(self) -> None:
        self._sig_calc.set()

    def stop_calculation(self) -> None:
        self._sig_record.clear()
        self._sig_calc.clear()

    def should_calculate(self) -> bool:
        self._sig_calc.is_set()

    def record(self) -> None:
        if not self._sig_calc.is_set():
            raise Exception("Did not start calculating the ray parameters")
        self._sig_record.set()

    def stop_recording(self) -> None:
        self._sig_record.clear()

    def should_record(self) -> bool:
        self._sig_record.is_set()

    def request_camera_config(self) -> CameraConfig:
        self._sig_request_cam_config.set()
        return self._cam_config_respond_queue.get(block=True)
    
    def sync_camera_config(self, camera: Camera) -> None:
        if self._sig_request_cam_config.is_set():
            self._cam_config_respond_queue.put(camera.config)

    @property
    def camera_config(self) -> CameraConfig:
        return self._cam_config_queue.get(block=False)

    @camera_config.setter
    def camera_config(self, camera_config: CameraConfig) -> None:
        return self._cam_config_queue.put(camera_config)
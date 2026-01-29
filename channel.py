from __future__ import annotations
from dataclasses import dataclass
from contextlib import contextmanager

from processor import Pipeline, FrameFilter
from utils import DisplayMode
from camera import CameraConfig, Camera

from multiprocessing import Queue
import multiprocessing as mp

@dataclass
class ExitMsg:
    success: bool
    message: str

@dataclass
class Channel:
    def __init__(
            self, 
            sig_term, 
            sig_calc, 
            sig_record,
            sig_save_subimage,
            display_mode_queue: Queue, 
            processor_queue: Queue, 
            cam_config_queue: Queue, 
            sig_request_cam_config, 
            cam_config_respond_queue: Queue):
        self._sig_term = sig_term
        self._sig_calc = sig_calc
        self._sig_record = sig_record
        self._sig_save_subimage = sig_save_subimage
        self._display_mode_queue = display_mode_queue
        self._processor_queue = processor_queue
        self._cam_config_queue = cam_config_queue
        self._sig_request_cam_config = sig_request_cam_config
        self._cam_config_respond_queue = cam_config_respond_queue
        self._exit_msg_lock = mp.Lock()
        self._exit_msg = ExitMsg(True, "")

    @classmethod
    def create(cls) -> Channel:
        sig_term = mp.Event()
        sig_calc = mp.Event()
        sig_record = mp.Event()
        sig_save_subimage = mp.Event()
        display_mode_queue = Queue(maxsize=1)
        processor_queue = Queue(maxsize=1)
        cam_config_queue = Queue(maxsize=1)
        sig_request_cam_config = mp.Event()
        cam_config_respond_queue = Queue(maxsize=1)

        return cls(
            sig_term, 
            sig_calc, 
            sig_record, 
            sig_save_subimage,
            display_mode_queue, 
            processor_queue, 
            cam_config_queue, 
            sig_request_cam_config, 
            cam_config_respond_queue
        )
    
    def recv_filters(self) -> Pipeline:
        return self._processor_queue.get(block=False)

    def send_filters(self, *filters: FrameFilter) -> None:
        self._processor_queue.put(filters)

    def recv_display_mode(self) -> DisplayMode:
        return self._display_mode_queue.get(block=False)

    def send_display_mode(self, display_mode: DisplayMode) -> None:
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
        return self._sig_calc.is_set()

    def record(self) -> None:
        if not self._sig_calc.is_set():
            raise Exception("Did not start calculating the ray parameters")
        self._sig_record.set()

    def stop_recording(self) -> None:
        self._sig_record.clear()

    def should_record(self) -> bool:
        return self._sig_record.is_set()
    
    def save_subimage(self) -> None:
        self._sig_save_subimage.set()

    def should_save_subimage(self) -> bool:
        should_save_subimage = self._sig_save_subimage.is_set()
        self._sig_save_subimage.clear()
        return should_save_subimage

    def request_camera_config(self) -> CameraConfig:
        self._sig_request_cam_config.set()
        return self._cam_config_respond_queue.get(block=True)
    
    def sync_camera_config(self, camera: Camera) -> None:
        if self._sig_request_cam_config.is_set():
            self._cam_config_respond_queue.put(camera.config)

    def recv_camera_config(self) -> CameraConfig:
        return self._cam_config_queue.get(block=False)

    def send_camera_config(self, camera_config: CameraConfig) -> None:
        return self._cam_config_queue.put(camera_config)
    
    @property
    def exit_msg(self) -> ExitMsg:
        with self._exit_msg_lock:
            return self._exit_msg
    
    @exit_msg.setter
    def exit_msg(self, exit_msg: ExitMsg) -> None:
        with self._exit_msg_lock:
            self._exit_msg = exit_msg

@contextmanager
def except_process(err_msg: str, channel: Channel):
    try:
        yield
    except Exception:
        channel.exit_msg = ExitMsg(False, err_msg)
        raise
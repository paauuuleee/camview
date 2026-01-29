from __future__ import annotations

from camera import Camera, CameraConfig
from processor import Processor
from context import Context
from channel import Channel, ExitMsg, except_process
import utils
from utils import Frame, FrameData, CaptureFormat, Capture, DisplayMode, DataRecord, except_continue, except_raise, Timer, HardwareTimer

from multiprocessing import Process
import pygame
import numpy
import cv2
import time
import csv

class Dispatch:
    def __init__(self, cam_name, process: Process, channel: Channel):
        self._cam_name = cam_name
        self._process = process
        self._channel = channel

    @classmethod
    def create(cls, cam_name: str, display: int = 0, config: CameraConfig | None = None):
        channel = Channel.create()
        process = Process(target=dispatch, args=(cam_name, channel, display, config))
        return cls(cam_name, process, channel)
    
    def start(self) -> None:
        self._process.start()
    
    def terminate(self) -> tuple[bool, str]:
        self._channel.terminate()
        self._process.join()
        return self._channel.exit_msg

    def set_processor(self, processor: Processor) -> None:
        self._channel.processor = processor

    def set_camera_config(self, config: CameraConfig) -> None:
        self._channel.send_camera_config(config)

    def get_camera_config(self) -> CameraConfig:
        return self._channel.request_camera_config()
    
    def set_display_mode(self, display_mode: DisplayMode) -> None:
        self._channel.send_display_mode(display_mode)

    def is_alive(self) -> bool:
        return self._process.is_alive()
    
    def get_exit_msg(self) -> ExitMsg:
        return self._channel.exit_msg
    
    @property
    def cam_name(self) -> str:
        return self._cam_name

def dispatch(cam_name: str, channel: Channel, display: int, config: CameraConfig | None) -> None:
    pygame.init()
    pygame.display.set_caption(f"CamView")
    screen = pygame.display.set_mode((1000, 800), display=display)
    context = Context.create()
    
    try:
        with except_process(f"Device not found", channel):
            camera = context.get_camera(cam_name)
        
        with except_process(f"Cannot setup camera", channel):
            camera.setup(auto_off=True)

        if config is not None:
            camera.config = config
        
        with except_process(f"Error during dispatch", channel):
            dispatch_run(screen, camera, channel)
        
    except:
        pass
    finally:
        pygame.quit()

def dispatch_run(screen: pygame.Surface, camera: Camera, channel: Channel) -> None:
    file = None
    writer = None
    
    processor = Processor.create()
    display_mode = DisplayMode.RGB
    
    timer = HardwareTimer.create(1000, lambda fps: print(f"{fps:.1f}"))
    with except_raise():
        camera.begin()

    while not channel.should_terminate():
        new_display_mode = sync_updates(channel, camera, display_mode, processor)
        if new_display_mode is not None: display_mode = new_display_mode

        try:
            frame_data, capture = capture_next_frame(camera, processor)
        except Exception as ex:
            print(f"Capture Error: {ex}")
            continue

        timer.frame(frame_data.timestamp)

        if channel.should_calculate():
            with except_continue("Gauss fit exception"):
                horiz_proj, vert_proj = utils.project(capture.processed)
                horiz_gaussian = utils.gauss_fit(horiz_proj)
                vert_gaussian = utils.gauss_fit(vert_proj)
                record = DataRecord.create(horiz_gaussian, vert_gaussian, frame_data)
                record_dict = record.asdict()

            if channel.should_record():
                if file is None:
                    file = open(utils.get_filename(camera.name), "w", newline="")
                    writer = csv.DictWriter(file, fieldnames=record_dict.keys())
                    writer.writeheader()
                writer.writerow(record_dict)
                file.flush()
        
        display_frame = get_display_frame(capture, display_mode)
        display_frame = numpy.rot90(display_frame)
        show_surface = pygame.surfarray.make_surface(display_frame)
        screen.blit(show_surface, (0, 0))
        pygame.display.flip()

        if channel.should_save_subimage():
            utils.save_subimage(camera.name, capture.rgb)

    camera.end()
    if file is not None:
        file.close()

def sync_updates(channel: Channel, camera: Camera, processor: Processor) -> DisplayMode | None:
    with except_continue():
        processor.updated_pipline(channel.recv_processor())

    with except_continue():
        camera.config = channel.recv_camera_config()

    channel.sync_camera_config(camera)

    with except_continue():
        return channel.recv_display_mode()    
    return None

def capture_next_frame(cam: Camera, processor: Processor) -> tuple[FrameData, Capture]:
    frame_data, frame = cam.acquire()

    rgb_frame: Frame
    mono_frame: Frame
    match frame_data.capture_format:
        case CaptureFormat.BAYER_RG8:
            rgb_frame = utils.convert_bayer_rgb(frame)
            mono_frame = utils.convert_bayer_mono(frame)
        case CaptureFormat.MONO8:
            rgb_frame = utils.expand_mono_rgb(frame)
            mono_frame = frame
        case CaptureFormat.RGB8:
            rgb_frame = frame
            mono_frame = utils.convert_rgb_mono(frame)

    processed_frame = processor.process(mono_frame)
    return frame_data, Capture(rgb_frame, mono_frame, processed_frame)

def get_display_frame(capture: Capture, display_mode: DisplayMode) -> Frame:
    match display_mode:
        case DisplayMode.RGB:
            return capture.rgb
        case DisplayMode.MONO:
            return utils.expand_mono_rgb(capture.mono)
        case DisplayMode.PROCESSED:
            return utils.expand_mono_rgb(capture.processed)
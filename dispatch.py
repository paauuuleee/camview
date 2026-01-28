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

def dispatch_run(screen: pygame.Surface, cam: Camera, channel: Channel) -> None:
    file = None
    writer = None
    processor = Processor.create()
    display_mode = DisplayMode.RGB
    timer = HardwareTimer.create(1000, lambda fps: print(f"{fps:.1f}"))
    with except_raise():
        cam.begin()

    while not channel.should_terminate():
       
        with except_continue():
            processor = channel.recv_processor()

        with except_continue():
            display_mode = channel.recv_display_mode()

        with except_continue():
            cam.config = channel.recv_camera_config()

        channel.sync_camera_config(cam)

        try:
            frame_data, capture = capture_next_frame(cam, processor)
        except Exception as ex:
            print(f"Capture Error: {ex}")
            continue

        if channel.should_calculate():
            with except_continue("Gauss fit exception"):
                horiz_proj, vert_proj = utils.project(capture.processed)
                horiz_gaussian = utils.gauss_fit(horiz_proj)
                vert_gaussian = utils.gauss_fit(vert_proj)
                record = DataRecord.create(horiz_gaussian, vert_gaussian, frame_data)
                record_dict = record.asdict()

            if channel.should_record():
                if file is None:
                    localtime = time.localtime()
                    file = open(f"./record/{cam.name}-{localtime.tm_year}{localtime.tm_mon:02d}{localtime.tm_mday:02d}-{localtime.tm_hour:02d}{localtime.tm_min:02d}.csv", "w")
                    writer = csv.DictWriter(file, fieldnames=record_dict.keys())
                    writer.writeheader()
                writer.writerow(record_dict)
                file.flush()
        
        show_frame: Frame
        match display_mode:
            case DisplayMode.NONE:
                show_frame = numpy.zeros((1000, 800, 3), numpy.uint8)
            case DisplayMode.RGB:
                show_frame = capture.rgb
            case DisplayMode.MONO:
                show_frame = utils.expand_mono_rgb(capture.mono)
            case DisplayMode.PROCESSED:
                show_frame = utils.expand_mono_rgb(capture.processed)
        show_frame = numpy.rot90(show_frame)
        show_surface = pygame.surfarray.make_surface(show_frame)
        screen.blit(show_surface, (0, 0))
        pygame.display.flip()
        
        timer.frame(frame_data.timestamp)
    
    cam.end()
    if file is not None:
        file.close()

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
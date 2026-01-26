from __future__ import annotations

from camera import Camera
from processor import Processor
from context import Context

import utils
from utils import Timer, Frame, FrameData, CaptureFormat, Capture, DisplayMode, except_continue
from ioc import Channel

import pygame
import numpy

class App:
    def __init__(self, context: Context):
        self._context = context

    @classmethod
    def init(cls) -> App:
        context = Context.create()
        return cls(context)
        
    def search_connected(self, read_config=True) -> None:
        self._connected = self._context.search_cams(read_config)

    def run(self) -> None:
        self.search_connected(read_config=True)
        
    def quit(self) -> None:
        self._context.release()

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

def window_init(display: int = 0) -> pygame.Surface:
    pygame.init()
    pygame.display.set_caption(f"CamView")
    return pygame.display.set_mode((1000, 800), display=display)

def window_quit() -> None:
    pygame.quit()

def dispatch(screen: pygame.Surface, cam: Camera, channel: Channel, timer: Timer | None = None) -> None:
    processor = Processor.create()
    display_mode = DisplayMode.RGB
    with except_continue("Error"):
        cam.setup()
        cam.config()
        cam.begin()
        
        timer.start()
        while not channel.should_terminate():
            with except_continue():
                processor = channel.processor

            with except_continue():
                display_mode = channel.display_mode

            with except_continue():
                cam.config = channel.camera_config
            
            channel.sync_camera_config(cam)

            try:
                frame_data, capture = capture_next_frame(cam, processor)
            except Exception as ex:
                print(f"Error: {ex}")
                continue

            if channel.should_calculate():
                with except_continue("Gauss fit exception"):
                    horiz_proj, vert_proj = utils.project(capture.processed)
                    horiz_gaussian = utils.gauss_fit(horiz_proj)
                    vert_gaussian = utils.gauss_fit(vert_proj)

                if channel.should_record():
                    pass
            
            show_frame: Frame
            match display_mode:
                case DisplayMode.NONE:
                    continue
                case DisplayMode.RGB:
                    show_frame = capture.rgb
                case DisplayMode.MONO:
                    show_frame = capture.mono
                case DisplayMode.PROCESSED:
                    show_frame = capture.processed
            show_frame = numpy.rot90(show_frame)
            show_surface = pygame.surfarray.make_surface(show_frame)
            screen.blit(show_surface, (0, 0))
            pygame.display.flip()

            if not timer == None:
                timer.frame()
    
    cam.end()
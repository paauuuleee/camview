from __future__ import annotations

from camera import Camera
from processor import Processor
from context import Context

import utils
from utils import Timer, Frame, FrameData, CaptureFormat, Capture

import threading
import pygame
import numpy

class Dispatch:
    def __init__(self, sig_term: threading.Event, dispatch_job: threading.Thread):
        self._sig_term = sig_term
        self._dispatch_job = dispatch_job
        
    @classmethod
    def create(cls, cam: Camera, processor: Processor, calculate: threading.Event, measure: threading.Event) -> Dispatch:
        def dispatch(cam: Camera, processor: Processor, calculate: threading.Event, measure: threading.Event, sig_term: threading.Event) -> None:
            while not sig_term.is_set():
                try:
                    frame_data, capture = capture_next_frame(cam, processor)
                except Exception as ex:
                    print(f"Error: {ex}")
                    continue

                if calculate.is_set():
                    try:
                        horiz_proj, vert_proj = utils.project(capture.processed)
                        horiz_gaussian = utils.gauss_fit(horiz_proj)
                        vert_gaussian = utils.gauss_fit(vert_proj)

                        if measure.is_set():
                            pass
                    except Exception as ex:
                        print(f"Gauss fit error: {ex}")

        sig_term = threading.Event()
        dispatch_job = threading.Thread(target=dispatch, args=(cam, processor, calculate, measure, sig_term))
        return cls(sig_term, dispatch_job)

    def start(self) -> None:
        self._dispatch_job.start()
    
    def terminate(self) -> None:
        self._sig_term.set()
        self._dispatch_job.join()

class App:
    def __init__(self, context: Context):
        self._context = context

    @classmethod
    def init(cls) -> App:
        context = Context.create()
        return cls(context)

    def _setup(self) -> None:
        pygame.init()
        pygame.display.set_caption(f"CamView")
        self._screen = pygame.display.set_mode((1000, 800), pygame.FULLSCREEN)
        
    def _search_connected(self, read_config=True) -> None:
        self._connected = self._context.search_cams(read_config)

    def start(self) -> None:
        self._setup()
        self._search_connected(read_config=True)
        
    def _quit(self) -> None:
        pygame.quit()
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

def app_init() -> pygame.Surface:
    pygame.init()
    pygame.display.set_caption(f"CamView")
    return pygame.display.set_mode((1000, 800))

def app_quit() -> None:
    pygame.quit()

def dispatch(screen: pygame.Surface, cam: Camera, processor: Processor, timer: Timer | None = None) -> None:
    break_cond = utils.keyboard_signal('space')
    try:
        cam.setup()
        cam.begin()

        timer.start()
        while not break_cond.is_set():
            try:
                frame_data, capture = capture_next_frame(cam, processor)
            except Exception as ex:
                print(f"Error: {ex}")
                continue

            try:
                horiz_proj, vert_proj = utils.project(capture.processed)
                # horiz_gaussian = utils.gauss_fit(horiz_proj)
                # vert_gaussian = utils.gauss_fit(vert_proj)
            except Exception as ex:
                print(f"Gauss fit error: {ex}")
            
            
            show_frame = numpy.rot90(capture.rgb)
            show_surface = pygame.surfarray.make_surface(show_frame)
            screen.blit(show_surface, (0, 0))
            pygame.display.flip()

            if not timer == None:
                timer.frame()
    except Exception as ex:
        print(f"Error: {ex}")
    finally:
        cam.end()
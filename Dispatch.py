from __future__ import annotations

from Cameras import Camera
from Processors import Processor

import Utils as utils
from Utils import Timer, Frame, FrameData, CaptureFormat

import pygame
import numpy

def capture_next_frame(cam: Camera, processor: Processor) -> tuple[FrameData, Frame, Frame, Frame]:
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
    return frame_data, rgb_frame, mono_frame, processed_frame

def app_init() -> pygame.Surface:
    pygame.init()
    pygame.display.set_caption(f"CamView")
    return pygame.display.set_mode((1000, 800))

def app_quit() -> None:
    pygame.quit()

def dispatch(screen: pygame.Surface, cam: Camera, processor: Processor, timer: Timer | None = None) -> None:
    timer.start()
    break_cond = utils.keyboard_signal('space')
    try:
        cam.setup()
        cam.begin()

        while not break_cond.is_set():
            try:
                frame_data, rgb_frame, mono_frame, processed_frame = capture_next_frame(cam, processor)
            except Exception as ex:
                print(f"Error: {ex}")
                continue

            try:
                horiz_proj, vert_proj = utils.project(processed_frame)
                # horiz_gaussian = utils.gauss_fit(horiz_proj)
                # vert_gaussian = utils.gauss_fit(vert_proj)
            except Exception as ex:
                print(f"Gauss fit error: {ex}")
            
            
            show_frame = numpy.rot90(rgb_frame)
            show_surface = pygame.surfarray.make_surface(show_frame)
            screen.blit(show_surface, (0, 0))
            pygame.display.flip()

            if not timer == None:
                timer.frame()
    except Exception as ex:
        print(f"Error: {ex}")
    finally:
        cam.end()
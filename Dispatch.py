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
    return pygame.display.set_mode((0, 0), pygame.FULLSCREEN)

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

            horiz_proj, vert_proj = utils.project(processed_frame)
            horiz_gaussian = utils.gauss_fit(horiz_proj)
            vert_gaussian = utils.gauss_fit(vert_proj)

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

'''
class Consumer:
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

            break_cond = utils.keyboard_signal('space')
            switch = utils.keyboard_signal('s')
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
'''
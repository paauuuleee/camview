from __future__ import annotations
from Utils import Frame
from typing import TypeAlias, Callable
import cv2 as cv

class PixelFormat:
    RGB = 0
    BGR = 1

FrameFilter: TypeAlias = Callable[[Frame, PixelFormat], Frame]

class ProcessFilter:
    @staticmethod
    def MEDIAN(frame: Frame, format: PixelFormat) -> Frame:
        pass 

class Processor:
    def __init__(self, pixel_format: PixelFormat, conversion_code: int, filters: tuple[FrameFilter, ...]):
        self._format = pixel_format
        self._conversion_code = conversion_code
        self._filters = filters

    @classmethod
    def create(cls, pixel_format: PixelFormat, *filters: FrameFilter) -> Processor:
        conversion_code = cls._get_conversion_code(pixel_format)
        return cls(pixel_format, conversion_code, filters)
    
    @staticmethod
    def _get_conversion_code(pixel_format: PixelFormat) -> int:
        match pixel_format:
            case PixelFormat.RGB: return cv.COLOR_BayerBG2RGB
            case PixelFormat.BGR: return cv.COLOR_BayerBG2BGR

    def process(self, bayer_frame: Frame) -> Frame:
        frame = cv.cvtColor(bayer_frame, self._conversion_code)
        for filter in self._filters:
            frame = filter(frame, self._format)
        return frame
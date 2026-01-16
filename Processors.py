from __future__ import annotations
from Utils import Frame
from typing import TypeAlias, Callable
import cv2 as cv

class PixelFormat:
    RGB = 0
    BGR = 1

FrameFilter: TypeAlias = Callable[[Frame], Frame]

class ProcessFilter:
    @staticmethod
    def MEDIAN(ksize) -> FrameFilter:
        return lambda frame: cv.medianBlur(frame, ksize)

class Processor:
    def __init__(self, conversion_code: int, filters: tuple[FrameFilter, ...]):
        self._conversion_code = conversion_code
        self._filters = filters

    @classmethod
    def create(cls, pixel_format: PixelFormat, *filters: FrameFilter) -> Processor:
        conversion_code = cls._get_conversion_code(pixel_format)
        return cls(conversion_code, filters)
    
    @staticmethod
    def _get_conversion_code(pixel_format: PixelFormat) -> int:
        match pixel_format:
            case PixelFormat.RGB: return cv.COLOR_BayerBGR2RGB
            case PixelFormat.BGR: return -1

    def process(self, bayer_frame: Frame) -> Frame:
        frame = cv.cvtColor(bayer_frame, cv.COLOR_BayerBG2BGR)
        for filter in self._filters:
            frame = filter(frame)
        if self._conversion_code == -1:
            return frame
        return cv.cvtColor(frame, self._conversion_code)
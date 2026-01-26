from __future__ import annotations
from Utils import Frame
from typing import TypeAlias, Callable
import cv2

'''
class PixelFormat:
    """
    Configuration class for the resulting pixel format after processing the frame.
    """
    RGB = 0
    """
    Pixel format of (red - uint8, green - uint8, blue - uint8)
    """
    BGR = 1
    """
    Pixel format of (blue - uint8, green - uint8, red - uint8)
    """
'''

FrameFilter: TypeAlias = Callable[[Frame], Frame]
"""
Type alias for a filter function that processes the frame data.
"""

class ProcessFilter:
    """
    Enumeration over already available filter functions.
    """
    @staticmethod
    def MEDIAN(ksize: int) -> FrameFilter:
        """
        Returns a FrameFilter function objet that applys a median filter with specified kernal size.
        
        :param ksize: Kernal size for the median filter.
        :type: int
        :return: Returns the FrameFilter function object.
        :rtype: FrameFilter
        """
        return lambda frame: cv2.medianBlur(frame, ksize)
    
    def SUBSTRACT(sub: Frame) -> FrameFilter:
        return lambda frame: cv2.subtract(frame, sub)
    
    def CROP(width: int, height: int, offset_x: int, offset_y: int) -> FrameFilter:
        return lambda frame: frame[offset_y:offset_y + height, offset_x:offset_x + width]
    
    def THRESHOLD(value: int) -> FrameFilter:
        def threshold(frame: Frame, value: int) -> Frame:
            frame[frame < value] = 0
            return frame
        return lambda frame: threshold(frame, value)

class Processor:
    def __init__(self, filters: tuple[FrameFilter, ...]):
        """
        **DO NOT USE!** Constructor for Processor class is only for internal usage.
        Use Processor.create(...) instead
        """
        self._filters = filters

    @classmethod
    def create(cls, *filters: FrameFilter) -> Processor:
        """
        Takes a variadic amount of FrameFilter function objects to be subsequently applied onto a provided image frame.
        
        :param filters: Pass as many FrameFilter functions as you like.
        :type filters: FrameFilter
        :return: Processor object with initialized filter pipeline.
        :rtype: Processor
        """
        return cls(filters)
    
    def process(self, frame: Frame) -> Frame:
        for filter in self._filters:
            frame = filter(frame)
        return frame
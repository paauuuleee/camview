from context import Context
from dispatch import Dispatch, DisplayMode
from camera import CameraConfig

import PySpin
import keyboard
import sys

def main() -> int:
    context = Context.create()

    dispatch = Dispatch.create("I0T2", 1)
    dispatch.start()

    keyboard.wait('space')
    dispatch.set_display_mode(DisplayMode.PROCESSED)

    keyboard.wait('space')
    dispatch.terminate()

    context.release()
    return 0

if __name__ == "__main__":
    sys.exit(main())
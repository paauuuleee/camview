import sys
from Contexts import Context
from Processors import Processor, ProcessFilter
from Dispatch import dispatch, app_init, app_quit
from Utils import Timer

def timer_callback(fps: float, _: float) -> None:
    print(f"Frame rate: {fps:.1f} FPS")

def main() -> int:
    screen = app_init()
    context = Context.create()

    try:
        camera = context.get_camera(1)
    except Exception as ex:
        print(f"CamView Error: {ex}")
        return 1
    
    processor = Processor.create(
        ProcessFilter.MEDIAN(3), 
        ProcessFilter.THRESHOLD(10)
    )

    timer = Timer.create(1000, timer_callback)
    
    dispatch(screen, camera, processor, timer)
    
    context.release()
    app_quit()
    return 0

if __name__ == "__main__":
    sys.exit(main())
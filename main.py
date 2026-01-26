import sys
from context import Context
from processor import Processor, ProcessFilter
from app import dispatch, app_init, app_quit
from utils import Timer
import multiprocessing as mp

def timer_callback(fps: float, _: float) -> None:
    print(f"Frame rate: {fps:.1f} FPS")

def fork():
    p1 = mp.Process(target=main)
    p1.start()
    p1.join()

def main() -> int:
    screen = app_init()
    context = Context.create()
    connected = context.search_cams(True)

    print(f"{connected}")

    try:
        camera = context.get_camera("I0T2")
    except Exception as ex:
        print(f"CamView Error: {ex}")
        return 1
    
    processor = Processor.create(
        ProcessFilter.MEDIAN(3), 
        ProcessFilter.THRESHOLD(10)
    )

    timer = Timer.create(100, timer_callback)
    mp.Event

    dispatch(screen, camera, processor, timer)

    camera.deinit()
    context.release()
    app_quit()
    return 0

if __name__ == "__main__":
    sys.exit(fork())
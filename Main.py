import sys
from Contexts import Context
from Processors import Processor, ProcessFilter
from Dispatchers import Consumer
from Utils import Timer

def timer_callback(fps: float, _: float) -> None:
    print(f"Frame rate: {fps:.1f} FPS")

def main() -> int:
    context = Context.create()

    try:
        cameras = context.get_cameras()
    except Exception as ex:
        print(f"CamView Error: {ex}")
        return 1
    
    processor = Processor.create(ProcessFilter.MEDIAN(3), ProcessFilter.THRESHOLD(10))
    consumer = Consumer.create(cameras[0], processor)
    consumer.add_timer(Timer.create(1000, timer_callback))
    consumer.dispatch()
    
    context.release()
    return 0

if __name__ == "__main__":
    sys.exit(main())
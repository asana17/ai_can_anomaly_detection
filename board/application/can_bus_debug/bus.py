"""Send one frame from the USB-CAN adapter on macOS and print the frames other nodes send.

    python3 -m board.application.can_bus_debug.bus

The frame has ID 0x18FEF200 and eight bytes of 0x11. Frames are printed until Ctrl-C.
On Ubuntu `cansend` and `candump` do the same.
"""

import threading
import time

from board.can_adapter import GsUsbAdapter, read_frames

CAN_ID = 0x18FEF200
DATA = bytes([0x11] * 8)


def main():
    echoes = [0]
    stop = threading.Event()
    adapter = GsUsbAdapter()
    reader = threading.Thread(target=read_frames, args=(adapter, stop, echoes))
    reader.start()
    try:
        adapter.send(CAN_ID, DATA)
        print(f"sent {CAN_ID:X}, Ctrl-C to stop", flush=True)
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()
        reader.join()
        adapter.close()
    print(f"echoed {echoes[0]}")


if __name__ == "__main__":
    main()

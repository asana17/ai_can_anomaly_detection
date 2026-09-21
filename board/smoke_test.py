"""Prepare, flash and verify the fixed board smoke test over ST-LINK UART."""

import argparse
import glob
import os
from pathlib import Path
import select
import subprocess
import sys
import termios
import time
import tty

APPLICATION = "model_check_from_flash"
EXPECTED_UART = ("model: processed 80/80", "dropped 0, errors 0")
TIMEOUT_SECONDS = 15
HERE = Path(__file__).resolve().parent


def uart_port(given):
    if given:
        return Path(given).expanduser()
    ports = sorted(glob.glob("/dev/cu.usbmodem*"))
    if len(ports) != 1:
        raise SystemExit(f"expected one ST-LINK UART, found {len(ports)}: {ports}")
    return Path(ports[0])


def open_uart(path):
    fd = os.open(path, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
    tty.setraw(fd)
    settings = termios.tcgetattr(fd)
    settings[4] = termios.B115200
    settings[5] = termios.B115200
    termios.tcsetattr(fd, termios.TCSANOW, settings)
    termios.tcflush(fd, termios.TCIFLUSH)
    return fd


def read_uart(fd):
    received = bytearray()
    deadline = time.monotonic() + TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        ready, _, _ = select.select([fd], [], [], 0.5)
        if not ready:
            continue
        chunk = os.read(fd, 4096)
        received.extend(chunk)
        sys.stdout.buffer.write(chunk)
        sys.stdout.buffer.flush()
        text = received.decode("utf-8", "replace")
        if all(expected in text for expected in EXPECTED_UART):
            return
    text = received.decode("utf-8", "replace")
    missing = [expected for expected in EXPECTED_UART if expected not in text]
    raise SystemExit(f"UART smoke test timed out; missing: {missing}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_dir", type=Path)
    parser.add_argument("--port", type=Path)
    parser.add_argument("--config", type=Path, default=HERE / "flash.json")
    args = parser.parse_args()

    project_dir = args.project_dir.expanduser().resolve()
    subprocess.run([sys.executable, "-m", "board.prepare", str(project_dir), APPLICATION],
                   check=True)
    port = uart_port(args.port)
    print(f"UART: {port} at 115200 baud", flush=True)
    fd = open_uart(port)
    try:
        subprocess.run([sys.executable, str(HERE / "flash.py"), str(project_dir),
                        "--config", str(args.config.expanduser())], check=True)
        read_uart(fd)
    finally:
        os.close(fd)
    print("\nboard smoke test passed")


if __name__ == "__main__":
    main()

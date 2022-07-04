# -*- coding: utf-8 -*-
"""
Created June 2022
Niklas Österlund
"""
import logging
import signal
from qr_attendance_logger import QRAttendanceLogger

# set up logging to file
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)


def handler(signum, frame):
    print("Ctrl-c was pressed")
    exit(1)


if __name__ == "__main__":
    logger = QRAttendanceLogger()
    signal.signal(signal.SIGINT, handler)
    print(f"Logger started, temp dir: {logger.temp_dir}/")
    print("Press Ctrl-c to exit")
    count = 0
    while True:
        text = input("awaiting input: ").strip()
        logger.log(text)

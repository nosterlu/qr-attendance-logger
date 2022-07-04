# -*- coding: utf-8 -*-
"""
QR attendance logger

Default connection string to azure container will be read from environment
variable.

QR_LOGGER_ACCOUNT_NAME

If not found, it will fall back on these two

QR_LOGGER_ACCOUNT_NAME
QR_LOGGER_SAS_TOKEN

Container name is set to "qr-attendance" as standard

Files will be stored in Azure as

year=yyyy/month=mm/[logname].log
..
.

If failed attempt will at least write in a tempfile

Will regularly try and connect to backend again and try and resend

Created June 2022
Niklas Österlund
"""
import os
import threading
import logging

from time import sleep
from datetime import datetime
from dateutil import parser
from pathlib import Path
from queue import Queue as _Queue
from appdirs import AppDirs

from ._version import __version__
from .qr_loggers import AzureLogger


class QRAttendanceLogger(object):
    def __init__(self, QR_Logger=AzureLogger):
        self.logger = logging.getLogger("qr_attendance_logger")
        self._QR_Logger = QR_Logger()
        # tempdir used if backend logger fails
        self.temp_dir = AppDirs("QR-attendance-logger").user_data_dir
        self.temp_file = f"{self.temp_dir}/failed_attendance.log"
        if os.path.isfile(self.temp_file):
            self.logger.warning(f"failed attempts exists in {self.temp_file}")
        self._q = _Queue()
        # Turn-on the worker thread.
        self.worker_thread = threading.Thread(
            target=self.handle_queue, daemon=True
        ).start()

    def log(self, text):
        """
        puts a new message in the _q
        """
        self._q.put(LogItem(datetime.today(), text))

    def handle_queue(self):
        # first_time = True
        while True:
            message = self._q.get()
            # we have a new message, see if we can append
            # failed logs (if any) also
            self._requeue_tempfile()
            y, m, d, *kwargs = message["timestamp"].timetuple()
            folder = f"year={y}/month={str(m).zfill(2)}"
            blob_name = f"{folder}/attendance.log"
            # write with tab for parsing
            text = f"{message['timestamp']}\t{message['text']}\n"
            try:
                # if first_time:
                #     first_time = False
                #     raise NameError("ERrrrrror")
                self._QR_Logger.log(text, blob_name=blob_name)
                self.logger.debug(f"Finished {message}")
            except Exception:
                self.logger.warning(f"Failed {message}, will attempt later")
                self._log_to_tempfile(text)
            self._q.task_done()
            sleep(0.3)

    def _requeue_tempfile(self):
        if os.path.isfile(self.temp_file):
            lines_added = 0
            with open(self.temp_file, "r") as f:
                for line in f.readlines():
                    if line == "":
                        continue
                    m = line.split("\t")
                    try:
                        timestamp = parser.parse(m[0])
                        message = LogItem(timestamp, m[1].replace("\n", ""))
                        lines_added += 1
                        self._q.put(message)
                    except Exception:
                        self.logger.warning(f"could not parse line {line}")
            os.remove(self.temp_file)
            self.logger.info("readded {lines_added} from previously failed attempts")

    def _log_to_tempfile(self, text):
        # make sure folder exists
        Path(self.temp_dir).mkdir(parents=True, exist_ok=True)
        with open(self.temp_file, "a") as f:
            f.write(text)


class LogItem(dict):
    def __init__(self, timestamp, text):
        self["timestamp"] = timestamp
        self["text"] = text

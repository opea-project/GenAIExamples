# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import base64
import logging
import logging.handlers
import os
import sys
from pathlib import Path

import cv2
from moviepy.video.io.VideoFileClip import VideoFileClip

LOGDIR = "."

server_error_msg = "**NETWORK ERROR DUE TO HIGH TRAFFIC. PLEASE REGENERATE OR REFRESH THIS PAGE.**"
moderation_msg = "YOUR INPUT VIOLATES OUR CONTENT MODERATION GUIDELINES. PLEASE TRY AGAIN."

handler = None
save_log = False


def build_logger(logger_name, logger_filename):
    global handler

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Set the format of root handlers
    if not logging.getLogger().handlers:
        logging.basicConfig(level=logging.INFO)
    logging.getLogger().handlers[0].setFormatter(formatter)

    # Redirect stdout and stderr to loggers
    stdout_logger = logging.getLogger("stdout")
    stdout_logger.setLevel(logging.INFO)
    sl = StreamToLogger(stdout_logger, logging.INFO)
    sys.stdout = sl

    stderr_logger = logging.getLogger("stderr")
    stderr_logger.setLevel(logging.ERROR)
    sl = StreamToLogger(stderr_logger, logging.ERROR)
    sys.stderr = sl

    # Get logger
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)

    # Add a file handler for all loggers
    if save_log and handler is None:
        os.makedirs(LOGDIR, exist_ok=True)
        filename = os.path.join(LOGDIR, logger_filename)
        handler = logging.handlers.TimedRotatingFileHandler(filename, when="D", utc=True)
        handler.setFormatter(formatter)

        for name, item in logging.root.manager.loggerDict.items():
            if isinstance(item, logging.Logger):
                item.addHandler(handler)

    return logger


class StreamToLogger(object):
    """Fake file-like stream object that redirects writes to a logger instance."""

    def __init__(self, logger, log_level=logging.INFO):
        self.terminal = sys.stdout
        self.logger = logger
        self.log_level = log_level
        self.linebuf = ""

    def __getattr__(self, attr):
        return getattr(self.terminal, attr)

    def write(self, buf):
        temp_linebuf = self.linebuf + buf
        self.linebuf = ""
        for line in temp_linebuf.splitlines(True):
            # From the io.TextIOWrapper docs:
            #   On output, if newline is None, any '\n' characters written
            #   are translated to the system default line separator.
            # By default sys.stdout.write() expects '\n' newlines and then
            # translates them so this is still cross platform.
            if line[-1] == "\n":
                self.logger.log(self.log_level, line.rstrip())
            else:
                self.linebuf += line

    def flush(self):
        if self.linebuf != "":
            self.logger.log(self.log_level, self.linebuf.rstrip())
        self.linebuf = ""


def maintain_aspect_ratio_resize(image, width=None, height=None, inter=cv2.INTER_AREA):
    # Grab the image size and initialize dimensions
    dim = None
    (h, w) = image.shape[:2]

    # Return original image if no need to resize
    if width is None and height is None:
        return image

    # We are resizing height if width is none
    if width is None:
        # Calculate the ratio of the height and construct the dimensions
        r = height / float(h)
        dim = (int(w * r), height)
    # We are resizing width if height is none
    else:
        # Calculate the ratio of the width and construct the dimensions
        r = width / float(w)
        dim = (width, int(h * r))

    # Return the resized image
    return cv2.resize(image, dim, interpolation=inter)


# function to split video at a timestamp
def split_video(
    video_path,
    timestamp_in_ms,
    output_video_path: str = "./public/splitted_videos",
    output_video_name: str = "video_tmp.mp4",
    play_before_sec: int = 5,
    play_after_sec: int = 5,
):
    timestamp_in_sec = int(timestamp_in_ms) / 1000
    # create output_video_name folder if not exist:
    Path(output_video_path).mkdir(parents=True, exist_ok=True)
    output_video = os.path.join(output_video_path, output_video_name)
    with VideoFileClip(video_path) as video:
        duration = video.duration
        start_time = max(timestamp_in_sec - play_before_sec, 0)
        end_time = min(timestamp_in_sec + play_after_sec, duration)
        new = video.subclip(start_time, end_time)
        new.write_videofile(output_video, audio_codec="aac")
    return output_video


def delete_split_video(video_path):
    if os.path.exists(video_path):
        os.remove(video_path)
        return True
    else:
        print("The file does not exist")
        return False


def convert_img_to_base64(image):
    "Convert image to base64 string"
    _, buffer = cv2.imencode(".png", image)
    encoded_string = base64.b64encode(buffer)
    return encoded_string.decode("utf-8")


def get_b64_frame_from_timestamp(video_path, timestamp_in_ms, maintain_aspect_ratio: bool = False):
    print(f"video path: {video_path}")
    vidcap = cv2.VideoCapture(video_path)
    vidcap.set(cv2.CAP_PROP_POS_MSEC, int(timestamp_in_ms))
    success, frame = vidcap.read()
    if success:
        if maintain_aspect_ratio:
            frame = maintain_aspect_ratio_resize(frame, height=350)
        b64_img_str = convert_img_to_base64(frame)
        return b64_img_str
    return None

import time

import cv2
import os
import platform
import threading

from tkinter import filedialog

from backend.video.video_source import VideoSource, DEMO_FILE_PATH
from backend.parameter_settings import VIDEO_FEED_SETTINGS


class VideoFeed:
    """Class for managing video feeds.

    This class provides functionality for selecting a video source and fetching
    video frames with an optional rescaling.
    """
    def __init__(self, video_source=VideoSource.DEMO, settings=VIDEO_FEED_SETTINGS):
        """
        Create a video feed.

        :param video_source: the video source
        :param settings: the settings
        """
        self.video_source = video_source
        self.settings = settings
        self.looping_possible = False
        self.video_capture = None
        self.fps = self.settings.get_value('DefaultFPS')
        self.latest_frame = None
        self.is_running = None
        self.thread = None

    def initialize(self):
        """
        Initialize the video feed.

        :return: True if the initialization was successful, False otherwise
        """
        self.is_running = False
        self.thread = threading.Thread(
            target=self._load_frames,
            daemon=True
        )

        if self.video_source == VideoSource.WEBCAM:
            try:
                if platform.system() == 'Windows':
                    self.video_capture = cv2.VideoCapture(0, cv2.CAP_DSHOW)
                else:
                    self.video_capture = cv2.VideoCapture(0)
            except Exception as e:
                print(e)
                return False
            self.looping_possible = False
            return True
        elif self.video_source == VideoSource.FILE:
            file_path = filedialog.askopenfilename(
                initialdir=os.getcwd(),
                filetypes=[
                    ('Video files', ('.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm'))
                ]
            )
            if file_path == '' or file_path is None:
                print('No file was selected. Stopping execution.')
                return False
            self.video_capture = cv2.VideoCapture(file_path)
            self.fps = self.video_capture.get(cv2.CAP_PROP_FPS)
            self.looping_possible = True
            return True
        elif self.video_source == VideoSource.DEMO:
            file_path = os.path.join(os.getcwd(), DEMO_FILE_PATH)
            if not os.path.exists(file_path):
                print('The file does not exist. Stopping execution.')
                return False
            self.video_capture = cv2.VideoCapture(file_path)
            self.fps = self.video_capture.get(cv2.CAP_PROP_FPS)
            self.looping_possible = True
            return True
        else:
            return False

    def run(self):
        """
        Start the video feed.

        :return: True if starting the feed is successful, False otherwise
        """
        self.is_running = True
        self.thread.start()

        return True

    def halt(self):
        """
        Halt the video feed.

        :return: True if halting the video was successful, False otherwise
        """
        self.is_running = False
        self.thread.join()

        return True

    def get_frame_width(self):
        """
        Get the video feed frame width.

        :return: the frame width
        """
        return self.video_capture.get(cv2.CAP_PROP_FRAME_WIDTH)

    def get_frame_height(self):
        """
        Get the video feed frame height.

        :return: the frame height
        """
        return self.video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT)

    def get_latest_frame(self):
        """
        Get the latest frame provided by the video feed.

        :return: the latest frame
        """
        return self.latest_frame

    def _load_frames(self):
        """
        Loop that updates the latest frame of the video feed.
        """
        time_between_frames = 1 / self.fps
        if self.settings.get_value('LoopingEnabled') and self.looping_possible:
            total_frame_count = self.video_capture.get(cv2.CAP_PROP_FRAME_COUNT)
            video_start_time = time.time()
            while self.is_running:
                expected_frame_number = int(self.fps * (time.time() - video_start_time))
                if expected_frame_number >= total_frame_count:
                    video_start_time = time.time()
                    expected_frame_number = 0
                self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, expected_frame_number)

                _, frame = self.video_capture.read()
                latest_frame_timestamp = time.time()
                self.latest_frame = cv2.resize(
                    frame,
                    (-1, -1),
                    fx=self.settings.get_value('ScalingFactor'),
                    fy=self.settings.get_value('ScalingFactor')
                )
                sleep_time = (time.time() - latest_frame_timestamp) % time_between_frames
                if sleep_time > 0:
                    time.sleep(sleep_time)
        else:
            while self.is_running:
                _, frame = self.video_capture.read()
                latest_frame_timestamp = time.time()
                self.latest_frame = cv2.resize(
                    frame,
                    (-1, -1),
                    fx=self.settings.get_value('ScalingFactor'),
                    fy=self.settings.get_value('ScalingFactor')
                )
                sleep_time = time_between_frames - (time.time() - latest_frame_timestamp)
                if sleep_time > 0:
                    time.sleep(sleep_time)

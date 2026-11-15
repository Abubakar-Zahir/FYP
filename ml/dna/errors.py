"""Extraction errors, kept apart from extract.py so callers can catch them without OpenCV installed."""


class UnreadableVideo(ValueError):
    pass


class VideoTooLong(ValueError):
    pass

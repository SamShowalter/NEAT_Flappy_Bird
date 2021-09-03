import skvideo.io
import numpy as np
from PIL import Image
from interestingness_xdrl.util.image import fade_image, resize_image_canvas, get_max_size

__author__ = 'Pedro Sequeira'
__email__ = 'pedro.sequeira@sri.com'


def save_video(buffer, video_path, fps=22.5, crf=18, verbosity=1, verify_input=False, color=0):
    """
    Saves the sequence of given image frames as a video file using FFmpeg.
    :param list[Image.Image] buffer: the sequence of frames to save to a video file.
    :param str video_path: the path to the file in which to save the video.
    :param float fps: the frames-per-second at which videos are to be recorded.
    :param int crf: constant rate factor (CRF): the default quality (and rate control) setting in `[0, 51]`, where
    lower values would result in better quality, at the expense of higher file sizes.
    :param int verbosity: the verbosity level of the FFmpeg process. `0` corresponds to non-verbose.
    :param bool verify_input: whether to guarantee that the given frames all have the same size and format.
    :param int or str or tuple[int] color: the "blank" color to fill in the canvas of out-of-size frames.
    :return:
    """
    if verify_input:
        max_size = get_max_size(buffer)
        buffer_ = []
        for img in buffer:
            img = resize_image_canvas(img, max_size, color)
            buffer_.append(np.array(img))
    else:
        buffer_ = [np.array(img) for img in buffer]

    # invokes video encoder
    skvideo.io.vwrite(video_path, np.array(buffer_),
                      inputdict={'-r': str(fps)},
                      outputdict={'-crf': str(crf),
                                  '-pix_fmt': 'yuv420p'},  # wide compatibility
                      # '-filter:v': 'minterpolate=fps=25:mi_mode=dup'},
                      verbosity=verbosity)


def fade_video(buffer, fade_ratio, fade_in=True, fade_out=True):
    """
    Adds fade-in/out effects to the given sequence of images.
    :param list[Image.Image] buffer: the sequence of frames to which add fade effects.
    :param float fade_ratio: the ratio of frames to which apply a fade-in/out effect.
    :param bool fade_in: whether to apply a fade-in effect.
    :param bool fade_out: whether to apply a fade-out effect.
    :rtype: list[Image.Image]
    :return: the given sequence of frames with fade-in/out effects applied.
    """
    # one fade effect required
    if not (fade_in or fade_out):
        return buffer

    total_frames = len(buffer)
    fade_steps = int(fade_ratio * total_frames)
    fade_in_frames = fade_steps if fade_in else 0
    fade_out_frames = fade_steps if fade_out else total_frames
    faded_buffer = []
    for t, frame in enumerate(buffer):

        # checks if frame is simply to be copied to the video or faded
        if t < fade_in_frames:
            frame = fade_image(frame, 1 - (t / fade_steps))
        elif t >= total_frames - fade_out_frames:
            frame = fade_image(frame, (t - (total_frames - fade_out_frames)) / fade_steps)

        # adds frame to list
        faded_buffer.append(frame)

    return faded_buffer

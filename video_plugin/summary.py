"""Video summaries and TensorFlow operations to create them.

A video summary stores the width, height, frames per second, and encoded video data
for zero or more videos in a rank-1 string array: [w, h, fps, vid0, vid1, ...].
"""

import numpy as np

from tensorboard.plugins.video import metadata
from tensorboard.plugins.video import summary_v2
from tensorboard.util import encoder

# Export V2 versions.
video = summary_v2.video

def op(
    name,
    videos,
    fps=30,
    max_outputs=3,
    display_name=None,
    description=None,
    collections=None,
):
    """Create a legacy video summary op for use in a TensorFlow graph.

    Arguments:
      name: A unique name for the generated summary node.
      videos: A `Tensor` representing video data with shape `[k, t, h, w, c]`,
        where `k` is the number of videos, `t` is the number of frames,
        `h` and `w` are the height and width of the frames, and `c` is the
        number of channels (must be 3 for RGB).
      fps: Frames per second for the video playback.
      max_outputs: Optional `int` or rank-0 integer `Tensor`. At most this
        many videos will be emitted at each step. When more than
        `max_outputs` many videos are provided, the first `max_outputs` many
        videos will be used and the rest silently discarded.
      display_name: Optional name for this summary in TensorBoard, as a
        constant `str`. Defaults to `name`.
      description: Optional long-form description for this summary, as a
        constant `str`. Markdown is supported. Defaults to empty.
      collections: Optional list of graph collections keys. The new
        summary op is added to these collections. Defaults to
        `[Graph Keys.SUMMARIES]`.

    Returns:
      A TensorFlow summary op.
    """
    import tensorflow.compat.v1 as tf

    if display_name is None:
        display_name = name

    summary_metadata = metadata.create_summary_metadata(
        display_name=display_name, description=description
    )

    with tf.name_scope(name), tf.control_dependencies(
        [
            tf.assert_rank(videos, 5),  # [batch, time, height, width, channels]
            tf.assert_type(videos, tf.uint8),
            tf.assert_equal(tf.shape(videos)[-1], 3),  # RGB only
            tf.assert_non_negative(max_outputs),
        ]
    ):
        limited_videos = videos[:max_outputs]
        
        def encode_video(video_tensor):
            # Note: In practice, you'd want to use a proper video encoder here
            # This is a placeholder for actual video encoding logic
            return tf.py_function(
                lambda x: encoder.encode_video(x, fps),
                [video_tensor],
                tf.string
            )
        
        encoded_videos = tf.map_fn(
            encode_video,
            limited_videos,
            dtype=tf.string,
            name="encode_each_video",
        )

        video_shape = tf.shape(input=videos)
        dimensions = tf.stack(
            [
                tf.as_string(video_shape[3], name="width"),
                tf.as_string(video_shape[2], name="height"),
                tf.as_string(fps, name="fps"),
            ],
            name="dimensions",
        )
        
        tensor = tf.concat([dimensions, encoded_videos], axis=0)
        return tf.summary.tensor_summary(
            name="video_summary",
            tensor=tensor,
            collections=collections,
            summary_metadata=summary_metadata,
        )

def pb(name, videos, fps=30, max_outputs=3, display_name=None, description=None):
    """Create a legacy video summary protobuf.

    Arguments:
      name: A unique name for the generated summary, including any desired
        name scopes.
      videos: An `np.array` representing video data with shape
        `[k, t, h, w, c]`, where `k` is the number of videos, `t` is the
        number of frames, `h` and `w` are the height and width of the frames,
        and `c` is the number of channels (must be 3 for RGB).
      fps: Frames per second for the video playback.
      max_outputs: Optional `int`. At most this many videos will be
        emitted. If more than this many videos are provided, the first
        `max_outputs` many videos will be used and the rest silently discarded.
      display_name: Optional name for this summary in TensorBoard, as a
        constant `str`. Defaults to `name`.
      description: Optional long-form description for this summary, as a
        constant `str`. Markdown is supported. Defaults to empty.

    Returns:
      A TensorFlow summary protobuf.
    """
    import tensorflow.compat.v1 as tf

    if display_name is None:
        display_name = name

    summary_metadata = metadata.create_summary_metadata(
        display_name=display_name, description=description
    )

    with tf.name_scope(name), tf.control_dependencies(
        [
            tf.assert_rank(videos, 5),  # [batch, time, height, width, channels]
            tf.assert_type(videos, tf.uint8),
            tf.assert_equal(tf.shape(videos)[-1], 3),  # RGB only
            tf.assert_non_negative(max_outputs),
        ]
    ):
        limited_videos = videos[:max_outputs]
        
        def encode_video(video_tensor):
            # Note: In practice, you'd want to use a proper video encoder here
            # This is a placeholder for actual video encoding logic
            return tf.py_function(
                lambda x: encoder.encode_video(x, fps),
                [video_tensor],
                tf.string
            )
        
        encoded_videos = tf.map_fn(
            encode_video,
            limited_videos,
            dtype=tf.string,
            name="encode_each_video",
        )

        video_shape = tf.shape(input=videos)
        dimensions = tf.stack(
            [
                tf.as_string(video_shape[3], name="width"),
                tf.as_string(video_shape[2], name="height"),
                tf.as_string(fps, name="fps"),
            ],
            name="dimensions",
        )
        
        tensor = tf.concat([dimensions, encoded_videos], axis=0)
        return tf.summary.tensor_summary(
            name="video_summary",
            tensor=tensor,
            summary_metadata=summary_metadata,
        )

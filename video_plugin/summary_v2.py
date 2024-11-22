import tensorflow as tf
from video_plugin import metadata
from tensorboard.util import lazy_tensor_creator

def video(name, data, fps=4, step=None, max_outputs=3, description=None):
    """Write a video summary.
    
    Arguments:
      name: A name for this summary
      data: A `Tensor` representing video data with shape `[k, t, h, w, c]`,
        where `k` is the number of videos, `t` is the number of frames,
        `h` and `w` are the height and width of the frames, and `c` is 
        the number of channels (3 for RGB).
      fps: Frames per second for the video playback
      step: Explicit `int64`-castable monotonic step value for this summary
      max_outputs: Optional `int`. Max number of videos to output
      description: Optional long-form description
    """
    summary_metadata = metadata.create_summary_metadata(
        display_name=None, description=description
    )
    
    summary_scope = (
        getattr(tf.summary.experimental, "summary_scope", None)
        or tf.summary.summary_scope
    )
    
    with summary_scope(
        name, "video_summary", values=[data, max_outputs, step]
    ) as (tag, _):
        @lazy_tensor_creator.LazyTensorCreator
        def lazy_tensor():
            tf.debugging.assert_rank(data, 5)  # [k, t, h, w, c]
            tf.debugging.assert_non_negative(max_outputs)
            
            videos = tf.image.convert_image_dtype(data, tf.uint8, saturate=True)
            limited_videos = videos[:max_outputs]
            
            encoded_videos = encode_mp4(limited_videos, fps)
            
            video_shape = tf.shape(input=videos)
            dimensions = tf.stack([
                tf.as_string(video_shape[2], name="height"),
                tf.as_string(video_shape[3], name="width"),
                tf.as_string(video_shape[1], name="frames"),
                tf.as_string(fps, name="fps"),
            ], name="dimensions")
            
            return tf.concat([dimensions, encoded_videos], axis=0)
            
        return tf.summary.write(
            tag=tag, tensor=lazy_tensor, step=step, metadata=summary_metadata
        )

def encode_mp4(video_tensor, fps):
    import tempfile
    import os
    from moviepy.editor import ImageSequenceClip

    def encode_video_fn(video_data):
        video_np = video_data.numpy()
        clip = ImageSequenceClip(list(video_np), fps=fps)
        # Create a temporary file with .mp4 extension
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Write to the temporary file
            clip.write_videofile(temp_path, codec='libx264', audio=False, 
                               verbose=False, logger=None)
            # Read the file contents
            with open(temp_path, 'rb') as f:
                video_bytes = f.read()
        finally:
            # Clean up the temporary file
            os.unlink(temp_path)
            
        return video_bytes

    return tf.map_fn(
        lambda x: tf.py_function(encode_video_fn, [x], tf.string),
        video_tensor,
        dtype=tf.string
    )

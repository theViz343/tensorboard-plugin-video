from tensorboard.compat.proto import summary_pb2
from video_plugin import plugin_data_pb2

PLUGIN_NAME = "videos"
PROTO_VERSION = 0


def create_summary_metadata(
    display_name, description, *, converted_to_tensor=None
):
    """Create a `summary_pb2.SummaryMetadata` proto for video plugin data.

    Args:
      display_name: A name to display for this summary
      description: A description of this summary
      converted_to_tensor: Optional; whether the video has been converted to a tensor

    Returns:
      A `summary_pb2.SummaryMetadata` protobuf object.
    """
    content = plugin_data_pb2.VideoPluginData(
        version=PROTO_VERSION,
        converted_to_tensor=converted_to_tensor,
    )
    metadata = summary_pb2.SummaryMetadata(
        display_name=display_name,
        summary_description=description,
        plugin_data=summary_pb2.SummaryMetadata.PluginData(
            plugin_name=PLUGIN_NAME, content=content.SerializeToString()
        ),
    )
    return metadata


def parse_plugin_metadata(content):
    """Parse summary metadata to a Python object.

    Arguments:
      content: The `content` field of a `SummaryMetadata` proto
        corresponding to the video plugin.

    Returns:
      A `VideoPluginData` protobuf object.
    """
    if not isinstance(content, bytes):
        raise TypeError("Content type must be bytes")
    result = plugin_data_pb2.VideoPluginData.FromString(content)
    if result.version == 0:
        return result
    # No other versions known at this time, so no migrations to do.
    return result

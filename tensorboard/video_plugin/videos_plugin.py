# Copyright 2024 The TensorFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""The TensorBoard Videos plugin."""

import urllib.parse
from werkzeug import wrappers
import os

from tensorboard import errors
from tensorboard import plugin_util
from tensorboard.backend import http_util
from tensorboard.data import provider
from tensorboard.plugins import base_plugin
from video_plugin import metadata

_VIDEO_MIMETYPE = "video/mp4"
_DEFAULT_DOWNSAMPLING = 10  # videos per time series

class VideosPlugin(base_plugin.TBPlugin):
    """Videos Plugin for TensorBoard."""

    plugin_name = metadata.PLUGIN_NAME

    def __init__(self, context):
        """Instantiates VideosPlugin via TensorBoard core.

        Args:
          context: A base_plugin.TBContext instance.
        """
        self._downsample_to = (context.sampling_hints or {}).get(
            self.plugin_name, _DEFAULT_DOWNSAMPLING
        )
        self._data_provider = context.data_provider
        self._version_checker = plugin_util._MetadataVersionChecker(
            data_kind="video",
            latest_known_version=metadata.PROTO_VERSION,
        )

    def get_plugin_apps(self):
        return {
            "/index.js": self._serve_js,
            "/videos": self._serve_video_metadata,
            "/individualVideo": self._serve_individual_video,
            "/tags": self._serve_tags,
        }

    def is_active(self):
        return True  # `list_plugins` as called by TB core suffices

    def frontend_metadata(self):
        return base_plugin.FrontendMetadata(es_module_path="/index.js")

    def _index_impl(self, ctx, experiment):
        mapping = self._data_provider.list_blob_sequences(
            ctx,
            experiment_id=experiment,
            plugin_name=metadata.PLUGIN_NAME,
        )
        result = {run: {} for run in mapping}
        for run, tag_to_content in mapping.items():
            for tag, metadatum in tag_to_content.items():
                md = metadata.parse_plugin_metadata(metadatum.plugin_content)
                if not self._version_checker.ok(md.version, run, tag):
                    continue
                description = plugin_util.markdown_to_safe_html(
                    metadatum.description
                )
                result[run][tag] = {
                    "displayName": metadatum.display_name,
                    "description": description,
                    "samples": metadatum.max_length-2,
                }
        return result

    @wrappers.Request.application
    def _serve_video_metadata(self, request):
        ctx = plugin_util.context(request.environ)
        experiment = plugin_util.experiment_id(request.environ)
        tag = request.args.get("tag")
        run = request.args.get("run")
        sample = int(request.args.get("sample", 2))
        batch_size_idx = int(request.args.get("batch_size", 1))
        try:
            response = self._video_response_for_run(
                ctx, experiment, run, tag, sample, batch_size_idx
            )
        except KeyError:
            return http_util.Respond(
                request, "Invalid run or tag", "text/plain", code=400
            )
        return http_util.Respond(request, response, "application/json")

    def _video_response_for_run(self, ctx, experiment, run, tag, sample, batch_size_idx):
        all_videos = self._data_provider.read_blob_sequences(
            ctx,
            experiment_id=experiment,
            plugin_name=metadata.PLUGIN_NAME,
            downsample=self._downsample_to,
            run_tag_filter=provider.RunTagFilter(runs=[run], tags=[tag]),
        )
        videos = all_videos.get(run, {}).get(tag, None)
        if videos is None:
            raise errors.NotFoundError(
                "No video data for run=%r, tag=%r" % (run, tag)
            )
        return [
            {
                "wall_time": datum.wall_time,
                "step": datum.step,
                "batch_size": int(self._get_sample_at_index(ctx, datum, batch_size_idx)),
                "query": self._data_provider_query(datum.values[sample]),
            }
            for datum in videos
            if len(datum.values) > sample
        ]

    def _get_sample_at_index(self, ctx, datum, index):
        return self._data_provider.read_blob(ctx, blob_key=datum.values[index].blob_key)

    def _data_provider_query(self, blob_reference):
        return urllib.parse.urlencode({"blob_key": blob_reference.blob_key})

    @wrappers.Request.application
    def _serve_individual_video(self, request):
        """Serves an individual video track."""
        try:
            ctx = plugin_util.context(request.environ)
            blob_key = request.args["blob_key"]
            track_number = int(request.args["track_number"])
            data = self._data_provider.read_blob(ctx, blob_key=blob_key)
            track_data = self._split_video_data(data)[track_number]
            return http_util.Respond(request, track_data, _VIDEO_MIMETYPE)
        except (KeyError, IndexError):
            return http_util.Respond(
                request,
                "Invalid run, tag, index, or sample",
                "text/plain",
                code=400,
            )

    def _split_video_data(self, mp4_data):
        import ffmpeg
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
            temp_file.write(mp4_data)
            temp_path = temp_file.name

        try:
            probe = ffmpeg.probe(temp_path)
            video_streams = [stream for stream in probe['streams'] if stream['codec_type'] == 'video']
            separate_videos = []
            for stream in video_streams:
                with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as out_file:
                    out_path = out_file.name
                try:
                    stream = (
                        ffmpeg
                        .input(temp_path)
                        .output(out_path, map=f"0:{stream['index']}", codec='copy')
                        .overwrite_output()
                    )
                    stream.run(capture_stdout=True, capture_stderr=True)
                    with open(out_path, 'rb') as f:
                        separate_videos.append(f.read())
                except ffmpeg.Error as e:
                    print(f"FFmpeg stderr:\n{e.stderr.decode()}")
                    raise
                finally:
                    try:
                        os.unlink(out_path)
                    except:
                        pass
            return separate_videos if separate_videos else [mp4_data]  # Fallback

        except Exception as e:
            print(f"Error processing video: {str(e)}")
            return [mp4_data]

        finally:
            try:
                os.unlink(temp_path)
            except:
                pass

    @wrappers.Request.application
    def _serve_tags(self, request):
        ctx = plugin_util.context(request.environ)
        experiment = plugin_util.experiment_id(request.environ)
        index = self._index_impl(ctx, experiment)
        return http_util.Respond(request, index, "application/json")

    @wrappers.Request.application
    def _serve_js(self, request):
        del request  # unused
        filepath = os.path.join(os.path.dirname(__file__), "static", "index.js")
        with open(filepath) as infile:
            contents = infile.read()
        return wrappers.Response(contents, content_type="text/javascript")

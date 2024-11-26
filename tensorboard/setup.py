import setuptools


setuptools.setup(
    name="videos",
    version="0.1.0",
    description="Tensorboard plugin for videos.",
    packages=["video_plugin"],
    package_data={
        "video_plugin": ["static/**"],
    },
    entry_points={
        "tensorboard_plugins": [
            "video_plugin = video_plugin.videos_plugin:VideosPlugin",
        ],
    },
)
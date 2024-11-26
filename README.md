# Video Plugin for Tensorboard

This plugin allows you to visualize videos in Tensorboard.

## On Hold
 - We were/are planning to utilize mp4 videos (with audio and video tracks) to record our latent diffusion model. However, we are holding off on this for now.
 - We created this repo in case someone else wants to finish implementing the summary writer and tensorboard plugin for recording mp4 videos
 - The tensorboard currently supports reading from event files (and displaying in the frontend). However, the tensorboard plugin isn't currently setup to create mp4s in the event file for TENSORFLOW
   - We use pytorch and didn't find it necessary to implement the TENSORFLOW logic.

## Installation
 - Ensure you have Tensorboard installed.
 - In the root directory, run `pip install .` to install the plugin.

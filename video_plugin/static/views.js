class VideoAPI {
    static async fetchTags() {
      try {
        const response = await fetch('/api/videos/tags');
        return await response.json();
      } catch (error) {
        console.error('Failed to fetch tags:', error);
        throw error;
      }
    }
  
    static async fetchVideoData(run, tag) {
      try {
        const response = await fetch(`/api/videos/${run}/${tag}`);
        return await response.json();
      } catch (error) {
        console.error('Failed to fetch video:', error);
        throw error;
      }
    }
  
    static renderVideoGrid(videos, container) {
      container.innerHTML = videos.map(video => `
        <div class="video-card">
          <div class="video-wrapper">
            <video 
              class="tensor-video"
              data-run="${video.run}"
              data-tag="${video.tag}"
              controls
              loop
            >
              <source src="${video.url}" type="video/mp4">
              Your browser does not support the video tag.
            </video>
            <div class="video-controls">
              <button class="play-pause">Play</button>
              <input type="range" class="video-progress" min="0" max="100" value="0">
              <span class="time-display">0:00 / 0:00</span>
            </div>
          </div>
          <div class="video-info">
            <span>Run: ${video.run}</span>
            <span>Tag: ${video.tag}</span>
            <span>Frame Rate: ${video.metadata.fps || 'N/A'} fps</span>
            <span>Duration: ${video.metadata.duration || 'N/A'} seconds</span>
          </div>
        </div>
      `).join('');
  
      // Add individual video controls
      container.querySelectorAll('.video-card').forEach(card => {
        const video = card.querySelector('video');
        const playPauseBtn = card.querySelector('.play-pause');
        const progress = card.querySelector('.video-progress');
        const timeDisplay = card.querySelector('.time-display');
  
        // Play/Pause button
        playPauseBtn.addEventListener('click', () => {
          if (video.paused) {
            video.play();
            playPauseBtn.textContent = 'Pause';
          } else {
            video.pause();
            playPauseBtn.textContent = 'Play';
          }
        });
  
        // Update progress bar
        video.addEventListener('timeupdate', () => {
          const percent = (video.currentTime / video.duration) * 100;
          progress.value = percent;
          timeDisplay.textContent = `${formatTime(video.currentTime)} / ${formatTime(video.duration)}`;
        });
  
        // Click on progress bar
        progress.addEventListener('input', () => {
          const time = (progress.value / 100) * video.duration;
          video.currentTime = time;
        });
      });
    }
  }
  
  // Helper function to format time
  function formatTime(seconds) {
    const minutes = Math.floor(seconds / 60);
    seconds = Math.floor(seconds % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  }
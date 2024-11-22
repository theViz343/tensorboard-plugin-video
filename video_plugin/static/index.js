export async function render() {
    // Initial loading message
    const msg = createElement('p', 'Fetching video data…');
    document.body.appendChild(msg);
  
    // Add styles
    const style = createElement(
      'style',
      `
        .dashboard-layout {
          display: flex;
          height: 100vh;
        }
        .sidebar {
          width: 300px;
          padding: 20px;
          border-right: 1px solid #ccc;
        }
        .center-content {
          flex: 1;
          padding: 20px;
          overflow-y: auto;
        }
        .controls {
          margin-bottom: 20px;
        }
        .slider-container {
          margin: 10px 0;
        }
        .video-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
          gap: 20px;
          padding: 20px;
        }
        .video-card {
          border: 1px solid #ddd;
          border-radius: 4px;
          padding: 10px;
        }
        .tensor-video {
          width: 100%;
          background: #000;
        }
        .video-info {
          margin-top: 10px;
          font-size: 0.9em;
        }
      `
    );
    document.head.appendChild(style);
  
    try {
      // First fetch tags to get run/tag combinations
      const runToTags = await fetch('./tags').then((response) => response.json());
      console.log('Fetched', Object.keys(runToTags).length, 'runs');
      
      // Then fetch metadata for all videos
      const videoData = await Promise.all(
        Object.entries(runToTags).flatMap(([run, tagToDescription]) =>
          Object.keys(tagToDescription).map(async (tag) => {
            // Fetch video metadata
            console.log('Fetching video metadata for', run, tag);
            const videoMetadata = await fetch('./videos?' + new URLSearchParams({
              run,
              tag
            })).then(response => response.json());
            console.log('Fetched', videoMetadata.length, 'videos');

            return {
              run,
              tag,
              metadata: tagToDescription[tag],
              videos: videoMetadata // Array of video data with wall_time, step, and query
            };
          })
        )
      );
  
      // Create dashboard structure
      const dashboard = createElement('div', { className: 'dashboard-layout' }, [
        // Sidebar
        createElement('div', { className: 'sidebar' }, [
          // Controls
          createElement('div', { className: 'controls' }, [
            // Playback Speed
            createElement('div', { className: 'slider-container' }, [
              createElement('label', [
                'Playback Speed: ',
                createElement('span', { id: 'speedValue' }, '1x'),
              ]),
              createElement('input', {
                type: 'range',
                id: 'speed',
                min: '0.25',
                max: '2',
                step: '0.25',
                value: '1',
              }),
            ]),
            // Brightness
            createElement('div', { className: 'slider-container' }, [
              createElement('label', [
                'Brightness: ',
                createElement('span', { id: 'brightnessValue' }, '1'),
              ]),
              createElement('input', {
                type: 'range',
                id: 'brightness',
                min: '0',
                max: '2',
                step: '0.1',
                value: '1',
              }),
            ]),
            // Contrast
            createElement('div', { className: 'slider-container' }, [
              createElement('label', [
                'Contrast: ',
                createElement('span', { id: 'contrastValue' }, '100%'),
              ]),
              createElement('input', {
                type: 'range',
                id: 'contrast',
                min: '0',
                max: '200',
                step: '1',
                value: '100',
              }),
            ]),
            // Global Controls
            createElement('div', { className: 'global-controls' }, [
              createElement('button', { 
                id: 'playAll',
                onclick: () => document.querySelectorAll('.tensor-video').forEach(v => v.play())
              }, 'Play All'),
              createElement('button', { 
                id: 'pauseAll',
                onclick: () => document.querySelectorAll('.tensor-video').forEach(v => v.pause())
              }, 'Pause All'),
            ]),
          ]),
        ]),
  
        // Main content
        createElement('div', { className: 'center-content' }, [
          createElement('input', {
            type: 'text',
            id: 'tagFilter',
            placeholder: 'Filter tags...',
            oninput: (e) => filterVideos(e.target.value),
          }),
          createElement('div', { className: 'video-grid' },
            videoData.flatMap(data => createVideoCards(data))
          ),
        ]),
      ]);
  
      // Replace loading message and render dashboard
      msg.remove();
      document.body.appendChild(dashboard);
  
      // Initialize controls
      initializeControls();
  
    } catch (error) {
      throw error;
      msg.textContent = 'Error loading video data: ' + error.message;
    }
  }
  
  function createVideoCards({run, tag, videos, metadata}) {
    return videos.map(video => 
      createElement('div', { className: 'video-card', 'data-tag': tag }, [
        createElement('video', {
          className: 'tensor-video',
          controls: true,
          loop: true,
          src: `./individualVideo?${video.query}`,
        }),
        createElement('div', { className: 'video-info' }, [
          createElement('div', `Run: ${run}`),
          createElement('div', `Tag: ${tag}`),
          createElement('div', `Step: ${video.step}`),
          createElement('div', `Wall Time: ${new Date(video.wall_time * 1000).toLocaleString()}`),
          metadata.description && createElement('div', `Description: ${metadata.description}`),
        ]),
      ])
    );
  }
  
  function createElement(tag, propsOrChildren, maybeChildren) {
    const element = document.createElement(tag);
    
    let props = propsOrChildren;
    let children = maybeChildren;
    
    if (typeof propsOrChildren === 'string' || Array.isArray(propsOrChildren)) {
      props = {};
      children = propsOrChildren;
    }
  
    // Handle properties
    Object.entries(props).forEach(([key, value]) => {
      if (key === 'className') {
        element.className = value;
      } else if (key.startsWith('on')) {
        element.addEventListener(key.slice(2).toLowerCase(), value);
      } else {
        element.setAttribute(key, value);
      }
    });
  
    // Handle children
    if (children != null) {
      if (typeof children === 'string') {
        element.textContent = children;
      } else if (Array.isArray(children)) {
        children.forEach(child => {
          // Only append if child exists and is a valid node or string
          if (child) {
            if (typeof child === 'string') {
              element.appendChild(document.createTextNode(child));
            } else if (child instanceof Node) {
              element.appendChild(child);
            }
          }
        });
      } else if (children instanceof Node) {
        element.appendChild(children);
      } else if (typeof children === 'number') {
        element.appendChild(document.createTextNode(children.toString()));
      }
    }
  
    return element;
  }
  
  function initializeControls() {
    // Playback Speed
    const speedSlider = document.getElementById('speed');
    speedSlider?.addEventListener('input', (e) => {
      const speed = e.target.value;
      document.getElementById('speedValue').textContent = `${speed}x`;
      document.querySelectorAll('.tensor-video').forEach(video => {
        video.playbackRate = Number(speed);
      });
    });
  
    // Brightness and Contrast
    const updateVideoFilters = () => {
      const brightness = document.getElementById('brightness').value;
      const contrast = document.getElementById('contrast').value;
      document.querySelectorAll('.tensor-video').forEach(video => {
        video.style.filter = `brightness(${brightness}) contrast(${contrast}%)`;
      });
    };
  
    document.getElementById('brightness')?.addEventListener('input', (e) => {
      document.getElementById('brightnessValue').textContent = e.target.value;
      updateVideoFilters();
    });
  
    document.getElementById('contrast')?.addEventListener('input', (e) => {
      document.getElementById('contrastValue').textContent = `${e.target.value}%`;
      updateVideoFilters();
    });
  }
  
  function filterVideos(searchText) {
    const cards = document.querySelectorAll('.video-card');
    cards.forEach(card => {
      const tag = card.getAttribute('data-tag').toLowerCase();
      card.style.display = tag.includes(searchText.toLowerCase()) ? '' : 'none';
    });
  } 
/**
 * 悬浮窗渲染进程：多 agent 视频网格播放、缩放、拖拽。
 * 与 main.js 的 CELL_1/CELL_2/CELL_3_4 对应，保证每格视频完整显示。
 */
(function () {
  const CELL_1 = 100;
  const CELL_2 = 70;
  const CELL_3_4 = 60;
  const MAX_AGENTS = 4;
  const CLICK_THRESHOLD_PX = 5;
  const CLICK_MAX_MS = 400;

  const overlayRoot = document.querySelector('.overlay-root');
  const videos = [
    document.getElementById('video0'),
    document.getElementById('video1'),
    document.getElementById('video2'),
    document.getElementById('video3'),
  ];
  const scalers = overlayRoot.querySelectorAll('.agent-slot .scaler');

  let agentCount = 1;
  let playlist = [];
  const currentPlayIndex = [0, 0, 0, 0];
  const playingState = [true, true, true, true];

  /** 当前布局下每格边长（px），与主进程窗口尺寸一致 */
  function getCellSize() {
    if (agentCount <= 1) return CELL_1;
    if (agentCount === 2) return CELL_2;
    return CELL_3_4;
  }

  function setVideoToItem(slotIndex, itemIndex) {
    if (!playlist.length || slotIndex >= agentCount) return;
    const item = playlist[itemIndex];
    const v = videos[slotIndex];
    const s = scalers[slotIndex];
    if (!v || !s || !item) return;
    v.src = item.path;
    v.load();
    v.addEventListener(
      'canplay',
      (function (idx) {
        return function () {
          scalers[idx].classList.add('ready');
          fitVideo(idx);
          if (playingState[idx]) videos[idx].play().catch(() => {});
        };
      })(slotIndex),
      { once: true }
    );
  }

  function advanceSlot(slotIndex) {
    if (!playlist.length) return;
    if (playlist.length === 1) {
      const v = videos[slotIndex];
      if (playingState[slotIndex] && v) {
        v.currentTime = 0;
        v.play().catch(() => {});
      }
      return;
    }
    currentPlayIndex[slotIndex] = (currentPlayIndex[slotIndex] + 1) % playlist.length;
    setVideoToItem(slotIndex, currentPlayIndex[slotIndex]);
  }

  /** 按当前格子尺寸缩放该 slot 的视频，保持比例完整显示 */
  function fitVideo(slotIndex) {
    const video = videos[slotIndex];
    const scaler = scalers[slotIndex];
    if (!video || !scaler) return;
    const w = video.videoWidth;
    const h = video.videoHeight;
    if (!w || !h) return;
    const cell = getCellSize();
    const scale = Math.min(cell / w, cell / h);
    scaler.style.width = w + 'px';
    scaler.style.height = h + 'px';
    scaler.style.transform = 'scale(' + scale + ')';
    video.style.width = w + 'px';
    video.style.height = h + 'px';
  }

  /** 对当前所有可见 slot 重新计算缩放（agent 数量/窗口尺寸变化时） */
  function refitVisibleVideos() {
    for (let i = 0; i < agentCount; i++) {
      const v = videos[i];
      if (v && v.videoWidth && v.videoHeight) fitVideo(i);
    }
  }

  function setupEndedListeners() {
    videos.forEach((v, i) => {
      v.addEventListener('ended', function () {
        if (playingState[i]) advanceSlot(i);
      });
    });
  }

  function buildPlaylistThenPlay(paths) {
    if (!paths || paths.length === 0) return;
    const seen = new Set();
    let i = 0;
    const scanVideo = videos[0];

    function scanNext() {
      if (i >= paths.length) {
        if (playlist.length === 0) return;
        for (let k = 0; k < agentCount; k++) {
          currentPlayIndex[k] = 0;
          setVideoToItem(k, 0);
        }
        setupEndedListeners();
        return;
      }
      const url = paths[i++];
      scanVideo.addEventListener(
        'loadedmetadata',
        function () {
          const w = scanVideo.videoWidth;
          const h = scanVideo.videoHeight;
          const key = w + ',' + h;
          if (!seen.has(key)) {
            seen.add(key);
            playlist.push({ path: url, w: w, h: h });
          }
          scanNext();
        },
        { once: true }
      );
      scanVideo.addEventListener('error', () => scanNext(), { once: true });
      scanVideo.src = url;
      scanVideo.load();
    }
    scanNext();
  }

  window.electronAPI.onVideoPaths(buildPlaylistThenPlay);

  window.electronAPI.onAgentCount?.((count) => {
    const prevCount = agentCount;
    agentCount = Math.min(MAX_AGENTS, Math.max(1, count));
    if (overlayRoot) overlayRoot.dataset.agentCount = String(agentCount);
    if (playlist.length > 0 && count > prevCount) {
      for (let i = prevCount; i < agentCount; i++) {
        currentPlayIndex[i] = 0;
        setVideoToItem(i, 0);
      }
    }
    refitVisibleVideos();
  });

  window.electronAPI.onPlayerCmd?.((cmd, index) => {
    const v = videos[index];
    if (!v || index >= agentCount) return;
    if (cmd === 'play') {
      playingState[index] = true;
      v.play().catch(() => {});
    } else if (cmd === 'pause') {
      playingState[index] = false;
      v.pause();
    }
  });

  (function setupOverlayDragAndClick() {
    if (!overlayRoot || !window.electronAPI.openMain) return;
    overlayRoot.addEventListener('mousedown', function (e) {
      if (e.button !== 0) return;
      const startX = e.screenX;
      const startY = e.screenY;
      const startTime = Date.now();
      let maxDist = 0;

      function onMove(ev) {
        maxDist = Math.max(maxDist, Math.hypot(ev.screenX - startX, ev.screenY - startY));
        window.electronAPI.overlayDragMove?.(ev.screenX, ev.screenY);
      }
      function onUp() {
        document.removeEventListener('mousemove', onMove);
        document.removeEventListener('mouseup', onUp);
        window.electronAPI.overlayDragEnd?.();
        if (maxDist < CLICK_THRESHOLD_PX && Date.now() - startTime < CLICK_MAX_MS) {
          window.electronAPI.openMain();
        }
      }
      window.electronAPI.overlayDragStart?.(startX, startY);
      document.addEventListener('mousemove', onMove);
      document.addEventListener('mouseup', onUp);
    });
  })();
})();
